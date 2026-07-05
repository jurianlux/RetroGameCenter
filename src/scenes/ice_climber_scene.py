"""アイスクライマー — 氷の山 1 ステージ（山頂ボーナス付き）。

ポポを操作して氷ブロックをハンマー（頭突き）で割りながら上へ登り、最上段を越えて
山頂ボーナスへ。制限時間内にコンドルへ飛び移るとステージクリア＋大量ボーナス。

状態機械:
  intro → play → (dying → play 復帰 | game_over)
                → (最上段到達で summit へ)
  summit → (コンドル掴む or 時間切れ) → clear

座標はワールド（y は下ほど大きい）。cam_y で画面へ落とす。
プレイヤーが上へ進むほど cam_y が小さく（負に）なり、山が下へ流れる。
"""

import math
import random

import pygame

from scenes.base_scene import BaseScene
from game_objects.ice.stage import Stage, floor_top_world
import game_objects.ice.stage as stage_mod
from game_objects.ice.player import Popo
from game_objects.ice.enemy import Topi, Icicle
from game_objects.collision import check_rect_collision
from utils.synth_audio import SoundBank
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE, COLOR_YELLOW,
    COLOR_GRAY, COLOR_RED,
    ICE_CELL, ICE_COLS, ICE_FLOORS, ICE_FLOOR_GAP,
    ICE_START_LIVES, ICE_RESPAWN_INVINCIBLE, ICE_DEATH_TIME,
    ICE_ICE_BREAK_SCORE, ICE_TOPI_SCORE, ICE_CONDOR_BONUS,
    ICE_TOPI_SPEED, ICE_TOPI_SPAWN_INTERVAL, ICE_TOPI_MAX,
    ICE_ICICLE_SPAWN_INTERVAL, ICE_SUMMIT_TIME,
    ICE_COLOR_SKY_TOP, ICE_COLOR_SKY_BOT, ICE_COLOR_SUMMIT_SKY,
    ICE_COLOR_POPO, ICE_COLOR_POPO_FACE, ICE_COLOR_CONDOR, ICE_COLOR_CLOUD,
    ICE_COLOR_ICICLE, ICE_COLOR_POPO_TRIM,
)

WORLD_RIGHT = ICE_COLS * ICE_CELL
# プレイヤーがこの割合より画面上に来たらカメラを追従させる
CAM_ANCHOR = 0.42
# 落下ミス判定：カメラ下端からこれ以上下に落ちたら
FALL_MARGIN = 90


