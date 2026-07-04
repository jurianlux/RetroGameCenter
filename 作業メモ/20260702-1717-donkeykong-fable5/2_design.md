# 実装設計: ドンキーコング '81（Fable 5 制作）

> このファイルは**新しいセッション**が単独で実装を再開できるよう、
> 承認済みの進め方・技術前提・ファイル構成・挙動仕様・キックオフ手順を自己完結でまとめる。
> 要件は [1_requirements.md](1_requirements.md) を参照。
>
> **状態: 承認済み（2026-07-02・確認点は推奨案で確定）→ 次セッションで Milestone A の実装へ。**

---

## 0. 進め方（承認済み）

- **本セッションでは実装しない**。実装は次のセッションで依頼する。
- 本体実装は **Fable 5 サブエージェントに一括委譲**する（Agent tool, `model: "fable"`）。
  承認済みの本設計を丸ごと渡し、**原則 1 発**で実装させる（小刻みな spawn はコンテキスト再読込で高コストなため避ける）。
- **Opus（オーケストレータ）は最小関与**：仕様提示・最終検証・報告のみ。プレミアム枠を温存する。
- **2 段マイルストーン**（A→B）。枠が尽きても A で“遊べる物”が残る。
- **A 完了後にユーザーが使用量メーターを実測** → B に進むか判断。

---

## 1. 技術前提（確認済み環境）

| 項目 | 値 |
|------|----|
| Python | 3.13.14 |
| Pygame | 2.6.1（利用可） |
| numpy | **未インストール（使わない）** |
| 画面 | 800×600 / 60FPS（既存踏襲） |
| 実行 | `python src/main.py` |

- サウンドは **標準ライブラリ（`array`/`struct`）でメモリ上に波形合成** → `pygame.mixer.Sound(buffer=...)`。
  **新規依存なし**（ARCH-004「追加ライブラリ不要」を維持）。
- `pygame.mixer.get_init()` が `None`（未初期化・dummy 環境）なら**全サウンドは no-op**。クラッシュ禁止。
- BGM は**著作権に配慮**し、原曲の写しではなく**レトロ風のオリジナル・モチーフ**を合成する。

---

## 2. 既存を壊さない方針（最重要）

- **新規ファイル中心**。既存の共有ファイルは**追記のみ**：
  - `src/config.py`：`DK81_*` 定数ブロックを追記
  - `src/scenes/menu_scene.py`：`GAMES` に 1 エントリ追加
  - `src/main.py`：新シーンを import + `register_scene`
- **既存 `game_objects/level.py` / `player.py` / `barrel.py` は変更しない**（既存 `donkey_kong` が壊れないこと）。
- 既存 `game_objects/collision.py` の `check_rect_collision` は**読み取り再利用**（変更しない）。
- 名前衝突を避けるため本作専用コードは **`game_objects/dk81/` サブパッケージ**に隔離する。

---

## 3. ファイル構成

### 新規
```
src/scenes/donkey_kong_81_scene.py     # DonkeyKong81Scene（本体・状態機械・描画・HUD・演出）
src/game_objects/dk81/__init__.py
src/game_objects/dk81/stage.py         # 地形（鉄骨/はしご/壊れはしご/オイルドラム/ハンマー位置）+ クエリ関数
src/game_objects/dk81/player.py        # DK81Player（移動/はしご/ジャンプ/ハンマー状態/ドット絵描画）
src/game_objects/dk81/barrel.py        # DK81Barrel（転がり/はしご降下/落下/ドラム誘導/描画）
src/game_objects/dk81/fireball.py      # Fireball（発生/徘徊・追跡/描画）      ← Milestone B
src/game_objects/dk81/hammer.py        # Hammer（設置/取得/スイング/破壊判定）  ← Milestone B
src/utils/synth_audio.py               # SoundBank（合成SE）+ 簡易BGMシーケンサ + 無音フォールバック
```

### 変更（追記のみ）
```
src/config.py            # DK81_* 定数
src/scenes/menu_scene.py # GAMES に ("DONKEY KONG '81", "donkey_kong_81")
src/main.py              # import + register_scene("donkey_kong_81", DonkeyKong81Scene())
```

