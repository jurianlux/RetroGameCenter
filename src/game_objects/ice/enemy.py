"""アイスクライマーの敵：トッピー（Topi）と つらら（Icicle）。

すべてワールド座標（y は下ほど大きい）で持ち、scene が cam_y で画面に落とす。

Topi:
  - 割れていない床の上を左右に歩く。端や穴の縁で反転する。
  - 穴（EMPTY）の上に来ると立ち止まり、一定時間かけて氷で塞ぎ直す。
  - 上から踏まれる（プレイヤーが落下中に上面接触）と倒れる → +得点。
  - 横から触れるとプレイヤーがミス。

Icicle:
  - 床の裏（下面）にぶら下がって発生。予兆（震え）後に落下。
  - プレイヤーに当たるとミス。画面外まで落ちたら消滅。
"""

import pygame

from config import (
    ICE_CELL, ICE_COLS, ICE_TOPI_SPEED, ICE_TOPI_REPAIR_TIME,
    ICE_ICICLE_FALL, ICE_ICICLE_WARN,
    ICE_COLOR_TOPI, ICE_COLOR_TOPI_DARK, ICE_COLOR_ICICLE,
)
import game_objects.ice.stage as stage_mod

TOPI_W = 28
TOPI_H = 22


class Topi:
    def __init__(self, stage, floor, col, direction):
        self.stage = stage
        self.floor = floor
        self.width = TOPI_W
        self.height = TOPI_H
        self.cx = float(col * ICE_CELL + ICE_CELL / 2)
        self.dir = direction  # +1 右 / -1 左
        self.alive = True
        self.dying = False
        self.die_timer = 0.0
        self.repairing = False
        self.repair_timer = 0.0
        self.repair_col = None
        self.anim = 0.0

    @property
    def bottom(self):
        return stage_mod.floor_top_world(self.floor)

    def get_world_rect(self):
        top = self.bottom - self.height
        return pygame.Rect(int(self.cx - self.width / 2), int(top),
                           self.width, self.height)

    def stomp(self):
        """踏まれて倒れる。"""
        if not self.dying:
            self.dying = True
            self.die_timer = 0.35

    def update(self, dt):
        self.anim += dt
        if self.dying:
            self.die_timer -= dt
            if self.die_timer <= 0:
                self.alive = False
            return

        if self.repairing:
            self._update_repair(dt)
            return

        self._walk(dt)

    def _walk(self, dt):
        self.cx += self.dir * ICE_TOPI_SPEED * dt
        col = self.stage.col_at(self.cx)

        # 世界端で反転
        if self.cx < ICE_CELL / 2:
            self.cx = ICE_CELL / 2
            self.dir = 1
            return
        if self.cx > ICE_COLS * ICE_CELL - ICE_CELL / 2:
            self.cx = ICE_COLS * ICE_CELL - ICE_CELL / 2
            self.dir = -1
            return

        # 足元が穴 → 塞ぎ始める（原作の「割れた床を直す」動き）
        if not self.stage.is_filled(self.floor, col):
            self.repairing = True
            self.repair_timer = ICE_TOPI_REPAIR_TIME
            self.repair_col = col
            # 穴の中央に立つ
            self.cx = col * ICE_CELL + ICE_CELL / 2

    def _update_repair(self, dt):
        self.repair_timer -= dt
        if self.repair_timer <= 0:
            # 穴を塞ぐ（まだ穴なら）。塞いだら向きを反転して立ち去る。
            self.stage.repair_ice(self.floor, self.repair_col)
            self.repairing = False
            self.repair_col = None
            self.dir *= -1

    def draw(self, screen, cam_y):
        r = self.get_world_rect()
        r.y -= int(cam_y)
        if self.dying:
            # ぺしゃんこ演出
            flat = pygame.Rect(r.x, r.bottom - 7, r.width, 7)
            pygame.draw.ellipse(screen, ICE_COLOR_TOPI, flat)
            pygame.draw.ellipse(screen, ICE_COLOR_TOPI_DARK, flat, 1)
            return

        # 体（丸っこいアザラシ風）
        pygame.draw.ellipse(screen, ICE_COLOR_TOPI, r)
        pygame.draw.ellipse(screen, ICE_COLOR_TOPI_DARK, r, 2)
        # 顔の向き
        eye_x = r.centerx + self.dir * 6
        pygame.draw.circle(screen, (30, 30, 40), (eye_x, r.y + 8), 2)
        # 鼻先
        nose_x = r.centerx + self.dir * (self.width // 2 - 2)
        pygame.draw.circle(screen, ICE_COLOR_TOPI_DARK, (nose_x, r.centery), 3)
        # ヒレ（歩行でパタつく）
        flap = 2 if int(self.anim * 8) % 2 == 0 else -2
        pygame.draw.ellipse(screen, ICE_COLOR_TOPI_DARK,
                            (r.centerx - 4, r.bottom - 4 + flap, 8, 5))
        # 塞ぎ中は氷のかけらを示す
        if self.repairing:
            pygame.draw.rect(screen, ICE_COLOR_ICICLE,
                             (r.centerx - 4, r.y - 6, 8, 5), border_radius=1)


class Icicle:
    """天井からぶら下がって落ちるつらら。"""

    def __init__(self, world_x, top_world_y):
        self.cx = float(world_x)
        self.top = float(top_world_y)  # つらら上端（床の下面）
        self.width = 12
        self.length = 26
        self.warn = ICE_ICICLE_WARN
        self.falling = False
        self.alive = True
        self.shake = 0.0

    def get_world_rect(self):
        return pygame.Rect(int(self.cx - self.width / 2), int(self.top),
                           self.width, self.length)

    def update(self, dt, cam_y):
        if not self.falling:
            self.warn -= dt
            self.shake += dt
            if self.warn <= 0:
                self.falling = True
            return
        # 落下は等速（レトロ感・避けやすさ重視）
        self.top += ICE_ICICLE_FALL * dt
        # 画面下（cam 基準）より十分下に落ちたら消える
        if self.top - cam_y > 640:
            self.alive = False

    def draw(self, screen, cam_y):
        x = int(self.cx)
        y = int(self.top - cam_y)
        jitter = 0
        if not self.falling:
            jitter = 1 if int(self.shake * 30) % 2 == 0 else -1
        # 縦長の三角（下向きの氷柱）
        pts = [
            (x - self.width // 2 + jitter, y),
            (x + self.width // 2 + jitter, y),
            (x + jitter, y + self.length),
        ]
        pygame.draw.polygon(screen, ICE_COLOR_ICICLE, pts)
        pygame.draw.polygon(screen, (255, 255, 255),
                            [(x - 2 + jitter, y + 2), (x + jitter, y + 2),
                             (x + jitter, y + self.length - 6)], 0)
        pygame.draw.polygon(screen, (150, 200, 225), pts, 1)
