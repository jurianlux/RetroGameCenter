import math
import pygame
from scenes.base_scene import BaseScene
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE,
    COLOR_GREEN, COLOR_YELLOW,
)


class ClearScene(BaseScene):
    def on_enter(self):
        super().on_enter()
        self.score = self.kwargs.get("score", 0)
        self.font_title = pygame.font.Font(None, 84)
        self.font_text = pygame.font.Font(None, 44)
        self.font_small = pygame.font.Font(None, 32)
        self.time = 0.0

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.request_scene("menu")

    def update(self, dt):
        self.time += dt

    def draw(self, screen):
        screen.fill(COLOR_BLACK)
        cx = SCREEN_WIDTH // 2

        bob = int(math.sin(self.time * 4) * 6)
        title = self.font_title.render("STAGE CLEAR!", True, COLOR_GREEN)
        screen.blit(title, title.get_rect(center=(cx, 180 + bob)))

        msg = self.font_text.render("YOU RESCUED PAULINE!", True, COLOR_YELLOW)
        screen.blit(msg, msg.get_rect(center=(cx, 270)))

        score = self.font_text.render(f"SCORE  {self.score:06d}", True, COLOR_WHITE)
        screen.blit(score, score.get_rect(center=(cx, 340)))

        if int(self.time * 2) % 2 == 0:
            info = self.font_small.render("PRESS ENTER TO RETURN TO MENU", True, COLOR_WHITE)
            screen.blit(info, info.get_rect(center=(cx, SCREEN_HEIGHT - 110)))
