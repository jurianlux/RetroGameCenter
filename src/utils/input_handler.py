import pygame


class InputHandler:
    """キー入力を管理するクラス"""

    def __init__(self):
        self.keys_pressed = set()
        self.keys_released = set()

    def handle_event(self, event):
        """イベントを処理してキーの状態を更新"""
        if event.type == pygame.KEYDOWN:
            self.keys_pressed.add(event.key)
        elif event.type == pygame.KEYUP:
            self.keys_pressed.discard(event.key)

    def is_key_pressed(self, key):
        """指定されたキーが押されているか"""
        return key in self.keys_pressed

    def is_key_just_pressed(self, key):
        """指定されたキーが今フレーム押されたか"""
        return key in self.keys_released

    def clear_frame(self):
        """フレーム終了時に状態をリセット"""
        self.keys_released.clear()

    def mark_key_pressed(self, key):
        """キーが今フレーム押されたことを記録"""
        self.keys_released.add(key)
