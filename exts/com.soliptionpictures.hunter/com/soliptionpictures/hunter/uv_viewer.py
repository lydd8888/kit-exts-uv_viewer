from omni.ui import scene as sc
from omni.ui_scene._scene import AbstractManipulatorItem
import omni.usd
from pxr import Tf
from pxr import Usd
from pxr import UsdGeom
import omni.ui as ui
from . import constants
import carb

class UvModel(sc.AbstractManipulatorModel):
    """
    The model that track mesh's uv
    """

    # Position needed for when we call item changed
    class PositionItem(sc.AbstractManipulatorItem):
        def __init__(self) -> None:
            super().__init__()
            self.value = [0,0,0]

    def __init__(self) -> None:
        super().__init__()
        # Current select prim
        self.prim = None
        # Set Current path
        self.current_path = ""
        # update to hold position object created
        self.position = UvModel.PositionItem()
        # Save the UsdContext name
        usd_context = self._get_context()
        # Get the Menu item
        self.uv_enabled = ui.SimpleBoolModel(True)
        self.uv_size = ui.SimpleFloatModel(constants.DEFAULT_UI_PERCENTAGE, min=0, max=100)

        # Track selection changes
        self.events = usd_context.get_stage_event_stream()
        self.stage_event_delegate = self.events.create_subscription_to_pop(
            self.on_stage_event, name="Object Info Selection Update"
        )

        self._register_submodel_callbacks()
        self._callbacks = []

    def _get_context(self) -> Usd.Stage:
        # Get the UsdContext we are attached to
        return omni.usd.get_context()
    
    def on_stage_event(self, event):
        # if statement to only check when selection changed
        if event.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            usd_context = self._get_context()
            stage = usd_context.get_stage()
            if not stage:
                return
            
            prim_paths = usd_context.get_selection().get_selected_prim_paths()
            if not prim_paths:
            # This turns off the manipulator when everything is deselected
                self._item_changed(self.position)
                self.current_path = ""
                return
            
            prim = stage.GetPrimAtPath(prim_paths[0])
            self.prim = prim
            self.current_path = prim_paths[0]
            
            # Position is changed because new selected object has a different position
            self._item_changed(self.position)
            
    def get_item(self, indentifier: str) -> AbstractManipulatorItem:
        if indentifier == "name":
            return self.current_path

    def destroy(self):
        self.events = None
        self.stage_event_delegate.unsubscribe()

    def _register_submodel_callbacks(self):
        """Register to listen to when any submodel values change."""
        self.uv_enabled.add_value_changed_fn(self._model_changed)
        self.uv_size.add_value_changed_fn(self._model_changed)

    def _model_changed(self, model):
        for callback in self._callbacks:
            callback()

    def add_model_changed_fn(self, callback):
        self._callbacks.append(callback)