"""テトリスシーン。落下・回転・ライン消去・スコア・ゲームオーバーを扱う。

盤面ロジックは game_objects.tetris_board.Board / Tetromino に分離している。
Esc によるメニュー復帰は main.py の共通処理が担当するため、ここでは扱わない。
"""

import random
import pygame
from scenes.base_scene import BaseScene
from game_objects.tetris_board import Board
from game_objects.tetromino import Tetromino, KINDS, COLORS
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE, COLOR_GRAY,
    TETRIS_COLS, TETRIS_ROWS, TETRIS_CELL, TETRIS_BOARD_X, TETRIS_BOARD_Y,
    TETRIS_BASE_FALL, TETRIS_FALL_STEP, TETRIS_MIN_FALL,
    COLOR_T_GRID, COLOR_T_FRAME, COLOR_RED, COLOR_YELLOW,
)

# 出現位置（盤面上部、おおむね中央）
SPAWN_X = 3
SPAWN_Y = 0

# ライン消去得点（消去数 -> 基本点）。いずれも × level
LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 1000}


class TetrisScene(BaseScene):
    def on_enter(self):
        super().on_enter()
        self.font_big = pygame.font.Font(None, 64)
        self.font_mid = pygame.font.Font(None, 40)
        self.font_small = pygame.font.Font(None, 30)
        self.font_label = pygame.font.Font(None, 26)
        self.font_hint = pygame.font.Font(None, 22)
        self._reset_game()

    def _reset_game(self):
        self.board = Board(TETRIS_COLS, TETRIS_ROWS)
        self.state = "play"
        self.score = 0
        self.lines = 0
        self.level = 1
        self.fall_timer = 0.0
        self.fall_interval = self._calc_fall_interval()
        self.time = 0.0
        self.next_kind = random.choice(KINDS)
        self.current = None
        self._spawn_piece()

    def _calc_fall_interval(self):
        return max(TETRIS_MIN_FALL,
                   TETRIS_BASE_FALL - (self.level - 1) * TETRIS_FALL_STEP)

    def _spawn_piece(self):
        """next を現在ピースにし、新しい next を抽選する。置けなければゲームオーバー。"""
        kind = self.next_kind
        self.next_kind = random.choice(KINDS)
        self.current = Tetromino(kind, SPAWN_X, SPAWN_Y)
        if not self.board.is_valid(self.current.cells()):
            self.state = "over"

    # --- 入力 -----------------------------------------------------------
    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.state == "over":
            if event.key in (pygame.K_r, pygame.K_RETURN):
                self._reset_game()
            return

        if event.key == pygame.K_LEFT:
            self._try_move(-1, 0)
        elif event.key == pygame.K_RIGHT:
            self._try_move(1, 0)
        elif event.key == pygame.K_DOWN:
            if self._try_move(0, 1):
                self.score += 1  # ソフトドロップ加点
                self.fall_timer = 0.0
        elif event.key in (pygame.K_UP, pygame.K_x, pygame.K_z):
            self._try_rotate()
        elif event.key == pygame.K_SPACE:
            self._hard_drop()

    def _try_move(self, dx, dy):
        piece = self.current
        cells = piece.cells(x=piece.x + dx, y=piece.y + dy)
        if self.board.is_valid(cells):
            piece.x += dx
            piece.y += dy
            return True
        return False

    def _try_rotate(self):
        piece = self.current
        new_rot = piece.next_rotation()
        # 簡易壁蹴り: その場 → 右1 → 左1 → 右2 → 左2 の順で試す
        for dx in (0, 1, -1, 2, -2):
            cells = piece.cells(rotation=new_rot, x=piece.x + dx)
            if self.board.is_valid(cells):
                piece.rotation = new_rot
                piece.x += dx
                return True
        return False

    def _hard_drop(self):
        piece = self.current
        dropped = 0
        while self.board.is_valid(piece.cells(y=piece.y + 1)):
            piece.y += 1
            dropped += 1
        self.score += dropped * 2  # ハードドロップ加点
        self._lock_and_next()

    # --- 更新 -----------------------------------------------------------
    def update(self, dt):
        self.time += dt
        if self.state != "play":
            return

        self.fall_timer += dt
        if self.fall_timer >= self.fall_interval:
            self.fall_timer -= self.fall_interval
            if not self._try_move(0, 1):
                self._lock_and_next()

    def _lock_and_next(self):
        piece = self.current
        self.board.lock(piece.cells(), piece.kind)
        cleared = self.board.clear_lines()
        if cleared:
            self.score += LINE_SCORES.get(cleared, 0) * self.level
            self.lines += cleared
            self.level = self.lines // 10 + 1
            self.fall_interval = self._calc_fall_interval()
        self.fall_timer = 0.0
        self._spawn_piece()

    # --- 描画 -----------------------------------------------------------
    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        self._draw_board(screen)
        self._draw_locked(screen)
        if self.state == "play":
            self._draw_current(screen)
        self._draw_side_panel(screen)
        if self.state == "over":
            self._draw_game_over(screen)

    def _cell_rect(self, col, row):
        return pygame.Rect(
            TETRIS_BOARD_X + col * TETRIS_CELL,
            TETRIS_BOARD_Y + row * TETRIS_CELL,
            TETRIS_CELL, TETRIS_CELL,
        )

    def _draw_cell(self, screen, col, row, color):
        rect = self._cell_rect(col, row)
        pygame.draw.rect(screen, color, rect)
        # 立体感のためのハイライト＋縁取り
        pygame.draw.rect(screen, COLOR_BLACK, rect, 1)
        light = tuple(min(255, c + 50) for c in color)
        pygame.draw.line(screen, light, rect.topleft,
                         (rect.right - 1, rect.top))
        pygame.draw.line(screen, light, rect.topleft,
                         (rect.left, rect.bottom - 1))

    def _draw_board(self, screen):
        w = TETRIS_COLS * TETRIS_CELL
        h = TETRIS_ROWS * TETRIS_CELL
        # グリッド線
        for c in range(TETRIS_COLS + 1):
            x = TETRIS_BOARD_X + c * TETRIS_CELL
            pygame.draw.line(screen, COLOR_T_GRID,
                             (x, TETRIS_BOARD_Y), (x, TETRIS_BOARD_Y + h))
        for r in range(TETRIS_ROWS + 1):
            y = TETRIS_BOARD_Y + r * TETRIS_CELL
            pygame.draw.line(screen, COLOR_T_GRID,
                             (TETRIS_BOARD_X, y), (TETRIS_BOARD_X + w, y))
        # 枠
        pygame.draw.rect(screen, COLOR_T_FRAME,
                         (TETRIS_BOARD_X - 3, TETRIS_BOARD_Y - 3, w + 6, h + 6), 3)

    def _draw_locked(self, screen):
        grid = self.board.grid
        for r in range(TETRIS_ROWS):
            for c in range(TETRIS_COLS):
                kind = grid[r][c]
                if kind is not None:
                    self._draw_cell(screen, c, r, COLORS[kind])

    def _draw_current(self, screen):
        for (cx, cy) in self.current.cells():
            if cy >= 0:
                self._draw_cell(screen, cx, cy, self.current.color)

    def _draw_side_panel(self, screen):
        px = TETRIS_BOARD_X + TETRIS_COLS * TETRIS_CELL + 40  # ≈ 510
        # NEXT
        label = self.font_label.render("NEXT", True, COLOR_WHITE)
        screen.blit(label, (px, TETRIS_BOARD_Y + 6))
        self._draw_next(screen, px, TETRIS_BOARD_Y + 40)

        # HUD
        hud_y = TETRIS_BOARD_Y + 180
        for title, value in (("SCORE", f"{self.score:06d}"),
                             ("LEVEL", str(self.level)),
                             ("LINES", str(self.lines))):
            t = self.font_label.render(title, True, COLOR_GRAY)
            screen.blit(t, (px, hud_y))
            v = self.font_mid.render(value, True, COLOR_YELLOW)
            screen.blit(v, (px, hud_y + 24))
            hud_y += 76

        # 操作ヒント
        controls = [
            "LEFT/RIGHT: MOVE",
            "UP: ROTATE",
            "DOWN: SOFT DROP",
            "SPACE: HARD DROP",
            "ESC: MENU",
        ]
        cy = SCREEN_HEIGHT - 18 - len(controls) * 22
        for line in controls:
            t = self.font_hint.render(line, True, COLOR_GRAY)
            screen.blit(t, (px, cy))
            cy += 22

    def _draw_next(self, screen, px, py):
        cells = [(c, r) for (c, r) in
                 _shape_cells(self.next_kind)]
        cell = TETRIS_CELL - 4
        for (c, r) in cells:
            rect = pygame.Rect(px + c * cell, py + r * cell, cell, cell)
            color = COLORS[self.next_kind]
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, COLOR_BLACK, rect, 1)

    def _draw_game_over(self, screen):
        cx = TETRIS_BOARD_X + (TETRIS_COLS * TETRIS_CELL) // 2
        cy = TETRIS_BOARD_Y + (TETRIS_ROWS * TETRIS_CELL) // 2
        # 半透明の暗幕
        overlay = pygame.Surface(
            (TETRIS_COLS * TETRIS_CELL, TETRIS_ROWS * TETRIS_CELL), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (TETRIS_BOARD_X, TETRIS_BOARD_Y))

        title = self.font_big.render("GAME OVER", True, COLOR_RED)
        screen.blit(title, title.get_rect(center=(cx, cy - 30)))
        if int(self.time * 2) % 2 == 0:
            info = self.font_small.render("R: RESTART   ESC: MENU", True, COLOR_WHITE)
            screen.blit(info, info.get_rect(center=(cx, cy + 30)))


def _shape_cells(kind):
    """NEXT 表示用に種類の基本（rotation 0）セルを返す。"""
    from game_objects.tetromino import SHAPES
    return SHAPES[kind][0]
