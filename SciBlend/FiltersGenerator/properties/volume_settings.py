import bpy
from bpy.props import CollectionProperty, IntProperty, StringProperty
from .volume_item import VolumeItem

_UPDATING_NODES = False
_SCHEDULED_UPDATE = None
_ITEM_TIMERS = {}


def _schedule_volume_item_update(item):
    """
    Schedule an update for a specific volume item.
    """
    global _ITEM_TIMERS
    
    item_id = id(item)
    
    def _do_update():
        global _UPDATING_NODES, _ITEM_TIMERS
        
        if item_id in _ITEM_TIMERS:
            del _ITEM_TIMERS[item_id]
        
        if _UPDATING_NODES:
            return None
        
        pending_sig = getattr(item, '_last_scheduled_signature', None)
        last_applied = getattr(item, '_last_applied_signature', None)
        
        if pending_sig is not None and pending_sig == last_applied:
            return None
        
        _UPDATING_NODES = True
        try:
            from ..operators.volume_update import update_volume_item_material
            result = update_volume_item_material(bpy.context, item)
            
            if result is not None:
                if pending_sig is None:
                    from .volume_item import _signature
                    pending_sig = _signature(item)
                item._last_applied_signature = pending_sig
        except Exception as e:
            import traceback
            print(f"Error in _do_update: {e}")
            traceback.print_exc()
        _UPDATING_NODES = False
        return None
    
    if item_id in _ITEM_TIMERS:
        try:
            bpy.app.timers.unregister(_ITEM_TIMERS[item_id])
        except Exception:
            pass
    
    _ITEM_TIMERS[item_id] = _do_update
    try:
        bpy.app.timers.register(_do_update, first_interval=0.05)
    except Exception:
        pass


class VolumeRenderingSettings(bpy.types.PropertyGroup):
    """
    Container for multiple volume items with list management.
    """
    
    volume_items_index: IntProperty(
        name="Active Volume Index",
        default=0,
        min=0
    )
    
    last_import_dir: StringProperty(
        name="Last Import Dir",
        default="",
        subtype='DIR_PATH'
    )


def get_active_volume_item(context):
    """
    Get the currently active volume item from settings.
    """
    settings = getattr(context.scene, 'filters_volume_settings', None)
    if not settings:
        return None
    
    if not settings.volume_items:
        return None
    
    idx = settings.volume_items_index
    if 0 <= idx < len(settings.volume_items):
        return settings.volume_items[idx]
    
    return None


def register():
    pass


def unregister():
    pass 