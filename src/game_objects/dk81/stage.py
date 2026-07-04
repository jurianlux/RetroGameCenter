"""ドンキーコング '81 の 25m ステージ地形定義とクエリ関数。

既存 game_objects/level.py の実証済みパターンを踏襲した自己完結モジュール。
（level.py は import しない — 既存 donkey_kong と完全に独立）

- 鉄骨（girder）: (x_left, x_right, y_left, y_right) の斜め線分。
  上下交互に傾け、樽が端で落ちて逆向きに転がる＝ジグザグ。
  index 0 が最下段（プレイヤー開始）、index が大きいほど上段。
- はしご（ladder）: (x, lower_index, upper_index, broken)。
  broken=True は「途中が壊れている」はしごで、プレイヤーも樽も使えない。
- オイルドラム: 最下段左（OIL_DRUM_RECT）。A では飾り、B で発火に使用。
- ハンマー位置: HAMMER_SPAWNS（A では定義のみ、B で使用）。
"""

import pygame
from config import (
    COLOR_GIRDER, COLOR_GIRDER_DARK, COLOR_LADDER,
    DK81_COLOR_OIL_DRUM, DK81_COLOR_OIL_BAND,
    DK81_COLOR_FLAME, DK81_COLOR_FLAME_CORE,
)

GIRDER_THICKNESS = 14

# 各鉄骨: (x_left, x_right, y_left, y_right)
GIRDERS = [
    (0,   800, 572, 532),   # G0 最下段（低い側=左。左端にオイルドラム／プレイヤー開始）
    (0,   800, 452, 492),   # G1 低い側=右
    (0,   800, 412, 372),   # G2 低い側=左
    (0,   800, 292, 332),   # G3 低い側=右
    (0,   800, 252, 212),   # G4 低い側=左
    (0,   800, 132, 172),   # G5 最上段（低い側=右。左端に DK）
    (330, 470,  92,  92),   # G6 ポーリンの足場（水平）
]

# はしご: (x, lower_girder_index, upper_girder_index, broken)
LADDERS = [
    (110, 0, 1, False),
    (640, 0, 1, True),     # 壊れはしご（渡れない）
    (690, 1, 2, False),
    (250, 1, 2, True),     # 壊れはしご
    (140, 2, 3, False),
    (520, 2, 3, False),
    (660, 3, 4, False),
    (300, 3, 4, True),     # 壊れはしご
    (220, 4, 5, False),
    (560, 4, 5, False),
    (400, 5, 6, False),    # ポーリンの足場へ
]

PAULINE_GIRDER = 6


def surface_y(girder_index, x):
    """指定した鉄骨の x 位置における表面 y を返す（線形補間）。"""
    xl, xr, yl, yr = GIRDERS[girder_index]
    if xr == xl:
        return yl
    t = (x - xl) / (xr - xl)
    t = max(0.0, min(1.0, t))
    return yl + (yr - yl) * t


def girder_range(girder_index):
    xl, xr, _, _ = GIRDERS[girder_index]
    return xl, xr


def downhill_dir(girder_index):
    """下り方向（樽が転がる向き）。+1=右, -1=左。"""
    _, _, yl, yr = GIRDERS[girder_index]
    if yr > yl:
        return 1
    if yl > yr:
        return -1
    return 1


def ladder_top_y(ladder):
    """はしごの上端 y（上段鉄骨の表面）。"""
    x, _lower, upper, _broken = ladder
    return surface_y(upper, x)


def ladder_bottom_y(ladder):
    """はしごの下端 y（下段鉄骨の表面）。"""
    x, lower, _upper, _broken = ladder
    return surface_y(lower, x)


def find_landing_girder(center_x, prev_bottom, new_bottom):
    """落下中に下方向へ通過した鉄骨を探す。

    着地した鉄骨 index と表面 y を返す。無ければ None。
    """
    best = None
    for i in range(len(GIRDERS)):
        xl, xr, _, _ = GIRDERS[i]
        if not (xl <= center_x <= xr):
            continue
        s = surface_y(i, center_x)
        # 前フレームは表面より上、今フレームで表面以下に到達した
        if prev_bottom <= s + 1 and new_bottom >= s:
            if best is None or s < best[1]:
                # 複数候補があるときは「より上にある（先に当たる）」鉄骨を選ぶ
                best = (i, s)
    return best


# --- 配置（DK・ポーリン・樽・プレイヤー・オイルドラム・ハンマー） ---------

