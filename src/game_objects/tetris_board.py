"""テトリスの盤面（固定ブロック）を保持し、衝突判定・ライン消去を行う。

描画を一切持たないため、ヘッドレスでロジック検証できる。
grid の各セルは空きが None、固定ブロックは種類名（"I" など）を格納する。
"""

from config import TETRIS_COLS, TETRIS_ROWS


class Board:
    def __init__(self, cols=TETRIS_COLS, rows=TETRIS_ROWS):
        self.cols = cols
        self.rows = rows
        self.grid = [[None for _ in range(cols)] for _ in range(rows)]

    def reset(self):
        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]

    def is_valid(self, cells):
        """セル集合が盤面内かつ空きに収まるか（壁・床・既存ブロックと衝突しないか）。"""
        for (cx, cy) in cells:
            if cx < 0 or cx >= self.cols or cy >= self.rows:
                return False
            # 天井より上（cy < 0）は出現直後の許容として通す
            if cy < 0:
                continue
            if self.grid[cy][cx] is not None:
                return False
        return True

    def lock(self, cells, kind):
        """セルを盤面に固定する。範囲外（cy<0）は無視。"""
        for (cx, cy) in cells:
            if 0 <= cy < self.rows and 0 <= cx < self.cols:
                self.grid[cy][cx] = kind

    def clear_lines(self):
        """揃った行を消して上を詰め、消した行数を返す。"""
        remaining = [row for row in self.grid if any(cell is None for cell in row)]
        cleared = self.rows - len(remaining)
        if cleared:
            empty = [[None for _ in range(self.cols)] for _ in range(cleared)]
            self.grid = empty + remaining
        return cleared
