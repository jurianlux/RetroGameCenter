"""アイスクライマー 1 ステージの地形モデルと描画。

DK81 の stage.py と同じく「自己完結モジュール」方針。既存の level.py 等は
import しない。地形はグリッドで持ち、ワールド座標（y は下ほど大きい）で扱う。

グリッド:
  - 幅 ICE_COLS セル、各セル ICE_CELL px 四方。
  - 「床（floor）」は ICE_FLOOR_GAP セル間隔で ICE_FLOORS 段。floor 0 が最下段。
  - 最下段（floor 0）は割れない岩土台 GROUND。上の段は割れる氷 ICE と穴 EMPTY。
  - 各セル状態: SOLID(=岩) / ICE(=割れる氷) / EMPTY(=穴)。

ワールド座標系:
  - 各床の「氷ブロックの上面 y」を floor_top_world(floor) で返す。
  - 下ほど y が大きい。floor 0 の上面が最大（画面下）、floor が上がるほど y が小さい。
  - カメラ（scene 側で管理）でスクロールして画面に落とし込む。

描画は draw(screen, cam_y) で、cam_y だけ上にずらして描く。
"""

import random

import pygame

from config import (
    ICE_CELL, ICE_COLS, ICE_FLOOR_GAP, ICE_FLOORS,
    ICE_COLOR_ICE, ICE_COLOR_ICE_HI, ICE_COLOR_ICE_DARK,
    ICE_COLOR_GROUND, ICE_COLOR_GROUND_HI,
    SCREEN_WIDTH, SCREEN_HEIGHT,
)

# セル状態
EMPTY = 0
ICE = 1
SOLID = 2

# floor 0 の氷上面をワールド y=0 とし、上の段ほど y が小さくなる（負）。
# floor f の上面 = -(f * ICE_FLOOR_GAP) * ICE_CELL
FLOOR_STEP_PX = ICE_FLOOR_GAP * ICE_CELL

# 山頂（ボーナス）ゾーンの上面ワールド y（最上段よりさらに上）
SUMMIT_TOP_WORLD = -(ICE_FLOORS * FLOOR_STEP_PX) - ICE_CELL * 2


def floor_top_world(floor):
    """floor の氷ブロック上面のワールド y。"""
    return -(floor * FLOOR_STEP_PX)


