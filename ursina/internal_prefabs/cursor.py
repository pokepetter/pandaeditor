from ursina import *

class Cursor(Entity):
    def __init__(self):
        super().__init__()
        self.parent = camera.ui
        # self.texture = 'cursor'
        self.model = 'quad'
        self.color = color.light_gray
        self.z = -.1
        # self.origin = (-.49, .49)
        self.scale *= .05
        self.render_queue = 1

    def update(self, dt):
        self.position = (mouse.x * window.aspect_ratio, mouse.y)