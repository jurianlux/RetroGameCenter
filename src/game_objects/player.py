"""プレイヤー（マリオ）。

状態:
  - "ground": 鉄骨の上を歩く（斜面に沿って y がスナップする）
  - "air":    ジャンプ・落下中（重力が働く）
  - "climb":  はしごを昇降中（x ははしごに固定）
"""

import pygame
from config import (
    PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_SPEED, CLIMB_SPEED,
    GRAVITY, JUMP_POWER, SCREEN_WIDTH,
    COLOR_RED, COLOR_BLUE, COLOR_WHITE,
)
import game_objects.level as level

LADDER_SNAP = 16  # はしごに乗れる x の許容範囲


class Player:
    def __init__(self, x, girder_index):
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.state = "ground"
        self.on_girder = girder_index
        self.vel_y = 0
        self.facing = 1   # 1=右, -1=左
        self.walk_anim = 0.0
        self.climb_ladder = None
        # 中心 x を基準に配置
        self.cx = x
        self.bottom = level.surface_y(girder_index, x)

    # --- 位置ヘルパー -------------------------------------------------
    @property
    def x(self):
        return self.cx - self.width / 2

    @property
    def y(self):
        return self.bottom - self.height

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    # --- 入力からの更新 ----------------------------------------------
    def update(self, dt, keys):
        left = keys[pygame.K_LEFT]
        right = keys[pygame.K_RIGHT]
        up = keys[pygame.K_UP]
        down = keys[pygame.K_DOWN]

        if self.state == "climb":
            self._update_climb(dt, up, down)
        elif self.state == "ground":
            self._update_ground(dt, left, right, up, down)
        else:  # air
            self._update_air(dt, left, right)

    def jump(self):
        """スペースキー（エッジ）で呼ばれる。"""
        if self.state == "ground":
            self.vel_y = -JUMP_POWER
            self.state = "air"

    # --- 各状態 ------------------------------------------------------
    def _update_ground(self, dt, left, right, up, down):
        # はしごへ乗る
        if up and self._try_enter_ladder(going_up=True):
            return
        if down and self._try_enter_ladder(going_up=False):
            return

        move = (1 if right else 0) - (1 if left else 0)
        if move != 0:
            self.facing = move
            self.cx += move * PLAYER_SPEED * dt
            self.walk_anim += dt * 10

        xl, xr = level.girder_range(self.on_girder)
        # 鉄骨の端を超えたら落下
        if self.cx < xl or self.cx > xr:
            self.cx = max(0, min(SCREEN_WIDTH, self.cx))
            self.state = "air"
            self.vel_y = 0
            return

        # 斜面にスナップ
        self.bottom = level.surface_y(self.on_girder, self.cx)

    def _update_air(self, dt, left, right):
        move = (1 if right else 0) - (1 if left else 0)
        if move != 0:
            self.facing = move
            self.cx += move * PLAYER_SPEED * dt
        self.cx = max(self.width / 2, min(SCREEN_WIDTH - self.width / 2, self.cx))

        prev_bottom = self.bottom
        self.vel_y += GRAVITY * dt
        self.bottom += self.vel_y * dt

        if self.vel_y > 0:  # 落下中のみ着地判定
            hit = level.find_landing_girder(self.cx, prev_bottom, self.bottom)
            if hit:
                self.on_girder, self.bottom = hit
                self.vel_y = 0
                self.state = "ground"

    def _update_climb(self, dt, up, down):
        ladder = self.climb_ladder
        top = level.ladder_top_y(ladder)
        bottom = level.ladder_bottom_y(ladder)
        _, lower, upper = ladder

        move = (1 if down else 0) - (1 if up else 0)
        self.bottom += move * CLIMB_SPEED * dt
        if move != 0:
            self.walk_anim += dt * 8

        # 上端に到達 → 上段へ
        if self.bottom <= top:
            self.bottom = top
            self.on_girder = upper
            self.state = "ground"
            self.climb_ladder = None
        # 下端に到達 → 下段へ
        elif self.bottom >= bottom:
            self.bottom = bottom
            self.on_girder = lower
            self.state = "ground"
            self.climb_ladder = None

    def _try_enter_ladder(self, going_up):
        for ladder in level.LADDERS:
            lx, lower, upper = ladder
            if abs(self.cx - lx) > LADDER_SNAP:
                continue
            if going_up and self.on_girder == lower:
                self._begin_climb(ladder, lx)
                return True
            if not going_up and self.on_girder == upper:
                self._begin_climb(ladder, lx)
                return True
        return False

    def _begin_climb(self, ladder, lx):
        self.cx = lx
        self.state = "climb"
        self.climb_ladder = ladder
        self.vel_y = 0

    # --- 描画 --------------------------------------------------------
    def draw(self, screen, blink=False):
        if blink:
            return  # 無敵中の点滅（このフレームは描かない）
        r = self.get_rect()
        # 体（青オーバーオール）
        pygame.draw.rect(screen, COLOR_BLUE, (r.x + 3, r.y + 14, r.width - 6, r.height - 14))
        # 顔
        pygame.draw.rect(screen, (245, 200, 150), (r.x + 5, r.y + 7, r.width - 10, 9))
        # 帽子（赤）
        pygame.draw.rect(screen, COLOR_RED, (r.x + 3, r.y + 2, r.width - 6, 6))
        pygame.draw.rect(screen, COLOR_RED, (r.x + 3, r.y + 6, r.width - 12, 3) if self.facing < 0
                         else (r.x + 9, r.y + 6, r.width - 12, 3))
        # 足（歩行アニメで左右に振る）
        swing = 3 if int(self.walk_anim) % 2 == 0 else -3
        foot_y = r.bottom - 5
        pygame.draw.rect(screen, COLOR_RED, (r.x + 3 + swing, foot_y, 7, 5))
        pygame.draw.rect(screen, COLOR_RED, (r.right - 10 - swing, foot_y, 7, 5))