class Stage:
    """1 ステージの地形。可変（氷が割れる・穴が塞がれる）なのでインスタンス。"""

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        # rows[floor] = 各列のセル状態リスト（長さ ICE_COLS）
        self.rows = []
        self._build()

    # --- 生成 ---------------------------------------------------------
    def _build(self):
        for f in range(ICE_FLOORS):
            self.rows.append(self._make_floor(f))

    def _make_floor(self, f):
        if f == 0:
            # 最下段：全面が割れない岩土台（登り始めの安全地帯）
            return [SOLID] * ICE_COLS

        cols = [ICE] * ICE_COLS
        # 各段に 1〜2 個のギャップ（穴）を空ける。ジャンプで通れるルートを保証。
        gaps = self.rng.randint(1, 2)
        chosen = set()
        for _ in range(gaps):
            # 端すぎない位置に穴を作る
            gx = self.rng.randint(2, ICE_COLS - 3)
            chosen.add(gx)
        for gx in chosen:
            cols[gx] = EMPTY
        return cols

    # --- クエリ -------------------------------------------------------
    def cell_rect_world(self, floor, col):
        """(floor, col) セルのワールド矩形。"""
        top = floor_top_world(floor)
        x = col * ICE_CELL
        return pygame.Rect(x, int(top), ICE_CELL, ICE_CELL)

    def col_at(self, world_x):
        return int(world_x // ICE_CELL)

    def is_filled(self, floor, col):
        """そのセルが乗れる・当たる（ICE か SOLID）か。"""
        if floor < 0 or floor >= ICE_FLOORS:
            return False
        if col < 0 or col >= ICE_COLS:
            return True  # 画面端の外は壁扱い（落下防止でなく横制限は scene 側）
        return self.rows[floor][col] != EMPTY

    def surface_floor_at(self, world_x, from_world_y):
        """world_x 列で、from_world_y 以下（下方向）に最初に現れる着地面を探す。

        戻り値: (floor, top_world_y) または None。
        from_world_y より下（y が大きい側）にある最初の filled セル上面を返す。
        """
        col = self.col_at(world_x)
        best = None
        for f in range(ICE_FLOORS):
            top = floor_top_world(f)
            if not self.is_filled(f, col):
                continue
            # この床の上面が from_world_y 以下（同じか下）にある
            if top >= from_world_y - 1:
                if best is None or top < best[1]:
                    best = (f, top)
        return best

    def break_ice(self, floor, col):
        """氷ブロックを割る。割れたら True（SOLID や EMPTY は割れない）。"""
        if floor < 0 or floor >= ICE_FLOORS:
            return False
        if col < 0 or col >= ICE_COLS:
            return False
        if self.rows[floor][col] == ICE:
            self.rows[floor][col] = EMPTY
            return True
        return False

    def repair_ice(self, floor, col):
        """穴を氷で塞ぐ（トッピー用）。塞げたら True。"""
        if floor <= 0 or floor >= ICE_FLOORS:
            return False  # 最下段（岩）は対象外
        if col < 0 or col >= ICE_COLS:
            return False
        if self.rows[floor][col] == EMPTY:
            self.rows[floor][col] = ICE
            return True
        return False

    def gaps_on_floor(self, floor):
        """floor 上の穴（EMPTY）の列 index を返す。"""
        if floor <= 0 or floor >= ICE_FLOORS:
            return []
        return [c for c, v in enumerate(self.rows[floor]) if v == EMPTY]

    # --- 描画 ---------------------------------------------------------
    def draw(self, screen, cam_y):
        """cam_y: 画面上端に対応するワールド y。world_y - cam_y = 画面 y。"""
        for f in range(ICE_FLOORS):
            top = floor_top_world(f)
            sy = top - cam_y
            # 画面外の段はスキップ（上下に少し余裕）
            if sy > SCREEN_HEIGHT + ICE_CELL or sy < -ICE_CELL * 3:
                continue
            for c in range(ICE_COLS):
                state = self.rows[f][c]
                if state == EMPTY:
                    continue
                x = c * ICE_CELL
                self._draw_block(screen, x, int(sy), state)

    def _draw_block(self, screen, x, y, state):
        if state == SOLID:
            base, hi = ICE_COLOR_GROUND, ICE_COLOR_GROUND_HI
        else:
            base, hi = ICE_COLOR_ICE, ICE_COLOR_ICE_HI
        rect = pygame.Rect(x, y, ICE_CELL, ICE_CELL)
        pygame.draw.rect(screen, base, rect)
        # 上面ハイライト（光沢）
        pygame.draw.rect(screen, hi, (x, y, ICE_CELL, 5))
        # 左辺の明るいエッジ
        pygame.draw.line(screen, hi, (x + 1, y + 1), (x + 1, y + ICE_CELL - 2), 1)
        # 陰（右・下）
        if state != SOLID:
            pygame.draw.line(screen, ICE_COLOR_ICE_DARK,
                             (x + ICE_CELL - 1, y + 1),
                             (x + ICE_CELL - 1, y + ICE_CELL - 1), 2)
            pygame.draw.line(screen, ICE_COLOR_ICE_DARK,
                             (x + 1, y + ICE_CELL - 1),
                             (x + ICE_CELL - 1, y + ICE_CELL - 1), 2)
            # 氷のひび（軽い装飾）
            pygame.draw.line(screen, ICE_COLOR_ICE_DARK,
                             (x + ICE_CELL // 2, y + 6),
                             (x + ICE_CELL // 2 + 4, y + ICE_CELL - 6), 1)
        # ブロックの外枠
        pygame.draw.rect(screen, ICE_COLOR_ICE_DARK, rect, 1)
