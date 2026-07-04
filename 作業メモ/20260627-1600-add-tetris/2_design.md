# 設計: テトリス

`1_requirements.md` のスコープを実装するための方針メモ。既存のドンキーコングと
同じ構造（`BaseScene` 継承シーン ＋ `game_objects/` のロジック）に合わせる。

## 1. ファイル構成

| ファイル | 役割 | 新規/変更 |
|----------|------|-----------|
| `src/game_objects/tetromino.py` | テトリミノの形状・回転・色の定義、`Tetromino` クラス | 新規 |
| `src/game_objects/tetris_board.py` | 盤面（固定ブロック）保持・衝突判定・ライン消去 | 新規 |
| `src/scenes/tetris_scene.py` | ゲーム進行・入力・スコア・描画（`TetrisScene`） | 新規 |
| `src/config.py` | テトリス用の定数・色を追記 | 変更 |
| `src/scenes/menu_scene.py` | `GAMES` に `("TETRIS", "tetris")` を追加 | 変更 |
| `src/main.py` | `TetrisScene` を `register_scene("tetris", ...)` | 変更 |

> 盤面ロジックをシーンから分離するのは、ヘッドレス・スモークテスト（pygame 描画なし）で
> ライン消去・衝突・ゲームオーバー判定を検証しやすくするため。

## 2. データ構造

### テトリミノ定義（tetromino.py）

各ピースの回転状態を**事前計算した相対セル座標のリスト**で持つ。
SRS の厳密再現はしない（スコープ外）。基準は 4×4 ボックス内の `(col, row)` オフセット。

```python
# 形状ごとに「回転状態のリスト」を持つ。各状態は (x, y) セルの集合。
SHAPES = {
    "I": [...],  # 4状態（横・縦）
    "O": [...],  # 1状態（回転しても同じ）
    "T": [...],  # 4状態
    "S": [...], "Z": [...], "J": [...], "L": [...],
}
COLORS = { "I": COLOR_T_CYAN, "O": COLOR_T_YELLOW, ... }
```

`class Tetromino`:
- 属性: `kind`（種類名）, `rotation`（状態インデックス）, `x`, `y`（盤面上のセル位置）
- `cells(rotation=None, x=None, y=None)`: 現在（または指定）状態の絶対セル座標 `[(gx, gy), ...]` を返す
- 回転や移動の試行は「新しい状態のセルを board に渡して衝突チェック → OK なら反映」
  という流れにし、Tetromino 自身は状態計算に専念する

### 盤面（tetris_board.py）

`class Board`:
- `COLS = 10`, `ROWS = 20`
- `grid`: `ROWS × COLS` の 2次元リスト。空きは `None`、固定ブロックは色（または種類名）
- `is_valid(cells)`: セル集合が範囲内かつ空きに収まるか（左右壁・床・既存ブロックと衝突しないか）
- `lock(cells, kind)`: セルを grid に固定
- `clear_lines() -> int`: 揃った行を消して上を詰め、消した行数を返す

## 3. ゲーム進行（tetris_scene.py）

### 状態

`self.state`: `"play"` / `"over"`

主な属性: `board`, `current`(Tetromino), `next_kind`, `score`, `level`, `lines`,
`fall_timer`, `fall_interval`。

### 入力（handle_input: KEYDOWN）

| キー | 動作 |
|------|------|
| ← / → | 左右移動（`is_valid` チェック後に確定） |
| ↑ | 右回転（衝突時は ±1, ±2 セルの簡易壁蹴りを試行、ダメなら回転中止） |
| ↓ | ソフトドロップ（1セル下げ＋わずかに加点） |
| スペース | ハードドロップ（落下しきって即ロック） |
| R | ゲームオーバー時にリスタート |

> Esc によるメニュー復帰は `main.py` の共通処理が担当するため、シーン側では扱わない。

### 更新（update: dt）

- `play` 時: `fall_timer += dt`。`fall_timer >= fall_interval` で1セル落下。
  落下できなければロック処理へ。
