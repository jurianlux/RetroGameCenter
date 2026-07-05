"""アイスクライマーのプレイヤー「ポポ」。

ワールド座標（y は下ほど大きい）。中心 x = cx、足元 = bottom で管理する。

状態:
  - "ground": 氷/岩の上に立つ。左右移動。
  - "air":    ジャンプ・落下中。重力。頭上の氷を突き上げて割る（頭突き）。
  - "dying":  やられ演出（跳ねてから落下）。

すり抜け床:
  - 上昇中（vel_y < 0）は床を通り抜ける。ただし頭が氷ブロックに入ったら「割る」。
    岩（SOLID）は割れず、頭がつかえて跳ね返る。
  - 落下中（vel_y > 0）は、前フレームで面の上、今フレームで面以下に到達したとき着地。

割った氷の情報は update() の戻り値 events で scene に渡す（SE・得点用）。
"""

import pygame

from config import (
    ICE_PLAYER_W, ICE_PLAYER_H, ICE_PLAYER_SPEED, ICE_JUMP_POWER,
    ICE_GRAVITY, ICE_AIR_CONTROL, ICE_CELL, ICE_COLS,
    ICE_COLOR_POPO, ICE_COLOR_POPO_TRIM, ICE_COLOR_POPO_FACE,
    ICE_COLOR_HAMMER_HEAD,
)
import game_objects.ice.stage as stage_mod

WORLD_LEFT = 0
WORLD_RIGHT = ICE_COLS * ICE_CELL


