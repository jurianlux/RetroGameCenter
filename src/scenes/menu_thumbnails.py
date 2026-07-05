"""メニュー用のゲームサムネイルを描画する。

本作の方針どおり画像ファイルは使わず、各ゲームらしいミニ絵を pygame の
プリミティブで Surface に描いて返す。1度作った Surface はキャッシュする。
"""

import pygame
from config import (
    COLOR_BLACK, COLOR_WHITE, COLOR_YELLOW, COLOR_GRAY,
    COLOR_GIRDER, COLOR_LADDER, COLOR_BARREL, COLOR_BARREL_BAND,
    COLOR_DK, COLOR_DK_FACE, COLOR_PAULINE, COLOR_RED,
    DK81_COLOR_OIL_DRUM, DK81_COLOR_OIL_BAND, DK81_COLOR_FLAME,
    DK81_COLOR_FLAME_CORE, DK81_COLOR_SKIN,
    COLOR_T_CYAN, COLOR_T_YELLOW, COLOR_T_PURPLE, COLOR_T_GREEN,
    COLOR_T_RED, COLOR_T_BLUE, COLOR_T_ORANGE, COLOR_T_GRID,
    ICE_COLOR_SKY_TOP, ICE_COLOR_SKY_BOT, ICE_COLOR_ICE, ICE_COLOR_ICE_HI,
    ICE_COLOR_ICE_DARK, ICE_COLOR_POPO, ICE_COLOR_POPO_TRIM,
    ICE_COLOR_POPO_FACE, ICE_COLOR_CONDOR, ICE_COLOR_TOPI, ICE_COLOR_HAMMER_HEAD,
)

_cache = {}


def get_thumbnail(key, size):
    """key に対応するサムネイル Surface を size=(w, h) で返す。"""
    cache_key = (key, size)
    if cache_key not in _cache:
        _cache[cache_key] = _render(key, size)
    return _cache[cache_key]


def _render(key, size):
    w, h = size
    surf = pygame.Surface(size)
    surf.fill(COLOR_BLACK)
    drawer = _DRAWERS.get(key, _draw_coming_soon)
    drawer(surf, w, h)
    return surf


# --- 各ゲームのサムネイル ------------------------------------------------

