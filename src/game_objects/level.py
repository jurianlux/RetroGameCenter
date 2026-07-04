"""ドンキーコング ステージ 1 の地形定義とクエリ関数。

鉄骨（girder）は斜めの線分として定義し、任意の x における表面 y を
線形補間で求める。はしご（ladder）は接続する上下の鉄骨から y 範囲を導出する。
これにより「樽が斜面を転がり落ちてジグザグに下りてくる」挙動を実現する。
"""

import pygame
from config import (
    SCREEN_WIDTH, COLOR_GIRDER, COLOR_GIRDER_DARK, COLOR_LADDER,
)

GIRDER_THICKNESS = 14

# 各鉄骨: (x_left, x_right, y_left, y_right)
# 上下交互に傾けることで、樽が端から落ちて逆向きに転がる＝ジグザグになる。
# index 0 が最下段（プレイヤー開始）、index が大きいほど上段。
GIRDERS = [
    (0,   800, 575, 535),   # G0 最下段（低い側=左、プレイヤー開始）
    (0,   800, 455, 495),   # G1 低い側=右
    (0,   800, 415, 375),   # G2 低い側=左
    (0,   800, 295, 335),   # G3 低い側=右
    (0,   800, 255, 215),   # G4 低い側=左
    (0,   800, 135, 175),   # G5 最上段（低い側=右、左端にDK）
    (330, 470,  95,  95),   # G6 ポーリンの足場（水平）
]

# はしご: (x, lower_girder_index, upper_girder_index)
LADDERS = [
    (120, 0, 1),
    (680, 1, 2),
    (130, 2, 3),
    (670, 3, 4),
    (210, 4, 5),
    (560, 4, 5),   # 上段への別ルート（樽の降下にも使われる）
    (400, 5, 6),   # ポーリンの足場へ
]

# DK・ポーリン・樽生成位置
DK_POS = (70, 95)          # G5 左端付近（高い側）
BARREL_SPAWN = (135, 5)    # (x, girder_index)
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
    x, _lower, upper = ladder
    return surface_y(upper, x)


def ladder_bottom_y(ladder):
    """はしごの下端 y（下段鉄骨の表面）。"""
    x, lower, _upper = ladder
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


def draw(screen):
    """鉄骨とはしごを描画する。"""
    # はしご（先に描いて鉄骨を上に重ねる）
    for ladder in LADDERS:
        x, lower, upper = ladder
        top = surface_y(upper, x)
        bottom = surface_y(lower, x)
        _draw_ladder(screen, x, top, bottom)

    # 鉄骨
    for i in range(len(GIRDERS)):
        xl, xr, yl, yr = GIRDERS[i]
        pygame.draw.line(screen, COLOR_GIRDER, (xl, yl), (xr, yr), GIRDER_THICKNESS)
        # 下側に影のラインを入れて立体感を出す
        pygame.draw.line(screen, COLOR_GIRDER_DARK,
                         (xl, yl + GIRDER_THICKNESS // 2),
                         (xr, yr + GIRDER_THICKNESS // 2), 3)


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