DK_POS = (70, int(surface_y(5, 70)))       # G5 左端付近（高い側）に立つ
BARREL_SPAWN = (140, 5)                    # (x, girder_index) DK の右手側
PLAYER_START = (100, 0)                    # (x, girder_index) 最下段左寄り

# オイルドラム（最下段左端）
OIL_DRUM_RECT = pygame.Rect(24, 0, 36, 44)
OIL_DRUM_RECT.bottom = int(surface_y(0, OIL_DRUM_RECT.centerx)) + 1

# ハンマー設置位置（Milestone B で使用。A では定義のみ）
HAMMER_SPAWNS = [(180, 2), (600, 4)]


def pauline_rect():
    """ポーリン（＝クリア判定）の矩形。"""
    xl, xr, yl, _ = GIRDERS[PAULINE_GIRDER]
    cx = (xl + xr) // 2
    return pygame.Rect(cx - 14, yl - 34, 28, 34)


# --- 描画 -----------------------------------------------------------------

def draw(screen):
    """鉄骨・はしご・オイルドラムを描画する。"""
    # はしご（先に描いて鉄骨を上に重ねる）
    for ladder in LADDERS:
        x, lower, upper, broken = ladder
        top = surface_y(upper, x)
        bottom = surface_y(lower, x)
        if broken:
            _draw_broken_ladder(screen, x, top, bottom)
        else:
            _draw_ladder(screen, x, top, bottom)

    # 鉄骨
    for i in range(len(GIRDERS)):
        xl, xr, yl, yr = GIRDERS[i]
        pygame.draw.line(screen, COLOR_GIRDER, (xl, yl), (xr, yr), GIRDER_THICKNESS)
        # 下側に影のラインを入れて立体感を出す
        pygame.draw.line(screen, COLOR_GIRDER_DARK,
                         (xl, yl + GIRDER_THICKNESS // 2),
                         (xr, yr + GIRDER_THICKNESS // 2), 3)
        # リベット風の点を等間隔に打つ
        span = xr - xl
        steps = max(1, span // 40)
        for k in range(steps + 1):
            rx = xl + span * k / steps
            ry = surface_y(i, rx)
            pygame.draw.circle(screen, COLOR_GIRDER_DARK, (int(rx), int(ry) - 3), 2)

    _draw_oil_drum(screen)


def _draw_ladder(screen, x, top, bottom, width=22):
    left = x - width // 2
    right = x + width // 2
    pygame.draw.line(screen, COLOR_LADDER, (left, top), (left, bottom), 3)
    pygame.draw.line(screen, COLOR_LADDER, (right, top), (right, bottom), 3)
    rung = int(top)
    step = 14
    while rung < bottom:
        pygame.draw.line(screen, COLOR_LADDER, (left, rung), (right, rung), 3)
        rung += step


def _draw_broken_ladder(screen, x, top, bottom, width=22):
    """壊れはしご：上下の断片だけを描き、中央が欠けている。"""
    stub = min(26, (bottom - top) / 3)
    _draw_ladder(screen, x, top, top + stub, width)
    _draw_ladder(screen, x, bottom - stub, bottom, width)


def _draw_oil_drum(screen):
    r = OIL_DRUM_RECT
    pygame.draw.rect(screen, DK81_COLOR_OIL_DRUM, r, border_radius=3)
    pygame.draw.line(screen, DK81_COLOR_OIL_BAND,
                     (r.x + 2, r.y + 10), (r.right - 3, r.y + 10), 2)
    pygame.draw.line(screen, DK81_COLOR_OIL_BAND,
                     (r.x + 2, r.bottom - 12), (r.right - 3, r.bottom - 12), 2)
    # 炎（点滅する2種の形）
    flick = (pygame.time.get_ticks() // 130) % 2
    cx = r.centerx
    top = r.y
    if flick == 0:
        pts = [(cx - 10, top), (cx - 4, top - 14), (cx, top - 6),
               (cx + 5, top - 18), (cx + 10, top)]
    else:
        pts = [(cx - 10, top), (cx - 5, top - 17), (cx, top - 8),
               (cx + 4, top - 13), (cx + 10, top)]
    pygame.draw.polygon(screen, DK81_COLOR_FLAME, pts)
    pygame.draw.polygon(screen, DK81_COLOR_FLAME_CORE,
                        [(cx - 4, top), (cx, top - 8), (cx + 4, top)])