def _draw_donkey_kong(surf, w, h):
    """斜め鉄骨・はしご・コング・樽・ポーリンのミニ絵。"""
    # 斜めに重なる鉄骨（下から上へ、交互に傾ける）
    rows = 4
    margin = int(w * 0.08)
    girder_h = max(3, int(h * 0.045))
    top = int(h * 0.16)
    bottom = int(h * 0.88)
    gap = (bottom - top) / (rows - 1)
    for i in range(rows):
        y = int(bottom - i * gap)
        tilt = int(h * 0.05) * (1 if i % 2 == 0 else -1)
        if i % 2 == 0:
            p1 = (margin, y + tilt)
            p2 = (w - margin, y - tilt)
        else:
            p1 = (margin, y - tilt)
            p2 = (w - margin, y + tilt)
        pygame.draw.line(surf, COLOR_GIRDER, p1, p2, girder_h)

    # はしご（2 本）
    for lx in (int(w * 0.30), int(w * 0.68)):
        pygame.draw.line(surf, COLOR_LADDER, (lx, top), (lx, bottom), 2)
        pygame.draw.line(surf, COLOR_LADDER, (lx + 8, top), (lx + 8, bottom), 2)
        for ry in range(top, bottom, max(6, int(h * 0.05))):
            pygame.draw.line(surf, COLOR_LADDER, (lx, ry), (lx + 8, ry), 2)

    # コング（左上）
    kx, ky = int(w * 0.24), top - int(h * 0.02)
    kw = int(w * 0.20)
    pygame.draw.rect(surf, COLOR_DK, (kx - kw // 2, ky - kw, kw, kw), border_radius=4)
    fw = int(kw * 0.6)
    pygame.draw.rect(surf, COLOR_DK_FACE, (kx - fw // 2, ky - kw + 3, fw, fw), border_radius=3)

    # ポーリン（右上）
    px, py = int(w * 0.80), top - int(h * 0.04)
    pygame.draw.circle(surf, COLOR_DK_FACE, (px, py), max(2, int(w * 0.03)))
    pygame.draw.rect(surf, COLOR_PAULINE,
                     (px - int(w * 0.03), py, int(w * 0.06), int(h * 0.10)))

    # 転がる樽
    for bx, by in ((int(w * 0.55), int(h * 0.45)), (int(w * 0.40), int(h * 0.72))):
        r = max(3, int(w * 0.045))
        pygame.draw.circle(surf, COLOR_BARREL, (bx, by), r)
        pygame.draw.circle(surf, COLOR_BARREL_BAND, (bx, by), r, 1)


def _draw_donkey_kong_81(surf, w, h):
    """DK と同系だがオイルドラムと炎を加えた '81 版。"""
    _draw_donkey_kong(surf, w, h)
    # 左下にオイルドラム＋炎
    dx = int(w * 0.14)
    dy = int(h * 0.86)
    dw, dh = int(w * 0.10), int(h * 0.14)
    pygame.draw.rect(surf, DK81_COLOR_OIL_DRUM,
                     (dx - dw // 2, dy - dh, dw, dh), border_radius=2)
    pygame.draw.line(surf, DK81_COLOR_OIL_BAND,
                     (dx - dw // 2, dy - dh // 2), (dx + dw // 2, dy - dh // 2), 1)
    # 炎（外炎＋芯）
    fx, fy = dx, dy - dh
    pygame.draw.polygon(surf, DK81_COLOR_FLAME, [
        (fx - dw // 3, fy), (fx, fy - int(h * 0.11)), (fx + dw // 3, fy)])
    pygame.draw.polygon(surf, DK81_COLOR_FLAME_CORE, [
        (fx - dw // 6, fy), (fx, fy - int(h * 0.06)), (fx + dw // 6, fy)])
    # 「'81」バッジ
    font = pygame.font.Font(None, max(14, int(h * 0.18)))
    badge = font.render("'81", True, COLOR_YELLOW)
    surf.blit(badge, badge.get_rect(bottomright=(w - 4, h - 3)))


# T スピン風に並べたテトリミノ盤面（列ごとの積み高さと色）
_TETRIS_STACK = [
    (COLOR_T_BLUE, 2), (COLOR_T_BLUE, 2), (COLOR_T_RED, 3), (COLOR_T_GREEN, 4),
    (COLOR_T_ORANGE, 3), (COLOR_T_ORANGE, 1), (COLOR_T_PURPLE, 2),
]


def _draw_tetris(surf, w, h):
    """積み上がったブロックと落下中のミノ。"""
    cols = len(_TETRIS_STACK)
    pad = int(w * 0.10)
    board_w = w - pad * 2
    board_h = int(h * 0.86)
    cell = min(board_w // cols, board_h // 6)
    board_w = cell * cols
    ox = (w - board_w) // 2
    oy = h - int(h * 0.07) - cell  # 最下段

    # グリッド枠
    rows_shown = 6
    pygame.draw.rect(surf, COLOR_T_GRID,
                     (ox - 2, oy - (rows_shown - 1) * cell - 2,
                      board_w + 4, rows_shown * cell + 4), 2)

    def block(cx, cy, color):
        rect = pygame.Rect(cx, cy, cell, cell)
        pygame.draw.rect(surf, color, rect)
        pygame.draw.rect(surf, COLOR_BLACK, rect, 1)
        hi = pygame.Rect(cx + 2, cy + 2, cell - 4, max(2, cell // 4))
        pygame.draw.rect(surf, COLOR_WHITE, hi, 0)

    # 積みブロック
    for c, (color, height) in enumerate(_TETRIS_STACK):
        for r in range(height):
            block(ox + c * cell, oy - r * cell, color)

    # 落下中の T ミノ（上部中央）
    ty = oy - 5 * cell
    tx = ox + 2 * cell
    for dc, dr in ((0, 0), (1, 0), (2, 0), (1, 1)):
        block(tx + dc * cell, ty + dr * cell, COLOR_T_CYAN)


def _draw_ice_climber(surf, w, h):
    """氷の山を登るポポ・氷ブロック（穴あり）・コンドルのミニ絵。"""
    # 空グラデ
    for y in range(0, h, 3):
        t = y / h
        col = (int(ICE_COLOR_SKY_TOP[0] + (ICE_COLOR_SKY_BOT[0] - ICE_COLOR_SKY_TOP[0]) * t),
               int(ICE_COLOR_SKY_TOP[1] + (ICE_COLOR_SKY_BOT[1] - ICE_COLOR_SKY_TOP[1]) * t),
               int(ICE_COLOR_SKY_TOP[2] + (ICE_COLOR_SKY_BOT[2] - ICE_COLOR_SKY_TOP[2]) * t))
        pygame.draw.rect(surf, col, (0, y, w, 3))

    cell = max(8, int(w * 0.12))
    cols = w // cell
    rows = 3
    top = h - rows * cell - int(h * 0.06)

    def ice_block(bx, by):
        r = pygame.Rect(bx, by, cell, cell)
        pygame.draw.rect(surf, ICE_COLOR_ICE, r)
        pygame.draw.rect(surf, ICE_COLOR_ICE_HI, (bx, by, cell, 3))
        pygame.draw.rect(surf, ICE_COLOR_ICE_DARK, r, 1)

    # 3 段の氷床（各段に穴を 1 つ空ける）
    for row in range(rows):
        by = top + row * cell
        gap = 1 + row  # 段ごとに穴の位置をずらす
        for c in range(cols):
            if c == gap:
                continue  # 穴
            ice_block(c * cell, by)

    # ポポ（下段、ハンマーを振り上げる）
    px = int(w * 0.30)
    py = top + rows * cell - cell
    pw = max(8, int(cell * 0.8))
    pygame.draw.rect(surf, ICE_COLOR_POPO, (px, py, pw, cell), border_radius=3)
    pygame.draw.rect(surf, ICE_COLOR_POPO_TRIM, (px, py, pw, 3))
    pygame.draw.rect(surf, ICE_COLOR_POPO_FACE, (px + 2, py + 3, pw - 4, 4))
    # 振り上げたハンマー
    pygame.draw.rect(surf, ICE_COLOR_HAMMER_HEAD, (px + pw - 2, py - 6, 6, 4))

    # トッピー（上段）
    tx = int(w * 0.66)
    ty = top - int(cell * 0.6)
    pygame.draw.ellipse(surf, ICE_COLOR_TOPI, (tx, ty, int(cell * 0.9), int(cell * 0.6)))

    # コンドル（上空）
    cxp, cyp = int(w * 0.72), int(h * 0.16)
    pygame.draw.ellipse(surf, ICE_COLOR_CONDOR, (cxp - 7, cyp - 3, 14, 8))
    pygame.draw.polygon(surf, ICE_COLOR_CONDOR,
                        [(cxp - 5, cyp), (cxp - 18, cyp - 6), (cxp - 6, cyp + 2)])
    pygame.draw.polygon(surf, ICE_COLOR_CONDOR,
                        [(cxp + 5, cyp), (cxp + 18, cyp - 6), (cxp + 6, cyp + 2)])


def _draw_coming_soon(surf, w, h):
    """準備中ゲーム用のプレースホルダ（?マークと点線枠）。"""
    surf.fill((18, 18, 24))
    # 点線風の枠
    step = max(6, int(w * 0.08))
    for x in range(step, w - step, step):
        pygame.draw.line(surf, COLOR_GRAY, (x, int(h * 0.12)),
                         (x + step // 2, int(h * 0.12)), 2)
        pygame.draw.line(surf, COLOR_GRAY, (x, int(h * 0.88)),
                         (x + step // 2, int(h * 0.88)), 2)
    font = pygame.font.Font(None, int(h * 0.6))
    q = font.render("?", True, COLOR_GRAY)
    surf.blit(q, q.get_rect(center=(w // 2, h // 2)))


_DRAWERS = {
    "donkey_kong": _draw_donkey_kong,
    "donkey_kong_81": _draw_donkey_kong_81,
    "tetris": _draw_tetris,
    "ice_climber": _draw_ice_climber,
}
