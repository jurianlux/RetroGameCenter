"""ドンキーコング '81 の樽（バレル）。

DK が投げた樽は鉄骨の斜面を下り方向へ転がり、端から落ちて下の鉄骨に乗り、
逆向きに転がる（ジグザグ）。一定確率ではしごを伝って下りる。
壊れはしごは使わない。画面下に出たら消滅する。
"""

import math
import random

import pygame
from config import (
    DK81_BARREL_RADIUS, DK81_BARREL_SPEED, DK81_BARREL_LADDER_CHANCE,
    GRAVITY, SCREEN_HEIGHT, COLOR_BARREL, COLOR_BARREL_BAND,
)
import game_objects.dk81.stage as stage


class DK81Barrel:
    def __init__(self, x, girder_index):
        self.cx = x
        self.girder = girder_index
        self.direction = stage.downhill_dir(girder_index)
        self.cy = stage.surface_y(girder_index, x) - DK81_BARREL_RADIUS
        self.state = "roll"        # roll / fall / ladder
        self.vel_y = 0.0
        self.ladder = None
        self.angle = 0.0
        self.scored = False        # 飛び越えボーナスを与えたか
        self.alive = True
        self._checked_ladders = set()

    def get_rect(self):
        r = DK81_BARREL_RADIUS
        return pygame.Rect(int(self.cx - r), int(self.cy - r), r * 2, r * 2)

    def update(self, dt):
        if self.state == "roll":
            self._update_roll(dt)
        elif self.state == "fall":
            self._update_fall(dt)
        else:
            self._update_ladder(dt)

        if self.cy - DK81_BARREL_RADIUS > SCREEN_HEIGHT:
            self.alive = False

    def _update_roll(self, dt):
        self.angle += self.direction * DK81_BARREL_SPEED * dt / DK81_BARREL_RADIUS
        prev_x = self.cx
        self.cx += self.direction * DK81_BARREL_SPEED * dt

        # はしごを下りるか判定（交差した瞬間・壊れはしごは対象外）
        for ladder in stage.LADDERS:
            lx, lower, upper, broken = ladder
            if broken or upper != self.girder:
                continue
            crossed = (prev_x - lx) * (self.cx - lx) <= 0
            if crossed and ladder not in self._checked_ladders:
                self._checked_ladders.add(ladder)
                if random.random() < DK81_BARREL_LADDER_CHANCE:
                    self.ladder = ladder
                    self.cx = lx
                    self.state = "ladder"
                    return

        xl, xr = stage.girder_range(self.girder)
        if self.cx < xl or self.cx > xr:
            # 端に到達 → 落下
            self.cx = max(xl, min(xr, self.cx))
            self.state = "fall"
            self.vel_y = 0
            self._checked_ladders.clear()
            return

        self.cy = stage.surface_y(self.girder, self.cx) - DK81_BARREL_RADIUS

    def _update_fall(self, dt):
        prev_bottom = self.cy + DK81_BARREL_RADIUS
        self.vel_y += GRAVITY * dt
        self.cy += self.vel_y * dt
        new_bottom = self.cy + DK81_BARREL_RADIUS

        hit = stage.find_landing_girder(self.cx, prev_bottom, new_bottom)
        if hit and hit[0] != self.girder:
            self.girder, surface = hit
            self.cy = surface - DK81_BARREL_RADIUS
            self.direction = stage.downhill_dir(self.girder)
            self.state = "roll"
            self.vel_y = 0

    def _update_ladder(self, dt):
        self.angle += dt * 4
        bottom_y = stage.ladder_bottom_y(self.ladder)
        self.cy += DK81_BARREL_SPEED * 0.9 * dt
        if self.cy + DK81_BARREL_RADIUS >= bottom_y:
            _, lower, _upper, _broken = self.ladder
            self.girder = lower
            self.cy = bottom_y - DK81_BARREL_RADIUS
            self.direction = stage.downhill_dir(self.girder)
            self.state = "roll"
            self.ladder = None

    def draw(self, screen):
        cx, cy, r = int(self.cx), int(self.cy), DK81_BARREL_RADIUS
        pygame.draw.circle(screen, COLOR_BARREL, (cx, cy), r)
        pygame.draw.circle(screen, COLOR_BARREL_BAND, (cx, cy), r, 2)
        # 回転を示すバンド（縦線を角度で振る）
        ox = int(math.cos(self.angle) * (r - 3))
        pygame.draw.line(screen, COLOR_BARREL_BAND,
                         (cx + ox, cy - r + 2), (cx + ox, cy + r - 2), 2)
        pygame.draw.line(screen, COLOR_BARREL_BAND, (cx - r, cy), (cx + r, cy), 2)