class IceClimberScene(BaseScene):
    HIGH_SCORE = 0  # 実行中のみ保持（DK81 と同方針）

    # --- ライフサイクル ----------------------------------------------
    def on_enter(self):
        super().on_enter()
        self.font = pygame.font.Font(None, 30)
        self.font_hint = pygame.font.Font(None, 22)
        self.big_font = pygame.font.Font(None, 68)
        self.mid_font = pygame.font.Font(None, 40)
        self.sound = SoundBank()

        self.lives = ICE_START_LIVES
        self.score = 0
        self.highest_floor = 0
        self.anim = 0.0
        self.state = "intro"
        self.intro_timer = 1.7

        self.stage = Stage(seed=random.randint(0, 99999))
        self._reset_round(full=True)
        self.state = "intro"

    def _reset_round(self, full=False):
        """ポポを（復帰時は到達済みの安全な段に）配置。"""
        start_floor = 0 if full else self._respawn_floor()
        cx = SCREEN_WIDTH // 2
        # 開始列が穴なら埋まっている列へ寄せる
        col = self.stage.col_at(cx)
        if not self.stage.is_filled(start_floor, col):
            for c in range(ICE_COLS):
                if self.stage.is_filled(start_floor, c):
                    cx = c * ICE_CELL + ICE_CELL // 2
                    break
        self.player = Popo(self.stage, cx, start_floor)
        self.cam_y = self._target_cam()
        if full:
            self.topis = []
            self.icicles = []
            self.topi_timer = 0.0
            self.icicle_timer = 0.0
        self.invincible = 0.0 if full else ICE_RESPAWN_INVINCIBLE
        self.death_timer = 0.0
        self.state = "play"

    def _respawn_floor(self):
        """ミス後は到達した高さより少し下の安全段へ戻す。"""
        return max(0, min(self.highest_floor, ICE_FLOORS - 1))

    # --- 入力 ---------------------------------------------------------
    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.state == "intro":
            self.state = "play"
            return
        if self.state in ("play", "summit") and event.key == pygame.K_SPACE:
            if self.player.jump():
                self.sound.play_se("jump")

    # --- 更新 ---------------------------------------------------------
    def update(self, dt):
        self.anim += dt

        if self.state == "intro":
            self.intro_timer -= dt
            if self.intro_timer <= 0:
                self.state = "play"
            return

        if self.state == "dying":
            self.player.update_dying(dt)
            self.death_timer -= dt
            if self.death_timer <= 0:
                if self.lives <= 0:
                    self._update_high()
                    self.request_scene("game_over", score=self.score)
                else:
                    self._reset_round(full=False)
            return

        if self.state == "clear":
            return

        keys = pygame.key.get_pressed()

        if self.state == "play":
            self._update_play(dt, keys)
        elif self.state == "summit":
            self._update_summit(dt, keys)

    def _update_play(self, dt, keys):
        events = self.player.update(dt, keys)
        for (f, c) in events:
            self.score += ICE_ICE_BREAK_SCORE
            self.sound.play_se("icebreak")

        if self.invincible > 0:
            self.invincible -= dt

        # 到達高度の更新（登った段が上がったら得点）
        if self.player.state == "ground" and self.player.on_floor > self.highest_floor:
            gained = self.player.on_floor - self.highest_floor
            self.highest_floor = self.player.on_floor
            self.score += gained * 50
            self.sound.play_se("score")

        self._update_camera(dt)
        self._spawn_enemies(dt)
        self._update_enemies(dt)
        self._check_stomp_and_hit()
        self._check_fall_death()
        self._check_reach_summit()
        self._update_high()

    def _update_summit(self, dt, keys):
        # 山頂：ポポは雲足場の上を移動・ジャンプできる。コンドルが横に飛ぶ。
        self.player.update(dt, keys)
        # 山頂では雲だけが足場（stage の氷は最上段のみ）。雲への着地を補う。
        self._summit_land()
        self._update_camera(dt, summit=True)

        self.summit_timer -= dt
        self.condor_x += self.condor_dir * 90 * dt
        if self.condor_x < 120:
            self.condor_x = 120
            self.condor_dir = 1
        elif self.condor_x > WORLD_RIGHT - 120:
            self.condor_x = WORLD_RIGHT - 120
            self.condor_dir = -1

        # コンドルとの接触でクリア（ボーナス付き）
        cr = pygame.Rect(int(self.condor_x - 26), int(self.condor_world_y - 14), 52, 28)
        if check_rect_collision(self.player.get_world_rect(), cr):
            self.score += ICE_CONDOR_BONUS
            self._finish_clear(caught=True)
            return

        # 時間切れ：ボーナスなしでクリア
        if self.summit_timer <= 0:
            self._finish_clear(caught=False)
            return

        # 山頂から落ちたらミス（残機を消費して山頂やり直し）
        if self.player.bottom - self.cam_y > SCREEN_HEIGHT + FALL_MARGIN:
            self._player_miss(from_summit=True)

    def _finish_clear(self, caught):
        self._update_high()
        self.sound.play_se("clear")
        self.state = "clear"
        msg = "YOU CAUGHT THE CONDOR!" if caught else "YOU REACHED THE SUMMIT!"
        self.request_scene("clear", score=self.score, title="CONGRATULATIONS!",
                           message=msg)

    # --- カメラ -------------------------------------------------------
    def _target_cam(self):
        # プレイヤーを画面の CAM_ANCHOR の高さに置く
        return self.player.bottom - SCREEN_HEIGHT * CAM_ANCHOR

    def _update_camera(self, dt, summit=False):
        target = self._target_cam()
        if not summit:
            # 下限：最下段が見え切る位置より下へは行かない（山の裾を見せる）
            floor0 = floor_top_world(0)
            max_cam = floor0 + ICE_CELL * 2 - SCREEN_HEIGHT + 40
            target = min(target, max_cam)
        # なめらかに追従
        self.cam_y += (target - self.cam_y) * min(1.0, dt * 8)

    # --- 敵の生成・更新 ----------------------------------------------
    def _spawn_enemies(self, dt):
        # トッピー：到達段の少し上の床から出す
        self.topi_timer += dt
        if self.topi_timer >= ICE_TOPI_SPAWN_INTERVAL and len(self.topis) < ICE_TOPI_MAX:
            self.topi_timer = 0.0
            self._spawn_topi()

        # つらら：画面内の床の下面から落とす
        self.icicle_timer += dt
        if self.icicle_timer >= ICE_ICICLE_SPAWN_INTERVAL:
            self.icicle_timer = 0.0
            self._spawn_icicle()

    def _spawn_topi(self):
        # プレイヤーが今いる段〜2 段上のどこかに、埋まっている列で出す
        base = self.player.on_floor
        candidates = [f for f in range(base, min(ICE_FLOORS, base + 3)) if f >= 1]
        if not candidates:
            return
        floor = random.choice(candidates)
        # 端の埋まった列から出す
        left_ok = self.stage.is_filled(floor, 1)
        right_ok = self.stage.is_filled(floor, ICE_COLS - 2)
        if left_ok and (not right_ok or random.random() < 0.5):
            self.topis.append(Topi(self.stage, floor, 1, 1))
        elif right_ok:
            self.topis.append(Topi(self.stage, floor, ICE_COLS - 2, -1))

    def _spawn_icicle(self):
        # 画面に見えている床のうち、プレイヤー前後の列で落とす
        top_visible = self.cam_y
        bot_visible = self.cam_y + SCREEN_HEIGHT
        floors = []
        for f in range(ICE_FLOORS):
            fy = floor_top_world(f)
            if top_visible - ICE_CELL <= fy <= bot_visible:
                floors.append(f)
        if not floors:
            return
        floor = random.choice(floors)
        col = random.randint(1, ICE_COLS - 2)
        # 落とすのは埋まっている床の下面から（穴からは落ちない）
        if not self.stage.is_filled(floor, col):
            return
        world_x = col * ICE_CELL + ICE_CELL // 2
        under_y = floor_top_world(floor) + ICE_CELL  # 床の下面
        self.icicles.append(Icicle(world_x, under_y))

    def _update_enemies(self, dt):
        for t in self.topis:
            t.update(dt)
        self.topis = [t for t in self.topis if t.alive]

        for ic in self.icicles:
            ic.update(dt, self.cam_y)
        self.icicles = [ic for ic in self.icicles if ic.alive]

    # --- 衝突 ---------------------------------------------------------
    def _check_stomp_and_hit(self):
        if self.state != "play":
            return
        pr = self.player.get_world_rect()

        # トッピー：上から踏めば撃破、それ以外の接触はミス
        for t in self.topis:
            if t.dying:
                continue
            tr = t.get_world_rect()
            if not check_rect_collision(pr, tr):
                continue
            # 落下中で、足がトッピーの上半分に当たった → 踏みつけ
            stomp = self.player.vel_y > 0 and pr.bottom <= tr.centery + 8
            if stomp:
                t.stomp()
                self.score += ICE_TOPI_SCORE
                self.player.vel_y = -260  # 小さく跳ねる
                self.sound.play_se("stomp")
            elif self.invincible <= 0:
                self._player_miss()
                return

        # つらら：落下中のものに当たるとミス
        if self.invincible <= 0:
            for ic in self.icicles:
                if not ic.falling:
                    continue
                if check_rect_collision(pr, ic.get_world_rect()):
                    self._player_miss()
                    return

    def _check_fall_death(self):
        # 画面下端よりさらに下に落ちたらミス
        if self.player.bottom - self.cam_y > SCREEN_HEIGHT + FALL_MARGIN:
            self._player_miss()

    def _check_reach_summit(self):
        # 最上段（ICE_FLOORS-1）に着地したら山頂ボーナスへ
        if self.player.state == "ground" and self.player.on_floor >= ICE_FLOORS - 1:
            self._enter_summit()

    def _player_miss(self, from_summit=False):
        self.lives -= 1
        self.state = "dying"
        self.death_timer = ICE_DEATH_TIME
        self.player.start_dying()
        self.sound.play_se("death")
        self._from_summit = from_summit

    # --- 山頂ボーナス -------------------------------------------------
    def _enter_summit(self):
        self.state = "summit"
        self.summit_timer = ICE_SUMMIT_TIME
        # 雲の足場を、最上段の上に「1 ジャンプで届く」間隔で階段状に配置する。
        # ジャンプ到達高 ≒ 80px なので 1 段あたり ~64px 上へ。
        top_floor_y = floor_top_world(ICE_FLOORS - 1)
        self.clouds = [
            pygame.Rect(int(WORLD_RIGHT * 0.34) - 60, int(top_floor_y - 66), 120, 18),
            pygame.Rect(int(WORLD_RIGHT * 0.60) - 60, int(top_floor_y - 130), 120, 18),
            pygame.Rect(int(WORLD_RIGHT * 0.42) - 70, int(top_floor_y - 196), 140, 18),
        ]
        # 雲を stage の当たり判定に組み込むのは複雑なので、summit 中は
        # プレイヤーの着地判定を雲矩形で補助する（_summit_land）。
        # コンドルは最上の雲のさらに上を横切る。
        self.condor_x = WORLD_RIGHT * 0.5
        self.condor_dir = 1
        self.condor_world_y = top_floor_y - 260
        self.sound.play_se("levelup")

    # summit 中はプレイヤー更新後に雲への着地を補う
    def _summit_land(self):
        if self.player.vel_y <= 0:
            return
        pr = self.player.get_world_rect()
        for cl in self.clouds:
            if pr.centerx < cl.left or pr.centerx > cl.right:
                continue
            if pr.bottom >= cl.top and pr.bottom <= cl.top + 18 and self.player.vel_y > 0:
                self.player.bottom = cl.top
                self.player.vel_y = 0
                self.player.state = "ground"
                self.player.on_floor = ICE_FLOORS  # 便宜上

    # --- 描画 ---------------------------------------------------------
    def draw(self, screen):
        if self.state == "summit":
            self._draw_summit_bg(screen)
        else:
            self._draw_sky(screen)

        self.stage.draw(screen, self.cam_y)

        if self.state == "summit":
            self._draw_clouds(screen)
            self._draw_condor(screen)

        for t in self.topis if self.state != "summit" else []:
            t.draw(screen, self.cam_y)
        for ic in (self.icicles if self.state != "summit" else []):
            ic.draw(screen, self.cam_y)

        blink = self.invincible > 0 and int(self.invincible * 12) % 2 == 0
        self.player.draw(screen, self.cam_y, blink=blink)

        self._draw_hud(screen)
        self._draw_controls(screen)

        if self.state == "intro":
            self._draw_center(screen, "CLIMB TO THE TOP!", COLOR_YELLOW, self.big_font)
        elif self.state == "dying":
            self._draw_center(screen, "MISS!", COLOR_RED, self.big_font)
        elif self.state == "summit":
            self._draw_summit_hud(screen)

    def _draw_sky(self, screen):
        # 縦グラデーションの空。高度が上がるほど濃くなる演出も少し。
        top = ICE_COLOR_SKY_TOP
        bot = ICE_COLOR_SKY_BOT
        h = SCREEN_HEIGHT
        for y in range(0, h, 4):
            t = y / h
            col = (int(top[0] + (bot[0] - top[0]) * t),
                   int(top[1] + (bot[1] - top[1]) * t),
                   int(top[2] + (bot[2] - top[2]) * t))
            pygame.draw.rect(screen, col, (0, y, SCREEN_WIDTH, 4))

    def _draw_summit_bg(self, screen):
        screen.fill(ICE_COLOR_SUMMIT_SKY)
        # 星
        rng = random.Random(7)
        for _ in range(60):
            x = rng.randint(0, SCREEN_WIDTH)
            y = rng.randint(0, SCREEN_HEIGHT)
            b = rng.randint(120, 255)
            tw = (math.sin(self.anim * 2 + x) + 1) * 0.5
            c = int(b * (0.5 + 0.5 * tw))
            screen.set_at((x, y), (c, c, min(255, c + 30)))

    def _draw_clouds(self, screen):
        for cl in self.clouds:
            r = cl.copy()
            r.y -= int(self.cam_y)
            pygame.draw.ellipse(screen, ICE_COLOR_CLOUD, r)
            pygame.draw.ellipse(screen, ICE_COLOR_CLOUD,
                                (r.x + 20, r.y - 8, r.width - 40, r.height + 8))

    def _draw_condor(self, screen):
        x = int(self.condor_x)
        y = int(self.condor_world_y - self.cam_y)
        flap = math.sin(self.anim * 8) * 10
        # 体
        pygame.draw.ellipse(screen, ICE_COLOR_CONDOR, (x - 14, y - 8, 28, 16))
        # 翼（羽ばたき）
        pygame.draw.polygon(screen, ICE_COLOR_CONDOR,
                            [(x - 8, y), (x - 40, y - flap), (x - 12, y + 4)])
        pygame.draw.polygon(screen, ICE_COLOR_CONDOR,
                            [(x + 8, y), (x + 40, y - flap), (x + 12, y + 4)])
        # くちばし
        pygame.draw.polygon(screen, (230, 180, 60),
                            [(x + 12, y - 2), (x + 22, y), (x + 12, y + 3)])

    def _draw_hud(self, screen):
        score = self.font.render(f"SCORE  {self.score:06d}", True, COLOR_WHITE)
        screen.blit(score, (12, 10))
        high = self.font.render(f"HIGH  {IceClimberScene.HIGH_SCORE:06d}", True, COLOR_RED)
        screen.blit(high, (12, 34))
        # 高度（登った段）
        alt = self.font.render(f"{self.highest_floor*100} m", True, ICE_COLOR_ICICLE)
        screen.blit(alt, (SCREEN_WIDTH // 2 - alt.get_width() // 2, 10))
        # 残機（ポポの頭アイコン）
        for i in range(self.lives):
            ix = SCREEN_WIDTH - 26 - i * 24
            pygame.draw.rect(screen, ICE_COLOR_POPO_TRIM, (ix, 10, 16, 5))
            pygame.draw.rect(screen, ICE_COLOR_POPO, (ix, 14, 16, 8))
            pygame.draw.rect(screen, ICE_COLOR_POPO_FACE, (ix + 3, 16, 10, 5))

    def _draw_summit_hud(self, screen):
        t = max(0, int(self.summit_timer) + 1)
        col = COLOR_RED if self.summit_timer < 4 else COLOR_YELLOW
        txt = self.mid_font.render(f"BONUS  {t:02d}", True, col)
        screen.blit(txt, txt.get_rect(center=(SCREEN_WIDTH // 2, 70)))
        hint = self.font_hint.render("JUMP TO THE CONDOR!", True, COLOR_WHITE)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, 100)))

    def _draw_controls(self, screen):
        text = "ARROWS: MOVE     SPACE: JUMP (BREAK ICE)     ESC: MENU"
        surf = self.font_hint.render(text, True, COLOR_GRAY)
        screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 14)))

    def _draw_center(self, screen, text, color, font):
        surf = font.render(text, True, color)
        screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

    def _update_high(self):
        if self.score > IceClimberScene.HIGH_SCORE:
            IceClimberScene.HIGH_SCORE = self.score
