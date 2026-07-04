# ゲーム全体の定数・設定値

# 画面設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TITLE = "Retro Game Center"

# 物理
GRAVITY = 1200          # pixels/sec^2（落下加速度）
JUMP_POWER = 430        # pixels/sec（ジャンプ初速）

# プレイヤー（マリオ）設定
PLAYER_WIDTH = 26
PLAYER_HEIGHT = 32
PLAYER_SPEED = 135      # pixels/sec（左右移動）
CLIMB_SPEED = 95        # pixels/sec（はしご昇降）
RESPAWN_INVINCIBLE = 1.5  # 復帰後の無敵時間（秒）

# 樽（バレル）設定
BARREL_RADIUS = 13
BARREL_SPEED = 105      # pixels/sec（鉄骨を転がる速度）
BARREL_LADDER_CHANCE = 0.35  # はしごを降りる確率
BARREL_SPAWN_INTERVAL = 2.2  # 生成間隔（秒）

# スコア・ライフ
START_LIVES = 3
JUMP_BONUS = 100        # 樽を飛び越えた時の得点
CLEAR_BONUS_START = 5000  # ボーナス（時間で減少、クリア時に加算）
CLEAR_BONUS_DRAIN = 100   # ボーナス減少量（毎秒）

# 色定義（RGB）
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (228, 0, 0)
COLOR_GREEN = (0, 220, 60)
COLOR_BLUE = (40, 90, 230)
COLOR_GRAY = (128, 128, 128)
COLOR_YELLOW = (255, 216, 0)
COLOR_GIRDER = (236, 70, 90)     # 鉄骨（赤ピンク）
COLOR_GIRDER_DARK = (150, 30, 50)
COLOR_LADDER = (90, 200, 230)    # はしご（水色）
COLOR_BARREL = (170, 100, 40)    # 樽（茶）
COLOR_BARREL_BAND = (90, 50, 15)
COLOR_DK = (120, 72, 40)         # ドンキーコング（茶）
COLOR_DK_FACE = (210, 170, 120)
COLOR_PAULINE = (240, 90, 160)   # ポーリン（ピンク）

# テトリス設定
TETRIS_COLS = 10
TETRIS_ROWS = 20
TETRIS_CELL = 26
TETRIS_BASE_FALL = 0.8     # レベル1の落下間隔（秒）
TETRIS_FALL_STEP = 0.07    # レベルごとの短縮量
TETRIS_MIN_FALL = 0.08     # 落下間隔の下限
TETRIS_BOARD_X = 210       # 盤面左上 X
TETRIS_BOARD_Y = 40        # 盤面左上 Y

# テトリミノ色（7種）
COLOR_T_CYAN   = (0, 220, 230)   # I
COLOR_T_YELLOW = (240, 220, 0)   # O
COLOR_T_PURPLE = (170, 70, 220)  # T
COLOR_T_GREEN  = (0, 210, 80)    # S
COLOR_T_RED    = (230, 60, 60)   # Z
COLOR_T_BLUE   = (50, 90, 230)   # J
COLOR_T_ORANGE = (240, 150, 30)  # L
COLOR_T_GRID   = (40, 40, 55)    # 盤面のグリッド線
COLOR_T_FRAME  = (120, 130, 170) # 盤面の枠

# パス
MAPS_DIR = "assets/maps"
TILESETS_DIR = "assets/tilesets"
SPRITES_DIR = "assets/sprites"

# ==========================================================================
# ドンキーコング '81（DK81）設定 — 本作専用。既存定数と衝突しないよう DK81_ 接頭辞
# ==========================================================================

# スコア・進行
DK81_START_LIVES = 3
DK81_JUMP_BONUS = 100          # 樽を飛び越えた時の得点
DK81_SMASH_BONUS = 500         # ハンマーで破壊した時の得点（Milestone B）
DK81_BONUS_START = 5000        # ボーナスタイマー初期値
DK81_BONUS_DRAIN = 100         # ボーナス減少量（毎秒）

# プレイヤー
DK81_PLAYER_WIDTH = 24
DK81_PLAYER_HEIGHT = 30
DK81_PLAYER_SPEED = 130        # pixels/sec（左右移動）
DK81_CLIMB_SPEED = 90          # pixels/sec（はしご昇降）
DK81_JUMP_POWER = 420          # pixels/sec（ジャンプ初速）
DK81_RESPAWN_INVINCIBLE = 1.5  # 復帰後の無敵時間（秒）
DK81_DEATH_TIME = 1.6          # やられ演出の時間（秒）
DK81_HAMMER_TIME = 9.0         # ハンマー効果時間（秒・Milestone B）

# 樽
DK81_BARREL_RADIUS = 12
DK81_BARREL_SPEED = 110        # pixels/sec（鉄骨を転がる速度）
DK81_BARREL_LADDER_CHANCE = 0.3   # はしごを降りる確率
DK81_BARREL_SPAWN_INTERVAL = 2.5  # 生成間隔（秒）

# 演出
DK81_INTRO_TIME = 1.6          # イントロ表示時間（秒・任意キーでスキップ可）

# 色（DK81 専用）
DK81_COLOR_OIL_DRUM = (40, 70, 190)       # オイルドラム（青）
DK81_COLOR_OIL_BAND = (120, 160, 240)
DK81_COLOR_FLAME = (255, 140, 30)         # 炎（オレンジ）
DK81_COLOR_FLAME_CORE = (255, 220, 80)    # 炎の芯（黄）
DK81_COLOR_SKIN = (245, 200, 150)         # 肌色
DK81_COLOR_HAMMER = (200, 160, 60)        # ハンマー（Milestone B）
