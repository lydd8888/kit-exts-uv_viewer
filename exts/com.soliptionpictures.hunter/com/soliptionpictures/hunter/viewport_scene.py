from functools import partial

from omni.ui import scene as sc
import omni.ui as ui
from .object_info_manipulator import ObjInfoManipulator
from .uv_viewer import UvModel
import carb
from omni.ui import color as cl
import omni.kit.app
import omni.client
import threading
import os
from . import constants


class ViewportSceneInfo():
    """The scene view overlay
    
    Build the Uv and Uv button on the given viewport window.
    """
    def __init__(self, model: UvModel, viewport_window: ui.Window, ext_id: str) -> None:
        """
        for check UV map changed
        """
        self.filename = "D:/Amazon_Box_Stable_Diffusion/HoudiniUV/UV_Viewer_Extension/kit-exts-uv_viewer/exts/com.soliptionpictures.hunter/data/output.png"
        self.previous_timestamp = None  # Initialize the previous timestamp
        """
        Overlay Constructor

        Args:
            viewport_window (Window): The viewport window to build the overlay on.
            ext_id (str): The extension id.
        """

        self.model = model
        self.scene_view = None
        self.viewport_window = viewport_window
        self.ext_id = ext_id
        self.on_window_changed()
        
        self.previous_resolution = (None, None)
        # Rebuild the overlay whenever the model change
        self.model.add_model_changed_fn(self.build_uv_overlay)

        # Rebuild the overlay whenever the viewport resolution changed
        self.check_resolution_periodically()
    
    def check_resolution_periodically(self):
        self.check_resolution_change()
        # Call this method every 1 second, for example
        threading.Timer(0.1, self.check_resolution_periodically).start()
    
    def check_resolution_change(self):
        current_resolution = self.viewport_window.viewport_api.get_texture_resolution()
        if current_resolution != self.previous_resolution:
            self.build_uv_overlay()
            self.previous_resolution = current_resolution

    def on_window_changed(self, *args):
        """Update aspect ratio and rebuild overlay when viewport window changes."""
        if self.viewport_window is None:
            return
        
        settings = carb.settings.get_settings()
        fill = self.viewport_window.viewport_api.fill_frame

        if fill: 
            width = self.viewport_window.frame.computed_width + 8
            height = self.viewport_window.height
        else:
            width, height = self.viewport_window.viewport_api.resolution
        self._aspect_ratio = width / height
        self.model = self.get_model()
        carb.log_info("build_overlay")
        self.build_uv_overlay()

    
    def get_aspect_ratio_flip_threshold(self):
        """Get magic number for aspect ratio policy.

        Aspect ratio policy doesn't seem to swap exactly when window_aspect_ratio == window_texture_aspect_ratio.
        This is a hack that approximates where the policy changes.
        """
        return self.get_aspect_ratio()*0.95
    
    def build_uv_overlay(self, *args):
        # Create a unique franme for our SceneView
        with self.viewport_window.get_frame(self.ext_id):
            with ui.ZStack():
            # Create a default SceneView (it has a default camera-model)
                self.scene_view = sc.SceneView()
                with self.scene_view.scene: 
                    if self.model.uv_enabled.as_bool:
                        ObjInfoManipulator(viewport_window=self.viewport_window, model=self.get_model())
            # Register the SceneView with the Viewport to get projection and view updates
            # This is control 
            # self.viewport_window.viewport_api.add_scene_view(self.scene_view)
            # Build UV Menu button
                with ui.VStack():
                        ui.Spacer()
                        with ui.HStack(height=0):
                            ui.Spacer()
                            self.uv_menu = UvMenu(self.model)
                    
    
    def get_aspect_ratio(self):
        return self._aspect_ratio
    
    def get_model(self):
        return self.model
   
    def __del__(self):
        self.destroy()

    def destroy(self):
        if self.scene_view:
            # Empty the SceneView of any elements it may have
            self.scene_view.scene.clear()
            # un-register the SceneView from Viewport updates
            if self.viewport_window:
                self.viewport_window.viewport_api.remove_scene_view(self.scene_view)
        # Remove our references to these objects
        self.viewport_window = None
        self.scene_view = None


class UvMenu():
    """The popup uv menu"""
    def __init__(self, model: UvModel):
        self.model = model
        self.button = ui.Button("Show Uv", height = 0, width = 0, mouse_pressed_fn=self.show_uv_menu,
                                  style={"margin": 10, "padding": 5, "color": cl.white})
        self.uv_menu = None
    
    def on_group_check_changed(self, safe_area_group, model):
        """Enables/disables safe area groups

        When a safe area checkbox state changes, all the widgets of the respective
        group should be enabled/disabled.

        Args:
            safe_area_group (HStack): The safe area group to enable/disable
            model (SimpleBoolModel): The safe group checkbox model.
        """
        safe_area_group.enabled = model.as_bool
    
    def show_uv_menu(self, x, y, button, modifier):
        self.uv_menu = ui.Menu("Uv Option", width=200, height=100)
        self.uv_menu.clear()

        with self.uv_menu:
            with ui.Frame(width=0, height=100):
                with ui.HStack():
                    with ui.VStack():
                        ui.Label("Uv Option", alignment=ui.Alignment.LEFT, height=30)
                        with ui.HStack(width=0):
                            ui.Spacer(width=20)
                            cb = ui.CheckBox(model=self.model.uv_enabled)
                            # if not action_safe_group, the floatslider will not work
                            action_safe_group = ui.HStack(enabled=self.model.uv_enabled.as_bool)
                            callback = partial(self.on_group_check_changed, action_safe_group)
                            cb.model.add_value_changed_fn(callback)
                            with action_safe_group:
                                ui.Spacer(width=10)
                                ui.Label("uv viewer", alignment=ui.Alignment.TOP)
                                ui.Spacer(width=14)
                                with ui.VStack():
                                    ui.FloatSlider(self.model.uv_size, width=100,
                                                   format="%.0f%%", min=0, max=100, step=1)
                                    ui.Rectangle(name="ActionSwatch", height=5)
                                    ui.Spacer()
        
        self.uv_menu.show_at(x - self.uv_menu.width, y - self.uv_menu.height)



