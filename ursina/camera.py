import sys
from ursina.entity import Entity
from panda3d.core import PerspectiveLens, OrthographicLens, LensNode, NodePath
from panda3d.core import Camera as PandaCamera
from panda3d.core import Texture as PandaTexture
from panda3d.core import Shader
from direct.filter.FilterManager import FilterManager
from ursina import application
from ursina import scene
from ursina import window
from ursina import color

# Test
class Camera(Entity):

    def __init__(self):
        super().__init__()
        self.parent = scene
        self.name = 'camera'
        self.eternal = True

        self._cam = None
        self._render = None
        self.ui_size = 40
        self._ui_lens_node = None
        self.ui = None
        self.fov = 40
        self.orthographic = False


    def set_up(self):
        self.display_region = base.camNode.get_display_region(0)
        win = self.display_region.get_window()

        self.perspective_lens = PerspectiveLens()
        self.perspective_lens = base.camLens # use panda3d's default for automatic aspect ratio on window resize
        self.lens = self.perspective_lens
        self.perspective_lens.set_aspect_ratio(window.screen_resolution[0] / window.screen_resolution[1])
        self.perspective_lens_node = LensNode('perspective_lens_node', self.perspective_lens)
        self.lens_node = self.perspective_lens_node

        self.orthographic_lens = OrthographicLens()
        self.orthographic_lens.set_film_size(self.fov * window.aspect_ratio, self.fov)
        self.orthographic_lens_node = LensNode('orthographic_lens_node', self.orthographic_lens)

        application.base.cam.node().set_lens(self.lens)

        self.orthographic = False
        self.fov = 40
        self.clip_plane_near = 0.1
        self.clip_plane_far = 10000

        self.ui_display_region = win.make_display_region()
        self.ui_display_region.set_sort(20)

        self.ui_camera = NodePath(PandaCamera('ui_camera'))
        self.ui_lens = OrthographicLens()
        # moved set_film_size() to window module for correct aspect ratio after setting window size
        self.ui_lens.set_near_far(-1000, 1000)
        self.ui_camera.node().set_lens(self.ui_lens)
        self._ui_lens_node = LensNode('_ui_lens_node', self.ui_lens)

        self.ui_render = NodePath('ui_render')
        self.ui_render.set_depth_test(0)
        self.ui_render.set_depth_write(0)
        self.ui_camera.reparent_to(self.ui_render)
        self.ui_display_region.set_camera(self.ui_camera)
        scene.ui_camera = self.ui_camera

        self.ui = Entity(eternal=True, name='ui', parent=self.ui_camera, scale=(self.ui_size*.5, self.ui_size*.5))
        self.overlay = Entity(parent=self.ui, model='quad', scale_x=self.aspect_ratio, color=color.clear, eternal=True, z=-99)

        # these get created when setting a shader
        self.filter_manager = None
        self.filter_quad = None
        self.render_texture = None
        self.filter_quad = None
        self.depth_texture = None
        # self.normals_texture = None


    @property
    def orthographic(self):
        return self._orthographic

    @orthographic.setter
    def orthographic(self, value):
        self._orthographic = value
        if value:
            self.lens = self.orthographic_lens
            self.lens_node = self.orthographic_lens_node
            application.base.cam.node().set_lens(self.orthographic_lens)
        else:
            self.lens = self.perspective_lens
            self.lens_node = self.perspective_lens_node
            application.base.cam.node().set_lens(self.perspective_lens)

        self.fov = self.fov


    @property
    def fov(self):
        return self._fov

    @fov.setter
    def fov(self, value):
        value = max(1, value)
        self._fov = value
        if not self.orthographic and hasattr(self, 'perspective_lens'):
            self.perspective_lens.set_fov(value)
            application.base.cam.node().set_lens(self.perspective_lens)

        elif self.orthographic and hasattr(self, 'orthographic_lens'):
            self.orthographic_lens.set_film_size(value * self.aspect_ratio, value)
            application.base.cam.node().set_lens(self.orthographic_lens)

    @property
    def clip_plane_near(self):
        return self.lens.getNear()

    @clip_plane_near.setter
    def clip_plane_near(self, value):
        self.lens.set_near(value)

    @property
    def clip_plane_far(self):
        return self.lens.getFar()

    @clip_plane_far.setter
    def clip_plane_far(self, value):
        self.lens.set_far(value)

    @property
    def aspect_ratio(self):
        return self.perspective_lens.get_aspect_ratio()

    @property
    def shader(self):
        return self._shader

    @shader.setter
    def shader(self, value):
        self._shader = value
        if value is None:
            self.filter_manager.cleanup()
            self.filter_manager = None
            if self.filter_quad:
                self.filter_quad.removeNode()
                # print('removed shader')
            return None

        shader = value
        if hasattr(value, '_shader'):
            shader = value._shader

        if not self.filter_manager:
            self.filter_manager = FilterManager(base.win, base.cam)
            self.render_texture = PandaTexture()
            self.depth_texture = PandaTexture()
            self.normals_texture = PandaTexture()
            self.filter_quad = self.filter_manager.renderSceneInto(colortex=self.render_texture, depthtex=self.depth_texture)
            # from panda3d.core import AuxBitplaneAttrib
            # self.filter_quad = self.filter_manager.renderSceneInto(colortex=self.render_texture, depthtex=self.depth_texture, auxtex=self.normal_texture, auxbits=AuxBitplaneAttrib.ABOAuxNormal)
            self.filter_quad.setShaderInput("tex", self.render_texture)
            self.filter_quad.setShaderInput("dtex", self.depth_texture)
            # self.filter_quad.setShaderInput("ntex", self.normals_texture)

        self.filter_quad.setShader(shader)

        if hasattr(value,'default_input'):
            for key, value in value.default_input.items():
                self.set_shader_input(key, value)

        print('set camera shader to:', shader)


    def set_shader_input(self, name, value):
        if self.filter_quad:
            self.filter_quad.setShaderInput(name, value)
        else:
            print('no filter quad')


sys.modules[__name__] = Camera()


if __name__ == '__main__':
    from ursina import *
    app = Ursina()
    # app.load_editor()
    scene.camera.orthographic = True
    e = Entity()
    e.model = 'quad'
    e.color = color.random_color()
    e.position = (-2, 0, 10)

    e = Entity()
    e.model = 'quad'
    e.color = color.random_color()
    e.position = (2, 0, 10)

    e = Entity()
    e.model = 'quad'
    e.color = color.random_color()
    e.position = (0, 0, 40)
    # from ursina import *
    # Button(text='test button')
    from ursina.shaders import camera_grayscale_shader
    camera.shader = camera_grayscale_shader

    # def update():
    #     t = Texture(camera.render_texture)
    #     print(t.pixels)
    app.run()
