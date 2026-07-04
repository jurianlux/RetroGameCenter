"""ドンキーコング ステージ 1。

斜めの鉄骨をはしごで登り、樽を避けて最上段のポーリンを目指す。
樽に当たるとミス（ライフ -1）。樽を飛び越えると +100。
"""

import math
import pygame
from scenes.base_scene import BaseScene
from game_objects.player import Player
from game_objects.barrel import Barrel
from game_objects.collision import check_rect_collision
import game_objects.level as level
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE, COLOR_YELLOW,
    COLOR_GRAY, COLOR_DK, COLOR_DK_FACE, COLOR_PAULINE, COLOR_RED,
    BARREL_SPAWN_INTERVAL, BARREL_RADIUS, START_LIVES, JUMP_BONUS,
    CLEAR_BONUS_START, CLEAR_BONUS_DRAIN, RESPAWN_INVINCIBLE,
)


class DonkeyKongScene(BaseScene):
    def on_enter(self):
        super().on_enter()
        self.font = pygame.font.Font(None, 30)
        self.font_hint = pygame.font.Font(None, 22)
        self.big_font = pygame.font.Font(None, 84)

        self.lives = START_LIVES
        self.score = 0
        self.bonus = CLEAR_BONUS_START
        self._reset_round(full=True)

    def _reset_round(self, full=False):
        """プレイヤー位置と樽をリセット（ミス後の復帰）。"""
        sx = level.GIRDERS[0][0] + 40
        self.player = Player(sx, 0)
        if full:
            self.barrels = []
            self.spawn_timer = 0.0
        self.invincible = RESPAWN_INVINCIBLE if not full else 0.0
        self.state = "play"   # play / dying / over / clear
        self.death_timer = 0.0
        self.dk_anim = 0.0

    def handle_input(self, event):
        if self.state != "play":
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.player.jump()

    def update(self, dt):
        self.dk_anim += dt
        if self.state == "dying":
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

        # ボーナスは時間で減少
        self.bonus = max(0, self.bonus - CLEAR_BONUS_DRAIN * dt)

        # 樽の生成
        self.spawn_timer += dt
        if self.spawn_timer >= BARREL_SPAWN_INTERVAL:
            self.spawn_timer = 0.0
            bx, bg = level.BARREL_SPAWN
            self.barrels.append(Barrel(bx, bg))

        # 樽の更新
        for b in self.barrels:
            b.update(dt)
        self.barrels = [b for b in self.barrels if b.alive]

        self._check_jump_bonus()
        self._check_hit()
        self._check_clear()

    def _check_jump_bonus(self):
        pr = self.player.get_rect()
        if self.player.state != "air":
            return
        for b in self.barrels:
            if b.scored:
                continue
            if abs(b.cx - self.player.cx) < 18 and b.cy > pr.bottom:
                b.scored = True
                self.score += JUMP_BONUS

    def _check_hit(self):
        if self.invincible > 0:
            return
        pr = self.player.get_rect()
        for b in self.barrels:
            if check_rect_collision(pr, b.get_rect()):
                self.lives -= 1
                self.state = "dying"
                self.death_timer = 1.0
                return

    def _check_clear(self):
        # ポーリンの足場に到達したらクリア
        pauline = self._pauline_rect()
        if check_rect_collision(self.player.get_rect(), pauline):
            self.score += int(self.bonus)
            self.request_scene("clear", score=self.score)

    def _pauline_rect(self):
        xl, xr, yl, _ = level.GIRDERS[level.PAULINE_GIRDER]
        cx = (xl + xr) // 2
        return pygame.Rect(cx - 14, yl - 34, 28, 34)

    # --- 描画 --------------------------------------------------------
    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        level.draw(screen)
        self._draw_dk(screen)
        self._draw_pauline(screen)

        for b in self.barrels:
            b.draw(screen)

        blink = self.invincible > 0 and int(self.invincible * 12) % 2 == 0
        if self.state != "dying":
            self.player.draw(screen, blink=blink)

        self._draw_hud(screen)
        self._draw_controls(screen)

        if self.state == "dying":
            self._draw_center_text(screen, "MISS!", COLOR_RED)

    def _draw_dk(self, screen):
        x, y = level.DK_POS
        t = math.sin(self.dk_anim * 4)
        # 体
        pygame.draw.rect(screen, COLOR_DK, (x - 26, y - 56, 52, 50), border_radius=8)
        # 顔
        pygame.draw.rect(screen, COLOR_DK_FACE, (x - 16, y - 44, 32, 24), border_radius=6)
        pygame.draw.circle(screen, COLOR_BLACK, (x - 8, y - 34), 3)
        pygame.draw.circle(screen, COLOR_BLACK, (x + 8, y - 34), 3)
        # 腕（投げる動き）
        arm_y = y - 40 + int(t * 6)
        pygame.draw.rect(screen, COLOR_DK, (x + 18, arm_y, 16, 10), border_radius=4)

    def _draw_pauline(self, screen):
        r = self._pauline_rect()
        pygame.draw.rect(screen, COLOR_PAULINE, (r.x, r.y + 12, r.width, r.height - 12))
        pygame.draw.circle(screen, (245, 200, 150), (r.centerx, r.y + 8), 8)
        # HELP! 表示
        help_text = self.font.render("HELP!", True, COLOR_WHITE)
        screen.blit(help_text, (r.centerx - help_text.get_width() // 2, r.y - 20))

    def _draw_hud(self, screen):
        score = self.font.render(f"SCORE  {self.score:06d}", True, COLOR_WHITE)
        screen.blit(score, (12, 10))
        bonus = self.font.render(f"BONUS  {int(self.bonus):04d}", True, COLOR_YELLOW)
        screen.blit(bonus, (SCREEN_WIDTH // 2 - bonus.get_width() // 2, 10))
        # 残機（マリオの頭アイコン）
        for i in range(self.lives):
            ix = SCREEN_WIDTH - 28 - i * 26
            pygame.draw.rect(screen, COLOR_RED, (ix, 12, 18, 8))
            pygame.draw.rect(screen, (245, 200, 150), (ix + 2, 18, 14, 8))

    def _draw_controls(self, screen):
        text = "ARROWS: MOVE / CLIMB     SPACE: JUMP     ESC: MENU"
        surf = self.font_hint.render(text, True, COLOR_GRAY)
        screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 14)))

    def _draw_center_text(self, screen, text, color):
        surf = self.big_font.render(text, True, color)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(surf, rect)