class Popo:
    def __init__(self, stage, cx, floor):
        self.stage = stage
        self.width = ICE_PLAYER_W
        self.height = ICE_PLAYER_H
        self.cx = float(cx)
        self.bottom = float(stage_mod.floor_top_world(floor))
        self.vel_y = 0.0
        self.state = "ground"
        self.facing = 1
        self.walk_anim = 0.0
        self.on_floor = floor
        self.spin_angle = 0.0
        self.swing = 0.0        # ハンマー振り演出（0=収納, >0=振り中）

    # --- 位置ヘルパー -------------------------------------------------
    @property
    def x(self):
        return self.cx - self.width / 2

    @property
    def top(self):
        return self.bottom - self.height

    def get_world_rect(self):
        return pygame.Rect(int(self.x), int(self.top), self.width, self.height)

    def get_screen_rect(self, cam_y):
        r = self.get_world_rect()
        r.y -= int(cam_y)
        return r

    # --- 入力 ---------------------------------------------------------
    def jump(self):
        if self.state == "ground":
            self.vel_y = -ICE_JUMP_POWER
            self.state = "air"
            self.swing = 0.18   # 飛び上がりでハンマーを振る演出
            return True
        return False

    def start_dying(self):
        self.state = "dying"
        self.spin_angle = 0.0
        self.vel_y = -260

    # --- 更新 ---------------------------------------------------------
    def update(self, dt, keys):
        """1 フレーム更新。割れた氷リスト [(floor, col), ...] を返す。"""
        if self.swing > 0:
            self.swing = max(0.0, self.swing - dt)

        if self.state == "ground":
            return self._update_ground(dt, keys)
        if self.state == "air":
            return self._update_air(dt, keys)
        return []

    def update_dying(self, dt):
        self.spin_angle += dt * 560
        self.vel_y += ICE_GRAVITY * 0.6 * dt
        self.bottom += self.vel_y * dt

    def _move_x(self, dt, keys, factor=1.0):
        move = (1 if keys[pygame.K_RIGHT] else 0) - (1 if keys[pygame.K_LEFT] else 0)
        if move != 0:
            self.facing = move
            self.cx += move * ICE_PLAYER_SPEED * factor * dt
            self.walk_anim += dt * 11
        # 横は世界の端で止める
        half = self.width / 2
        self.cx = max(WORLD_LEFT + half, min(WORLD_RIGHT - half, self.cx))
        return move

    def _update_ground(self, dt, keys):
        self._move_x(dt, keys)
        # 足元が抜けたら落下（穴の上に来た）
        col = self.stage.col_at(self.cx)
        if not self.stage.is_filled(self.on_floor, col):
            self.state = "air"
            self.vel_y = 0.0
        else:
            # 段の上面にスナップ
            self.bottom = stage_mod.floor_top_world(self.on_floor)
        return []

    def _update_air(self, dt, keys):
        self._move_x(dt, keys, factor=ICE_AIR_CONTROL)
        prev_bottom = self.bottom
        prev_top = self.top

        self.vel_y += ICE_GRAVITY * dt
        self.bottom += self.vel_y * dt

        events = []
        if self.vel_y < 0:
            # 上昇中：頭が氷ブロックに入ったら割る（頭突き）
            events = self._check_head_bump(prev_top)
        else:
            # 落下中：着地判定
            self._check_landing(prev_bottom)
        return events

    def _check_head_bump(self, prev_top):
        """頭上のブロックに接触したら割る／岩なら跳ね返す。"""
        head = self.top
        # 頭がまたいだ床の上面を探す（prev_top より上、head 以下に来たもの）
        for f in range(len(self.stage.rows)):
            top = stage_mod.floor_top_world(f)
            block_bottom = top + ICE_CELL
            # このブロックの下面を頭が上向きに通過したか
            if prev_top >= block_bottom - 1 and head <= block_bottom:
                col = self.stage.col_at(self.cx)
                if self.stage.rows[f][col] == stage_mod.ICE:
                    self.stage.break_ice(f, col)
                    # 割っても上昇は止めない（そのまま穴を抜けて上段へ届く）
                    return [(f, col)]
                elif self.stage.rows[f][col] == stage_mod.SOLID:
                    # 岩は割れない：頭がつかえて跳ね返る
                    self.bottom = block_bottom + self.height
                    self.vel_y = 60
                    return []
        return []

    def _check_landing(self, prev_bottom):
        col = self.stage.col_at(self.cx)
        for f in range(len(self.stage.rows)):
            if not self.stage.is_filled(f, col):
                continue
            top = stage_mod.floor_top_world(f)
            if prev_bottom <= top + 1 and self.bottom >= top:
                self.bottom = top
                self.vel_y = 0.0
                self.state = "ground"
                self.on_floor = f
                return

    # --- 描画 ---------------------------------------------------------
    def draw(self, screen, cam_y, blink=False):
        if blink:
            return
        surf = self._build_sprite()
        if self.facing < 0:
            surf = pygame.transform.flip(surf, True, False)
        if self.state == "dying":
            surf = pygame.transform.rotate(surf, self.spin_angle % 360)
        cx = int(self.cx)
        cy = int(self.bottom - self.height / 2 - cam_y)
        screen.blit(surf, surf.get_rect(center=(cx, cy)))

    def _build_sprite(self):
        """ポポ（青い防寒着のクライマー）を右向き基準で組む。"""
        w, h = self.width, self.height
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        step = int(self.walk_anim) % 2
        airborne = self.state in ("air", "dying")

        # フード付きの体（青）
        pygame.draw.rect(s, ICE_COLOR_POPO, (3, 6, w - 6, h - 12), border_radius=5)
        # フードの白縁
        pygame.draw.rect(s, ICE_COLOR_POPO_TRIM, (3, 4, w - 6, 5), border_radius=3)
        # 顔
        pygame.draw.rect(s, ICE_COLOR_POPO_FACE, (7, 8, w - 14, 8), border_radius=3)
        pygame.draw.rect(s, (30, 30, 30), (w - 10, 10, 2, 2))  # 目
        # おなかの白い模様
        pygame.draw.rect(s, ICE_COLOR_POPO_TRIM, (w // 2 - 3, 16, 6, h - 22))
        # 脚（歩行アニメ）
        swing = 3 if step == 0 else -3
        if airborne:
            swing = 4
        pygame.draw.rect(s, ICE_COLOR_POPO, (5 + swing, h - 6, 6, 6))
        pygame.draw.rect(s, ICE_COLOR_POPO, (w - 11 - swing, h - 6, 6, 6))

        # ハンマー（振り演出中は上に、通常は横に構える）
        if self.swing > 0:
            # 頭上へ振り上げ
            pygame.draw.rect(s, (110, 80, 40), (w - 8, -6, 3, 14))       # 柄
            pygame.draw.rect(s, ICE_COLOR_HAMMER_HEAD, (w - 12, -9, 11, 6),
                             border_radius=2)  # 頭
        else:
            pygame.draw.rect(s, (110, 80, 40), (w - 6, 12, 3, 12))       # 柄
            pygame.draw.rect(s, ICE_COLOR_HAMMER_HEAD, (w - 9, 20, 10, 6),
                             border_radius=2)
        return s
