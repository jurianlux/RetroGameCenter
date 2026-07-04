"""テトリミノ（7種のブロック）の形状・回転・色の定義と Tetromino クラス。

各ピースは「回転状態のリスト」を持ち、各状態は 4 セルの (col, row) オフセット集合。
基準は小さなボックス内の相対座標で、盤面上の絶対座標は (x + col, y + row) で求める。
SRS の厳密再現はしない（簡易回転 ＋ 簡易壁蹴り）。
"""

from config import (
    COLOR_T_CYAN, COLOR_T_YELLOW, COLOR_T_PURPLE, COLOR_T_GREEN,
    COLOR_T_RED, COLOR_T_BLUE, COLOR_T_ORANGE,
)

# 形状ごとの回転状態。各状態は (col, row) のリスト（4セル）。
SHAPES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

COLORS = {
    "I": COLOR_T_CYAN,
    "O": COLOR_T_YELLOW,
    "T": COLOR_T_PURPLE,
    "S": COLOR_T_GREEN,
    "Z": COLOR_T_RED,
    "J": COLOR_T_BLUE,
    "L": COLOR_T_ORANGE,
}

KINDS = ["I", "O", "T", "S", "Z", "J", "L"]


class Tetromino:
    """落下中のピース。状態計算に専念し、衝突判定は Board 側に委ねる。"""

    def __init__(self, kind, x, y, rotation=0):
        self.kind = kind
        self.x = x
        self.y = y
        self.rotation = rotation

    @property
    def color(self):
        return COLORS[self.kind]

    def rotation_count(self):
        """この種類が持つ回転状態の数。"""
        return len(SHAPES[self.kind])

    def cells(self, rotation=None, x=None, y=None):
        """指定（省略時は現在）状態の盤面上の絶対セル座標 [(gx, gy), ...] を返す。"""
        rot = self.rotation if rotation is None else rotation
        ox = self.x if x is None else x
        oy = self.y if y is None else y
        rot %= len(SHAPES[self.kind])
        return [(ox + cx, oy + cy) for (cx, cy) in SHAPES[self.kind][rot]]

    def next_rotation(self):
        """右回転後の状態インデックス。"""
        return (self.rotation + 1) % len(SHAPES[self.kind])
