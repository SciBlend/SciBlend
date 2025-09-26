import bpy
from bpy.props import PointerProperty

from .properties.settings import SciBlendNodesSettings
from .properties.collection_item import CollectionListItem
from .properties.preset_item import PresetListItem
from .operators.apply_filter import SCIBLENDNODES_OT_apply_filter_to_collection, SCIBLENDNODES_OT_apply_preset, SCIBLENDNODES_OT_clear_collection_geo_nodes, SCIBLENDNODES_OT_rename_collection
from .operators.presets_crud import SCIBLENDNODES_OT_preset_add, SCIBLENDNODES_OT_preset_remove, SCIBLENDNODES_OT_preset_apply_selected
from .ui.collection_list import SCIBLENDNODES_UL_collection_list
from .ui.preset_list import SCIBLENDNODES_UL_preset_list
from .ui.panel import SCIBLENDNODES_PT_panel


classes = (
    CollectionListItem,
    PresetListItem,
    SciBlendNodesSettings,
    SCIBLENDNODES_UL_collection_list,
    SCIBLENDNODES_UL_preset_list,
    SCIBLENDNODES_OT_apply_filter_to_collection,
    SCIBLENDNODES_OT_apply_preset,
    SCIBLENDNODES_OT_preset_add,
    SCIBLENDNODES_OT_preset_remove,
    SCIBLENDNODES_OT_preset_apply_selected,
    SCIBLENDNODES_OT_clear_collection_geo_nodes,
    SCIBLENDNODES_OT_rename_collection,
    SCIBLENDNODES_PT_panel,
)

_nodes_timer_running = False
_nodes_last_change_time = 0.0
_NODES_DEBOUNCE_SEC = 0.2


def _debounced_apply():
    global _nodes_timer_running, _nodes_last_change_time
    try:
        import time
        now = time.monotonic()
        if now - _nodes_last_change_time < _NODES_DEBOUNCE_SEC:
            return 0.1
        try:
            sc = getattr(bpy.context, 'scene', None)
            if sc and getattr(sc, 'sciblend_nodes_settings', None):
                try:
                    bpy.ops.sciblend_nodes.apply_preset()
                except Exception:
                    pass
        except Exception:
            pass
        return None
    finally:
        _nodes_timer_running = False


def schedule_nodes_apply(scene: bpy.types.Scene | None = None):
    """Schedule an auto-apply of the current preset to the selected collection with debounce."""
    global _nodes_timer_running, _nodes_last_change_time
    try:
        import time
        _nodes_last_change_time = time.monotonic()
        if not _nodes_timer_running:
            _nodes_timer_running = True
            try:
                bpy.app.timers.register(_debounced_apply, first_interval=_NODES_DEBOUNCE_SEC)
            except Exception:
                _nodes_timer_running = False
    except Exception:
        pass


def register():
    """Register SciBlend Nodes module classes and attach scene properties."""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            bpy.utils.unregister_class(cls)
            bpy.utils.register_class(cls)
    bpy.types.Scene.sciblend_nodes_settings = PointerProperty(type=SciBlendNodesSettings)


def unregister():
    """Unregister SciBlend Nodes module classes and detach scene properties."""
    try:
        del bpy.types.Scene.sciblend_nodes_settings
    except Exception:
        pass
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass 