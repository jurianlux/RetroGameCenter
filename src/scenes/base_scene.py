from abc import ABC, abstractmethod


class BaseScene(ABC):
    """全シーンの基本クラス。

    シーン遷移は self.next_scene に (シーン名, kwargs) をセットして要求する。
    GameManager が毎フレーム確認し、セットされていれば切り替える。
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.next_scene = None

    def request_scene(self, name, **kwargs):
        """次のシーンへの遷移を要求する。"""
        self.next_scene = (name, kwargs)

    def on_enter(self):
        """シーン開始時に呼ばれる。"""
        self.next_scene = None

    def on_exit(self):
        """シーン終了時に呼ばれる。"""
        pass

    @abstractmethod
    def handle_input(self, event):
        """単発イベント処理（KEYDOWN など）。"""
        pass

    @abstractmethod
    def update(self, dt):
        """フレーム更新 (dt: delta time in seconds)。"""
        pass

    @abstractmethod
    def draw(self, screen):
        """画面に描画。"""
        pass
