"""ドンキーコング '81 — 25m 樽ステージ（Milestone A）。

斜め鉄骨をはしごで登り、DK が投げる樽を避けて最上段のポーリンを目指す。
樽に当たるとミス（回転落下アニメ → 復帰 or ゲームオーバー）。
樽を飛び越えると +100。クリア時は残りボーナスを加算して clear シーンへ。

状態機械: intro → play → (dying → play 復帰 | game_over) / (ポーリン到達 → clear)
"""

import math

import pygame
from scenes.base_scene import BaseScene
from game_objects.dk81.player import DK81Player
from game_objects.dk81.barrel import DK81Barrel
from game_objects.collision import check_rect_collision
import game_objects.dk81.stage as stage
from utils.synth_audio import SoundBank
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE, COLOR_YELLOW,
    COLOR_GRAY, COLOR_DK, COLOR_DK_FACE, COLOR_PAULINE, COLOR_RED,
    DK81_COLOR_SKIN,
    DK81_START_LIVES, DK81_JUMP_BONUS, DK81_BONUS_START, DK81_BONUS_DRAIN,
    DK81_BARREL_SPAWN_INTERVAL, DK81_RESPAWN_INVINCIBLE, DK81_DEATH_TIME,
    DK81_INTRO_TIME,
)

COLOR_LIGHTBLUE = (110, 200, 255)  # 「25 m」表示用


