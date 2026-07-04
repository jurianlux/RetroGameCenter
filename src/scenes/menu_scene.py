"""メニューシーン。レトロアーケード風のタイトル＋ゲーム選択。"""

import math
import pygame
from scenes.base_scene import BaseScene
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE,
    COLOR_YELLOW, COLOR_RED, COLOR_GIRDER, COLOR_BARREL, COLOR_GRAY,
)

# (表示名, シーンキー or None=準備中)
GAMES = [
    ("DONKEY KONG", "donkey_kong"),
    ("DONKEY KONG '81", "donkey_kong_81"),
    ("TETRIS", "tetris"),
    ("PAC-MAN", None),
    ("SPACE INVADERS", None),
]


class MenuScene(BaseScene):
    def on_enter(self):
        super().on_enter()
        self.font_title = pygame.font.Font(None, 88)
        self.font_menu = pygame.font.Font(None, 52)
        self.font_small = pygame.font.Font(None, 28)
        self.selected = 0
        self.time = 0.0

    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_UP:
            self.selected = (self.selected - 1) % len(GAMES)
        elif event.key == pygame.K_DOWN:
            self.selected = (self.selected + 1) % len(GAMES)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            scene_key = GAMES[self.selected][1]
            if scene_key:
                self.request_scene(scene_key)

    def update(self, dt):
        self.time += dt

    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        self._draw_border(screen)

        # タイトル（影付き・上下にゆれる）
        bob = int(math.sin(self.time * 2) * 4)
        title = "RETRO GAME CENTER"
        shadow = self.font_title.render(title, True, COLOR_RED)
        main = self.font_title.render(title, True, COLOR_YELLOW)
        cx = SCREEN_WIDTH // 2
        screen.blit(shadow, shadow.get_rect(center=(cx + 4, 110 + bob + 4)))
        screen.blit(main, main.get_rect(center=(cx, 110 + bob)))

        sub = self.font_small.render("- SELECT A GAME -", True, COLOR_WHITE)
        screen.blit(sub, sub.get_rect(center=(cx, 175)))

        # ゲーム一覧
        for i, (name, key) in enumerate(GAMES):
            y = 270 + i * 64
            selected = (i == self.selected)
            playable = key is not None
            if not playable:
                color = COLOR_GRAY
                label = f"{name}  (COMING SOON)"
            elif selected:
                color = COLOR_YELLOW
                label = name
            else:
                color = COLOR_WHITE
                label = name

            text = self.font_menu.render(label, True, color)
            rect = text.get_rect(center=(cx, y))
            screen.blit(text, rect)

            if selected:
                # 点滅する樽カーソル
                if int(self.time * 3) % 2 == 0:
                    bx = rect.left - 40
                    pygame.draw.circle(screen, COLOR_BARREL, (bx, y), 13)
                    pygame.draw.circle(screen, COLOR_GIRDER, (bx, y), 13, 2)

        # 操作説明（点滅）
        if int(self.time * 2) % 2 == 0:
            hint = self.font_small.render(
                "ARROW KEYS: SELECT     ENTER: PLAY", True, COLOR_WHITE)
            screen.blit(hint, hint.get_rect(center=(cx, SCREEN_HEIGHT - 45)))

    def _draw_border(self, screen):
        pygame.draw.rect(screen, COLOR_GIRDER,
                         (10, 10, SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20), 4)