---

## 4. 統合コントラクト（実装時に必ず守る）

- シーンは `scenes/base_scene.py` の `BaseScene` を継承し、`on_enter/handle_input/update/draw` を実装。
- 遷移は `self.request_scene(name, **kwargs)` で `self.next_scene` にセット。`GameManager` が毎フレーム処理（[main.py:54-59](../../src/main.py#L54-L59)）。
- **ゲームオーバー**：`self.request_scene("game_over", score=self.score)`
- **クリア**：残ボーナスを加算後 `self.request_scene("clear", score=self.score)`
  - `game_over` / `clear` シーンは `kwargs["score"]` を読み、Enter/Space でメニューへ戻る（既存実装済み）。
- **ESC → メニュー**は `GameManager.handle_events` が全シーン共通で処理（[main.py:40-42](../../src/main.py#L40-L42)）。シーン側で ESC を握らない。
- 入力は既存シーンに合わせ **`pygame.key.get_pressed()`（連続）＋ `KEYDOWN`（単発：ジャンプ等）** を直接使う
  （`utils/input_handler.py` は既存では未使用のため踏襲しない）。

---

## 5. ステージ設計（`dk81/stage.py`）

既存 [level.py](../../src/game_objects/level.py) の**実証済みパターンを踏襲**しつつ、本作専用に自己完結で定義する。

- **鉄骨（girder）**: `(x_left, x_right, y_left, y_right)` の斜め線分。上下交互に傾け、樽が端で落ちて逆向きに転がる＝ジグザグ。7 段構成（最下段=プレイヤー開始、最上段左に DK、最上部にポーリンの水平足場）。
- **はしご（ladder）**: `(x, lower_index, upper_index)`。加えて**壊れはしご**は「途中までしか無い＝渡れない」ものとして表現（例：`broken` フラグ or 別リスト。プレイヤー・樽ともに上り下りの接続に使えない）。
- **オイルドラム**: 最下段左に矩形＋炎。`OIL_DRUM_RECT` を公開（当たり/発火判定に使用）。
- **ハンマー位置**: 鉄骨上に 1〜2 個（`HAMMER_SPAWNS = [(x, girder_index), ...]`）。
- クエリ関数（既存名に合わせる）: `surface_y(gi, x)`, `girder_range(gi)`, `downhill_dir(gi)`, `ladder_top_y/bottom_y(l)`, `find_landing_girder(cx, prev_b, new_b)`, `draw(screen)`。
- 座標の具体値は Fable 5 が決めてよい（見た目のバランス優先）。ポーリン到達＝クリア判定の矩形も stage 側で提供すると綺麗。

---

## 6. 挙動仕様（本家準拠）

### プレイヤー（`DK81Player`）
- 状態 `ground / air / climb`（既存 Player を参考）。左右移動・斜面スナップ・はしご昇降・ジャンプ（スペースのエッジ）。
- **ハンマー状態**（B）：取得中は `hammering=True`。**ジャンプ・はしご昇降を禁止**、左右移動のみ可。ハンマーが上下にスイングし、下（叩き）フェーズで前方の樽/炎に当たれば破壊。制限時間（例 8〜10 秒）で解除。
- **描画**：ドット絵風（赤帽子・青オーバーオール・歩行アニメ・向き反転）。B でさらに作り込み。
- **やられ**：`dying` で回転落下アニメ（既存は非表示のみ→本作はアニメ）。

### 樽（`DK81Barrel`）
- `roll / fall / ladder`（既存 Barrel を参考）。斜面を下り方向へ転がり、端で落下→下段で逆向き。
- **はしご降下**：交差時に確率（`DK81_BARREL_LADDER_CHANCE`）で降りる。壊れはしごは使わない。
- **ドラム誘導**（B）：最下段付近でオイルドラム方向へ寄る挙動を確率で付与。
- **発火**（B）：オイルドラムに到達した樽は確率で消滅し **Fireball を 1 体生成**。
- 画面下に出たら消滅。

### ファイアボール（`Fireball`, B）
- オイルドラム/樽から発生。鉄骨を移動・はしごを上下し、**プレイヤーの段・x に寄る**バイアスで追跡（完全追尾ではなく揺らぎを持たせる）。
- 接触でミス。ハンマーの叩きで破壊可（加点）。

### ハンマー（`Hammer`, B）
- `HAMMER_SPAWNS` に設置。接触で取得（`player.grab_hammer()`）。取得中はプレイヤー頭上でスイング描画。
- 叩きフェーズ×対象矩形の重なりで樽/炎を破壊し加点。時間切れで消滅（消えた後は再取得不可 or リポップしない＝本家準拠）。

### スコア・進行
- 樽/炎を**飛び越え** `+100`（`DK81_JUMP_BONUS`。既存同様、空中かつ対象が足元通過で 1 回だけ）。
- ハンマー破壊：**固定 `+500`**（`DK81_SMASH_BONUS`）。
- **ボーナスタイマー**：`DK81_BONUS_START`（例 5000）から毎秒 `DK81_BONUS_DRAIN` 減少。0 下限。クリア時に残りを加算。
- **ライフ**：`DK81_START_LIVES`（例 3）。0 で `game_over`。
- **ハイスコア**：HUD に表示（A は実行中のみ保持で可）。**JSON 永続化は B の任意**（`scores.json` 等。失敗しても無視して続行）。

---

## 7. サウンド設計（`utils/synth_audio.py`）

- 初期化時に `pygame.mixer.get_init()` を確認：
  - `None` → **無音モード**（`play_se/play_bgm/stop_bgm` 全て no-op）。
  - 取れれば `(freq, size, channels)` に合わせて **16bit 署名付き**サンプルを `array('h', ...)` で生成し、
    チャンネル数分インターリーブして `pygame.mixer.Sound(buffer=samples.tobytes())` を作る。
- **SE（A で最低限）**: `jump`, `score`（+100）, `death`, `clear`。
  **B で追加**: `walk/step`, `get_hammer`, `smash`（破壊）, `stage_start`。
  → 方形波/三角波 + 短いエンベロープ（アタック/ディケイ）で「ピコ」音を合成。
- **BGM（B）**: 簡易ノートシーケンサ（`update(dt)` で経過に応じ次の音を鳴らす）。
  トラック例：`intro`（イントロ演出中）, `hammer`（ハンマー取得中のアップテンポ）。**オリジナル・モチーフ**。
- 例外は握りつぶして**絶対にゲームを落とさない**（合成失敗時も無音で続行）。

---

## 8. シーン状態機械（`DonkeyKong81Scene`）

```
intro ──(演出終了 or キーでスキップ)──▶ play
play  ──被弾──▶ dying ──(タイマー)──▶ play(復帰)  |  request_scene("game_over", score)
play  ──ポーリン到達──▶ clearing ──(演出)──▶ request_scene("clear", score)  # 残ボーナス加算後
```

- `on_enter`：フォント/サウンド初期化、`lives/score/bonus` 初期化、ステージ・プレイヤー・樽リセット、`state="intro"`。
- **イントロ（B）**：DK がポーリンを抱えて登り、踏みつけで鉄骨が水平→斜めに“曲がる”アニメ、`HOW HIGH CAN YOU GET?` → `25 M`。~3〜4 秒、任意キーでスキップ可。A では省略して即 `play` で可。
- **クリア（B）**：ハート出現→DK 転落の簡易演出（~2 秒）→ clear シーンへ。A では即遷移で可。
- HUD：`SCORE / HIGH / BONUS / m 表示 / 残機アイコン / 操作ヒント`（既存 HUD を参考）。

---

## 9. マイルストーン内訳（タスク＝受け入れ対応）

### A（必達・1 枠で狙う）
- [x] `config.py` に `DK81_*` 追記
- [x] `dk81/stage.py`（鉄骨/はしご/クエリ/描画。壊れはしご・ドラム矩形・ハンマー位置は定義だけでも可）
- [x] `dk81/player.py`（移動/はしご/ジャンプ/ドット絵描画/やられアニメ）
- [x] `dk81/barrel.py`（転がり/はしご/落下/描画）
- [x] `synth_audio.py`（SE: jump/score/death/clear + 無音フォールバック）
- [x] `donkey_kong_81_scene.py`（play/dying、衝突、+100、ボーナス、ライフ、HUD、ポーリン到達→clear、被弾→game_over。intro/clear は簡易でも可）
- [x] `menu_scene.py` / `main.py` 統合
- [x] ヘッドレススモークテスト + 既存 `donkey_kong`/`tetris` 非回帰確認
- → 受け入れ条件の該当項目（移動・はしご・ジャンプ・樽・+100・ボーナス・ミス→復帰→GO・クリア→clear・基本音・ESC・起動）を満たす

### B（見せ場・枠が残れば）
- [ ] `dk81/fireball.py`（発生/追跡/破壊）＋ オイルドラム発火連動
- [ ] `dk81/hammer.py`（取得/スイング/破壊/制約）＋ ハンマー中 BGM
- [ ] イントロ演出（鉄骨が曲がる → HOW HIGH → 25M、スキップ可）
- [ ] クリア演出（ハート → DK 転落）
- [ ] BGM 拡充・SE 追加（walk/get_hammer/smash/stage_start）
- [ ] ドット絵の作り込み（DK/ポーリン/樽バンド/鉄骨リベット）
- [ ] ハイスコア JSON 永続化（任意）
- [ ] known-issues.md へ残課題を追記

---

## 10. テスト方針（ヘッドレス）

- 環境変数で GUI/音声を無効化してから `import pygame`：
  `os.environ["SDL_VIDEODRIVER"]="dummy"`, `os.environ["SDL_AUDIODRIVER"]="dummy"`。
- `DonkeyKong81Scene` を生成し `on_enter` → 疑似フレームで検証：
  - `intro`→`play` 遷移（or A の即 play）
  - 樽が生成・移動する／プレイヤーがはしごで上段へ到達できる
  - 衝突で `dying`→復帰、ライフ 0 で `game_over` 要求（`next_scene`）
  - 最上段ポーリン到達で `clear` 要求、`score` が渡る
  - `synth_audio` が dummy 音声下で no-op（例外なし）
- **既存非回帰**：`menu/donkey_kong/tetris/game_over/clear` を import & 生成してエラーが出ないこと。
- キー入力は `pygame.key.get_pressed` を monkeypatch するか、`KEYDOWN` イベントを流して再現。

---

## 11. 影響範囲・リスク

- **影響ファイル**：新規（scenes 1・dk81 パッケージ・synth_audio）＋ 追記 3（config/menu/main）。既存ゲームのロジックには触れない。
- **リスク**：
  - 音声バッファ形式が mixer 初期化と不一致 → `get_init()` を必ず参照し、不一致/未初期化は無音化。
  - **fireball の追跡 AI・hammer** が反復デバッグを食いやすい → だから B に分離。A の完成を最優先。
  - dummy ドライバでの mixer 挙動差 → no-op 経路を必ず用意。
- **既存差異メモ**：ARCH-002（Tiled）に対し本作もデータ定義方式（既存 known-issues No.1 と同方針）。B 完了時に known-issues へ 1 行追記。

---

## 12. 新セッションでのキックオフ手順

1. CLAUDE.md セッション開始手順を実施（`README.md` / `設計/concept.md` / `設計/architecture.md` / 本作業メモ 2 ファイルを読む）。
2. 環境確認（`python -c "import pygame"` OK・numpy 無しを再確認）。
3. **Milestone A** を **Fable 5 サブエージェント 1 発**で実装（Agent tool `model:"fable"`、本設計＋要件を丸ごと指示。`run_in_background` は任意）。
   - オーケストレータ（Opus）は仕様提示と検証のみ。実装コードは Fable 5 に書かせる。
4. A 完了後：ヘッドレススモークテスト実行＋既存ゲーム非回帰確認 → 結果を報告。
5. ユーザーが**使用量メーターを実測** → B に進むか判断。
6. 作業完了時（CLAUDE.md ルール）：タスクを `- [x]` 化、`設計/` 反映事項があれば承認を得て更新、`known-issues.md` 追記、型/実行確認の結果を報告。
