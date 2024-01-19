import omni.ext
import omni.ui as ui
# import viewport
from omni.kit.viewport.utility import get_active_viewport_window
from .viewport_scene import ViewportSceneInfo
from .uv_viewer import UvModel
from omni.ui import scene as sc
import carb



class UV_Viewer(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def __init__(self):
        super().__init__()
        self.viewport_scene = None

    def on_startup(self, ext_id: str) -> None:

        viewport_window = get_active_viewport_window()
        
        if viewport_window is not None:
            uv_model = UvModel()
            self.viewport_scene = ViewportSceneInfo(uv_model, viewport_window, ext_id)

    def on_shutdown(self):
        """Called when the extension is shutting down."""
        if self.viewport_scene:
            self.viewport_scene.destroy()
            self.viewport_scene = None