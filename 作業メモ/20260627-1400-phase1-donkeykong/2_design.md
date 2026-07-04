# Phase 1: 実装設計

## ディレクトリ構成

```
src/
├── main.py                    # ゲーム初期化・メインループ
├── config.py                  # 定数・設定値
├── scenes/
│   ├── __init__.py
│   ├── base_scene.py         # シーンの基本クラス
│   ├── menu_scene.py         # メニューシーン
│   ├── donkey_kong_scene.py  # ドンキーコングゲームシーン
│   ├── game_over_scene.py    # ゲームオーバー画面
│   └── clear_scene.py        # クリア画面
├── game_objects/
│   ├── __init__.py
│   ├── player.py             # プレイヤーキャラクター
│   ├── enemy.py              # 敵（樽）
│   ├── tile_map.py           # タイルマップ読み込み・描画
│   └── collision.py          # 衝突判定
├── scene_manager.py          # シーン管理・切り替え
├── assets/
│   ├── maps/                 # Tiled マップファイル (.tmx)
│   │   └── donkey_kong_1.tmx
│   ├── tilesets/             # タイルセット画像
│   └── sprites/              # スプライト画像（将来用）
└── utils/
    ├── __init__.py
    └── input_handler.py      # キー入力処理
```

## アーキテクチャ概要

### 1. ゲームループ構造

```
main.py
  ├─ GameManager 初期化
  │  ├─ pygame 初期化
  │  ├─ SceneManager 作成
  │  └─ 800×600 ウィンドウ生成
  │
  └─ メインループ（無限）
     ├─ イベント処理（キー入力・ウィンドウ閉じる）
     ├─ 現在シーン.update()
     ├─ 現在シーン.draw()
     ├─ ディスプレイ更新
     └─ フレームレート制御（60 FPS）
```

### 2. シーン管理

**BaseScene** - 全シーンの基本クラス
- `update(dt)` - フレーム更新
- `draw(screen)` - 描画
- `handle_input(event)` - イベント処理
- `on_enter()` - シーン開始時
- `on_exit()` - シーン終了時

**SceneManager** - シーン遷移管理
- 現在のシーンを保持・更新
- `change_scene(scene_name, **kwargs)` でシーン切り替え
- メニュー ↔ ゲーム ↔ クリア/ゲームオーバー の遷移

### 3. ゲームシーンの実装アプローチ

**DonkeyKongScene** の流れ：
1. `on_enter()` - マップ読み込み、プレイヤー・敵初期化
2. `update(dt)` - 毎フレーム実行
   - プレイヤー更新（位置・ジャンプ状態）
   - 敵更新（移動・生成判定）
   - 衝突判定チェック
   - ゴール判定チェック
3. `draw(screen)` - マップ・プレイヤー・敵を描画
4. クリア or ゲームオーバー → シーン切り替え

### 4. ゲームオブジェクト設計

**Player クラス**
- 属性: x, y, 幅, 高さ、速度、jumping フラグ、ジャンプ速度
- メソッド: 
  - `move_left()` / `move_right()` / `stop()` - 移動制御
  - `jump()` - ジャンプ開始
  - `update(dt)` - 重力適用・位置更新
  - `get_rect()` - 当たり判定矩形

**Enemy（樽）クラス**
- 属性: x, y, 幅, 高さ、速度、方向
- メソッド:
  - `update(dt)` - 移動（左右を往復）
  - `get_rect()` - 当たり判定矩形

**TileMap クラス**
- pytmx でマップ読み込み
- レイヤー管理（背景・衝突オブジェクト）
- `draw(screen)` で Tiled マップ描画
- 衝突判定用タイル情報の提供

**Collision モジュール**
- `check_tile_collision(rect, tilemap)` - タイルとの衝突判定
- `check_rect_collision(rect1, rect2)` - 矩形同士の衝突判定

### 5. Tiled マップ設計

**donkey_kong_1.tmx** の構成：
- **レイヤー 1: 背景タイル** - はしご・足場を視覚的に配置
- **レイヤー 2: 衝突判定タイル** - 踏めるタイルのみ（見えない用）
- **オブジェクトレイヤー: スポーン地点**
  - プレイヤースポーン (x, y 座標)
  - ゴール地点 (x, y, 幅, 高さ)

マップサイズ: 800×600 ピクセルの範囲内

### 6. 入力処理

**InputHandler** モジュール
- キー入力状態を管理（押下・離上）
- 各フレームで `update()` を呼び出し
- `is_key_pressed('left')` / `is_key_pressed('right')` / `is_key_pressed('jump')` など

イベント処理は `main.py` で、`handle_input()` 経由でシーンに通知

### 7. 状態管理・通信

**グローバル状態** (config.py)
- 画面サイズ (800, 600)
- フレームレート (60 FPS)
- 重力加速度
- 移動速度・ジャンプ速度

**シーン間データ受け渡し**
- `SceneManager.change_scene('clear', score=1000)` の形式で引数渡し
- シーン作成時に kwargs で初期化

## 実装の優先順位

1. **セットアップ** - 環境構築・基本骨組み
   - main.py / config.py / SceneManager
   
2. **シーン基本** - BaseScene + MenuScene
   - メニュー表示・選択機能が動作することを確認

3. **ゲームシーン基本** - プレイヤー移動まで
   - Player クラス + DonkeyKongScene で左右移動・ジャンプを実装
   
4. **マップ・敵** - Tiled マップ読み込み + Enemy
   - TileMap 表示 + 敵生成・移動
   
5. **衝突判定** - 完成度向上
   - Collision モジュール + 終了画面
   
6. **デバッグ・調整** - 細かい制御感の調整

## 変更するファイル

- 新規作成: `src/` 以下全ファイル（初期実装）
- 新規作成: `assets/` 以下全ファイル

## 影響範囲

**このフェーズの完成条件**
- ゲーム起動 → メニュー表示 → ドンキーコング起動 → プレイ → 終了画面 → メニュー戻却 の一連の流れが成立

**今後の拡張性**
- Phase 2: ステージ 2〜4 追加時も、既存の GameObject / Scene 基本構造を再利用可能
- Phase 3: 別ゲーム追加時も、同じ Scene / GameObject インターフェースで実装可能