class DonkeyKong81Scene(BaseScene):
    HIGH_SCORE = 0  # 実行中のみ保持（クラス変数・A の仕様）

    def on_enter(self):
        super().on_enter()
        self.font = pygame.font.Font(None, 30)
        self.font_hint = pygame.font.Font(None, 22)
        self.big_font = pygame.font.Font(None, 72)
        self.sound = SoundBank()

        self.lives = DK81_START_LIVES
        self.score = 0
        self.bonus = DK81_BONUS_START
        self._bonus_tick = 0.0
        self.dk_anim = 0.0
        self.state = "intro"   # intro / play / dying / clear
        self.intro_timer = DK81_INTRO_TIME
        self._reset_round(full=True)
        self.state = "intro"   # _reset_round が play にするので intro に戻す

    def _reset_round(self, full=False):
        """プレイヤー位置と樽をリセット（ミス後の復帰）。"""
        sx, sg = stage.PLAYER_START
        self.player = DK81Player(sx, sg)
        if full:
            self.barrels = []
            self.spawn_timer = 0.0
        self.invincible = DK81_RESPAWN_INVINCIBLE if not full else 0.0
        self.state = "play"
        self.death_timer = 0.0

    def _start_play(self):
        self.state = "play"

    # --- 入力 ---------------------------------------------------------
    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.state == "intro":
            self._start_play()   # 任意キーでスキップ
            return
        if self.state == "play" and event.key == pygame.K_SPACE:
            if self.player.jump():
                self.sound.play_se("jump")

    # --- 更新 ---------------------------------------------------------
    def update(self, dt):
        self.dk_anim += dt

        if self.state == "intro":
            self.intro_timer -= dt
            if self.intro_timer <= 0:
                self._start_play()
            return

        if self.state == "dying":
            self.player.update_dying(dt)
            self.death_timer -= dt
            if self.death_timer <= 0:
                if self.lives <= 0:
                    self.request_scene("game_over", score=self.score)
                else:
                    self._reset_round(full=False)
            return

        if self.state != "play":
            return

        keys = pygame.key.get_pressed()
        self.player.update(dt, keys)

        if self.invincible > 0:
            self.invincible -= dt

        # ボーナスは 1 秒ごとに減少（0 下限）
        self._bonus_tick += dt
        while self._bonus_tick >= 1.0:
            self._bonus_tick -= 1.0
            self.bonus = max(0, self.bonus - DK81_BONUS_DRAIN)

        # 樽の生成（DK の位置から）
        self.spawn_timer += dt
        if self.spawn_timer >= DK81_BARREL_SPAWN_INTERVAL:
            self.spawn_timer = 0.0
            bx, bg = stage.BARREL_SPAWN
            self.barrels.append(DK81Barrel(bx, bg))

        # 樽の更新
        for b in self.barrels:
            b.update(dt)
        self.barrels = [b for b in self.barrels if b.alive]

        self._check_jump_bonus()
        self._check_hit()
        self._check_clear()
        self._update_high()

    def _update_high(self):
        if self.score > DonkeyKong81Scene.HIGH_SCORE:
            DonkeyKong81Scene.HIGH_SCORE = self.score

    def _check_jump_bonus(self):
        if self.player.state != "air":
            return
        pr = self.player.get_rect()
        for b in self.barrels:
            if b.scored:
                continue
            if abs(b.cx - self.player.cx) < 18 and b.cy > pr.bottom:
                b.scored = True
                self.score += DK81_JUMP_BONUS
                self.sound.play_se("score")

    def _check_hit(self):
        if self.invincible > 0:
            return
        pr = self.player.get_rect()
        for b in self.barrels:
            if check_rect_collision(pr, b.get_rect()):
                self.lives -= 1
                self.state = "dying"
                self.death_timer = DK81_DEATH_TIME
                self.player.start_dying()
                self.sound.play_se("death")
                return

    def _check_clear(self):
        # ポーリンに到達したらクリア（残りボーナスを加算）
        if check_rect_collision(self.player.get_rect(), stage.pauline_rect()):
            self.score += int(self.bonus)
            self._update_high()
            self.sound.play_se("clear")
            self.state = "clear"
            self.request_scene("clear", score=self.score)

    # --- 描画 ---------------------------------------------------------
    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        stage.draw(screen)
        self._draw_dk(screen)
        self._draw_pauline(screen)

        for b in self.barrels:
            b.draw(screen)

        blink = self.invincible > 0 and int(self.invincible * 12) % 2 == 0
        self.player.draw(screen, blink=blink)

        self._draw_hud(screen)
        self._draw_controls(screen)

        if self.state == "intro":
            self._draw_center_text(screen, "HOW HIGH CAN YOU GET?", COLOR_YELLOW)
        elif self.state == "dying":
            self._draw_center_text(screen, "MISS!", COLOR_RED)

    def _draw_dk(self, screen):
        x, y = stage.DK_POS   # y は G5 の表面（足元）
        t = math.sin(self.dk_anim * 4)
        # 体
        pygame.draw.rect(screen, COLOR_DK, (x - 28, y - 58, 56, 52), border_radius=8)
        # 顔
        pygame.draw.rect(screen, COLOR_DK_FACE, (x - 17, y - 46, 34, 25), border_radius=6)
        pygame.draw.circle(screen, COLOR_BLACK, (x - 8, y - 36), 3)
        pygame.draw.circle(screen, COLOR_BLACK, (x + 8, y - 36), 3)
        pygame.draw.line(screen, COLOR_BLACK, (x - 5, y - 27), (x + 5, y - 27), 2)
        # 腕（樽を投げる動き）
        arm_y = y - 42 + int(t * 6)
        pygame.draw.rect(screen, COLOR_DK, (x + 22, arm_y, 18, 11), border_radius=4)
        pygame.draw.rect(screen, COLOR_DK, (x - 40, y - 36, 18, 11), border_radius=4)
        # 足
        pygame.draw.rect(screen, COLOR_DK, (x - 24, y - 10, 16, 10), border_radius=3)
        pygame.draw.rect(screen, COLOR_DK, (x + 8, y - 10, 16, 10), border_radius=3)

    def _draw_pauline(self, screen):
        r = stage.pauline_rect()
        pygame.draw.rect(screen, COLOR_PAULINE, (r.x, r.y + 12, r.width, r.height - 12))
        pygame.draw.circle(screen, DK81_COLOR_SKIN, (r.centerx, r.y + 8), 8)
        # HELP! 表示（点滅）
        if int(self.dk_anim * 2) % 2 == 0:
            help_text = self.font.render("HELP!", True, COLOR_WHITE)
            screen.blit(help_text, (r.centerx - help_text.get_width() // 2, r.y - 22))

    def _draw_hud(self, screen):
        score = self.font.render(f"SCORE  {self.score:06d}", True, COLOR_WHITE)
        screen.blit(score, (12, 10))
        high = self.font.render(
            f"HIGH  {DonkeyKong81Scene.HIGH_SCORE:06d}", True, COLOR_RED)
        screen.blit(high, (12, 34))
        bonus = self.font.render(f"BONUS  {int(self.bonus):04d}", True, COLOR_YELLOW)
        screen.blit(bonus, (SCREEN_WIDTH // 2 - bonus.get_width() // 2, 10))
        # 残機（マリオの頭アイコン）
        for i in range(self.lives):
            ix = SCREEN_WIDTH - 28 - i * 26
            pygame.draw.rect(screen, COLOR_RED, (ix, 12, 18, 8))
            pygame.draw.rect(screen, DK81_COLOR_SKIN, (ix + 2, 18, 14, 8))
        # ステージ表示
        meter = self.font.render("25 m", True, COLOR_LIGHTBLUE)
        screen.blit(meter, (SCREEN_WIDTH - 28 - meter.get_width(), 34))

    def _draw_controls(self, screen):
        text = "ARROWS: MOVE / CLIMB     SPACE: JUMP     ESC: MENU"
        surf = self.font_hint.render(text, True, COLOR_GRAY)
        screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 14)))

    def _draw_center_text(self, screen, text, color):
        surf = self.big_font.render(text, True, color)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(surf, rect)