- ロック処理: `board.lock()` → `clear_lines()` → スコア/ライン/レベル更新 →
  次ピース生成。生成位置で `is_valid` が False なら `state = "over"`。

### 落下→ロック→次ピースの流れ

```
落下不可？ ──No→ そのまま継続
   │Yes
   ▼
board.lock(current)
lines_cleared = board.clear_lines()
スコア・lines・level・fall_interval 更新
current = Tetromino(next_kind, 出現位置)
next_kind = ランダム抽選
is_valid(current)? ──No→ state="over"
```

## 4. スコア・レベル・速度の計算式

- **ライン消去得点**（レベル係数あり、標準的な値）:
  1=100, 2=300, 3=500, 4=1000、いずれも `× level` で加算
- **ソフトドロップ**: 1セルにつき +1
- **ハードドロップ**: 落下セル数 × 2 を加点
- **レベル**: `level = lines // 10 + 1`（10ライン毎に +1）
- **落下速度**: `fall_interval = max(0.08, BASE_FALL - (level - 1) * STEP)`
  - 例: `BASE_FALL = 0.8`, `STEP = 0.07`（config で調整可能）

## 5. 描画レイアウト（800×600）

- セルサイズ `CELL = 26`px
- 盤面: 10×20 → 260×520px。左上を `(BOARD_X, BOARD_Y) = (210, 40)` に配置
  （盤面は x:210〜470）
- 枠線を盤面の周囲に描画（既存メニューの枠と同系統の色）
- 右側サイドパネル（x ≈ 510〜）:
  - NEXT（次ピースのミニ描画）
  - SCORE / LEVEL / LINES のテキスト HUD
- ゲームオーバー時: 盤面中央に「GAME OVER」、下に
  「R: RESTART   ESC: MENU」を点滅表示（既存 GameOverScene の文言トーンに合わせる）

## 6. config.py への追加（例）

```python
# テトリス設定
TETRIS_COLS = 10
TETRIS_ROWS = 20
TETRIS_CELL = 26
TETRIS_BASE_FALL = 0.8     # レベル1の落下間隔（秒）
TETRIS_FALL_STEP = 0.07    # レベルごとの短縮量
TETRIS_MIN_FALL = 0.08
# テトリミノ色（7種）
COLOR_T_CYAN   = (0, 220, 230)   # I
COLOR_T_YELLOW = (240, 220, 0)   # O
COLOR_T_PURPLE = (170, 70, 220)  # T
COLOR_T_GREEN  = (0, 210, 80)    # S
COLOR_T_RED    = (230, 60, 60)   # Z
COLOR_T_BLUE   = (50, 90, 230)   # J
COLOR_T_ORANGE = (240, 150, 30)  # L
```

## 7. 影響範囲

- 既存ゲーム（ドンキーコング）には影響なし。シーンを追加するだけ。
- `menu_scene.py` の `GAMES` 配列に1要素追加（PAC-MAN / SPACE INVADERS の手前に TETRIS）。
- `main.py` に import 1行 ＋ register 1行。
- `config.py` は追記のみ（既存定数は変更しない）。

## 8. テスト方針

ヘッドレス（`pygame.display` を使わない）で `Board` / `Tetromino` を直接検証する
スモークテストを `作業メモ` 配下か一時スクリプトで実行する:

1. 各ピースが7種とも生成・回転できる（`cells()` が4セル返す）
2. 左右・床・既存ブロックで `is_valid` が正しく False を返す
3. 1行を埋めると `clear_lines()` が 1 を返し、上のブロックが下がる
4. 出現位置を塞いだ状態で次ピース生成 → ゲームオーバー判定になる

描画・実操作の最終確認はユーザーが実機で行う。

## 9. 未決事項 / 設計判断メモ

- ランダム抽選は単純な `random.choice`（7-bag は採用しない＝スコープ簡素化のため）。
- `known-issues.md` 反映候補: 7-bag 未採用・SRS 壁蹴り簡易版である点は、
  気になるようなら後日 known-issues に記録する。
