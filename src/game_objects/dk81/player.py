"""ドンキーコング '81 のプレイヤー（マリオ風）。

状態:
  - "ground": 鉄骨の上を歩く（斜面に沿って y がスナップする）
  - "air":    ジャンプ・落下中（重力が働く）
  - "climb":  はしごを昇降中（x ははしごに固定）
  - "dying":  やられ演出（回転しながら落下する）

hammering は Milestone B 用のスタブ（A では常に False）。
True の間ははしご昇降・ジャンプを禁止する分岐だけ先に入れてある。
"""

import pygame
from config import (
    DK81_PLAYER_WIDTH, DK81_PLAYER_HEIGHT, DK81_PLAYER_SPEED,
    DK81_CLIMB_SPEED, DK81_JUMP_POWER, GRAVITY, SCREEN_WIDTH,
    COLOR_RED, COLOR_BLUE, DK81_COLOR_SKIN,
)
import game_objects.dk81.stage as stage

LADDER_SNAP = 16  # はしごに乗れる x の許容範囲
COLOR_YELLOW_SAFE = (250, 210, 60)  # オーバーオールのボタン用（ドット向けの落ち着いた黄）


class DK81Player:
    def __init__(self, x, girder_index):
        self.width = DK81_PLAYER_WIDTH
        self.height = DK81_PLAYER_HEIGHT
        self.state = "ground"
        self.on_girder = girder_index
        self.vel_y = 0.0
        self.facing = 1   # 1=右, -1=左
        self.walk_anim = 0.0
        self.climb_ladder = None
        self.hammering = False   # Milestone B 用スタブ
        self.spin_angle = 0.0    # dying 中の回転角
        # 中心 x を基準に配置
        self.cx = x
        self.bottom = stage.surface_y(girder_index, x)

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
        elif self.state == "air":
            self._update_air(dt, left, right)
        # dying は update_dying() で更新する

    def jump(self):
        """スペースキー（エッジ）で呼ばれる。ジャンプしたら True。"""
        if self.state == "ground" and not self.hammering:
            self.vel_y = -DK81_JUMP_POWER
            self.state = "air"
            return True
        return False

    # --- やられ演出 ---------------------------------------------------
    def start_dying(self):
        self.state = "dying"
        self.spin_angle = 0.0
        self.vel_y = -220  # 小さく跳ねてから落下

    def update_dying(self, dt):
        self.spin_angle += dt * 540
        self.vel_y += GRAVITY * 0.6 * dt
        self.bottom += self.vel_y * dt

    # --- 各状態 ------------------------------------------------------
    def _update_ground(self, dt, left, right, up, down):
        # はしごへ乗る（ハンマー中は不可）
        if not self.hammering:
            if up and self._try_enter_ladder(going_up=True):
                return
            if down and self._try_enter_ladder(going_up=False):
                return

        move = (1 if right else 0) - (1 if left else 0)
        if move != 0:
            self.facing = move
            self.cx += move * DK81_PLAYER_SPEED * dt
            self.walk_anim += dt * 10

        xl, xr = stage.girder_range(self.on_girder)
        # 鉄骨の端を超えたら落下
        if self.cx < xl or self.cx > xr:
            self.cx = max(0, min(SCREEN_WIDTH, self.cx))
            self.state = "air"
            self.vel_y = 0
            return

        # 斜面にスナップ
        self.bottom = stage.surface_y(self.on_girder, self.cx)

    def _update_air(self, dt, left, right):
        move = (1 if right else 0) - (1 if left else 0)
        if move != 0:
            self.facing = move
            self.cx += move * DK81_PLAYER_SPEED * dt
        self.cx = max(self.width / 2, min(SCREEN_WIDTH - self.width / 2, self.cx))

        prev_bottom = self.bottom
        self.vel_y += GRAVITY * dt
        self.bottom += self.vel_y * dt

        if self.vel_y > 0:  # 落下中のみ着地判定
            hit = stage.find_landing_girder(self.cx, prev_bottom, self.bottom)
            if hit:
                self.on_girder, self.bottom = hit
                self.vel_y = 0
                self.state = "ground"

    def _update_climb(self, dt, up, down):
        ladder = self.climb_ladder
        top = stage.ladder_top_y(ladder)
        bottom = stage.ladder_bottom_y(ladder)
        _, lower, upper, _broken = ladder

        move = (1 if down else 0) - (1 if up else 0)
        self.bottom += move * DK81_CLIMB_SPEED * dt
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
        for ladder in stage.LADDERS:
            lx, lower, upper, broken = ladder
            if broken:
                continue  # 壊れはしごは使えない
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
        surf = self._build_sprite()
        if self.facing < 0:
            surf = pygame.transform.flip(surf, True, False)
        if self.state == "dying":
            surf = pygame.transform.rotate(surf, self.spin_angle % 360)
        rect = surf.get_rect(
            center=(int(self.cx), int(self.bottom - self.height / 2)))
        screen.blit(surf, rect)

    def _build_sprite(self):
        """ドット絵風スプライトを組み立てる（右向き基準）。"""
        w, h = self.width, self.height
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        climbing = self.state == "climb"
        step = int(self.walk_anim) % 2

        # 帽子（赤・つばは進行方向側）
        pygame.draw.rect(s, COLOR_RED, (3, 0, w - 6, 6))
        pygame.draw.rect(s, COLOR_RED, (w - 10, 5, 9, 3))  # つば（右）
        # 顔
        pygame.draw.rect(s, DK81_COLOR_SKIN, (5, 6, w - 10, 9))
        if not climbing:
            pygame.draw.rect(s, (30, 30, 30), (w - 10, 8, 2, 2))       # 目
            pygame.draw.rect(s, (90, 50, 20), (w - 12, 12, 7, 2))      # ひげ
        # シャツ（赤い腕）＋オーバーオール（青）
        pygame.draw.rect(s, COLOR_BLUE, (5, 14, w - 10, 10))
        if climbing:
            # はしご：腕を交互に上げる
            arm_up = 6 if step == 0 else 14
            arm_dn = 14 if step == 0 else 6
            pygame.draw.rect(s, COLOR_RED, (1, arm_up, 4, 8))
            pygame.draw.rect(s, COLOR_RED, (w - 5, arm_dn, 4, 8))
        else:
            pygame.draw.rect(s, COLOR_RED, (1, 15, 4, 8))
            pygame.draw.rect(s, COLOR_RED, (w - 5, 15, 4, 8))
        # ボタン
        pygame.draw.rect(s, COLOR_YELLOW_SAFE, (8, 16, 2, 2))
        pygame.draw.rect(s, COLOR_YELLOW_SAFE, (w - 10, 16, 2, 2))
        # 脚・靴（歩行アニメで左右に振る）
        swing = 3 if step == 0 else -3
        if self.state == "air":
            swing = 4  # 空中は開脚
        pygame.draw.rect(s, COLOR_BLUE, (6, 24, 4, 3))
        pygame.draw.rect(s, COLOR_BLUE, (w - 10, 24, 4, 3))
        pygame.draw.rect(s, (150, 70, 20), (3 + swing, h - 4, 7, 4))
        pygame.draw.rect(s, (150, 70, 20), (w - 10 - swing, h - 4, 7, 4))
        return s
