class SceneManager:
    """シーン管理・遷移を行うクラス"""

    def __init__(self):
        self.scenes = {}
        self.current_scene = None

    def register_scene(self, name, scene):
        """シーンを登録"""
        self.scenes[name] = scene

    def change_scene(self, scene_name, **kwargs):
        """シーン切り替え"""
        if self.current_scene:
            self.current_scene.on_exit()

        if scene_name not in self.scenes:
            raise ValueError(f"Scene '{scene_name}' not registered")

        self.current_scene = self.scenes[scene_name]
        self.current_scene.kwargs = kwargs
        self.current_scene.on_enter()

    def handle_input(self, event):
        """現在のシーンにイベント処理を委譲"""
        if self.current_scene:
            self.current_scene.handle_input(event)

    def update(self, dt):
        """現在のシーンを更新"""
        if self.current_scene:
            self.current_scene.update(dt)

    def draw(self, screen):
        """現在のシーンを描画"""
        if self.current_scene:
            self.current_scene.draw(screen)
