import bpy
from bpy.props import IntProperty, StringProperty, EnumProperty, CollectionProperty, FloatProperty, BoolProperty, FloatVectorProperty
from bpy.types import PropertyGroup
from matplotlib import font_manager
import logging
import time

from .operators.png_overlay import PNGOverlayOperator
from .operators.move_color_value import MoveColorValue
from .ui.color_values_list import COLOR_UL_Values_List
from .ui.png_overlay_panel import PNGOverlayPanel
from .properties.color_value import ColorValue
from .properties.legend_settings import LegendSettings
from .utils.gradient_bar import create_gradient_bar
from .utils.compositor_utils import update_legend_position_in_compositor, update_legend_scale_in_compositor
from .utils.color_utils import get_colormap_items, update_colormap
from .operators.choose_shader import LEGEND_OT_choose_shader, update_legend_from_shader

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO)


def update_nodes(self, context):
    scene = context.scene
    current_num_nodes = len(scene.colors_values)
    new_num_nodes = scene.num_nodes

    if new_num_nodes > current_num_nodes:
        for i in range(current_num_nodes, new_num_nodes):
            new_color = scene.colors_values.add()
            new_color.color = (1.0, 1.0, 1.0)  
            new_color.value = f"{i/(new_num_nodes-1):.2f}"
    elif new_num_nodes < current_num_nodes:
        for i in range(current_num_nodes - new_num_nodes):
            scene.colors_values.remove(len(scene.colors_values) - 1)


    for i, color_value in enumerate(scene.colors_values):
        color_value.value = f"{i/(new_num_nodes-1):.2f}"

def update_legend_position(self, context):
    update_legend_position_in_compositor(context)

def update_legend_scale(self, context):
    scene = context.scene
    if scene.legend_scale_linked:
        current_x = scene.legend_scale_x
        current_y = scene.legend_scale_y
        
        if self == scene.legend_scale_x and current_x != current_y:
            scene.legend_scale_y = current_x
        elif self == scene.legend_scale_y and current_y != current_x:
            scene.legend_scale_x = current_y
    
    update_legend_scale_in_compositor(context)
    
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

def update_legend_scale_mode(self, context):
    from .utils.compositor_utils import update_legend_scale_in_compositor
    update_legend_scale_in_compositor(context)
    
    for area in context.screen.areas:
        area.tag_redraw()

def update_legend(self, context):
    from .utils.compositor_utils import update_legend_scale_in_compositor
    update_legend_scale_in_compositor(context)

def get_system_fonts(self, context):
    return [(f.name, f.name, f.name) for f in font_manager.fontManager.ttflist]

classes = (
    ColorValue,
    LegendSettings,
    PNGOverlayOperator,
    MoveColorValue,
    COLOR_UL_Values_List,
    PNGOverlayPanel,
    LEGEND_OT_choose_shader,
)

_prev_obj_name = None
_prev_signature = None
_processing_auto = False
_last_change_time = 0.0
_DEBOUNCE_SEC = 0.2
_timer_running = False


def _build_shader_signature(obj):
    try:
        mat = obj.active_material or (obj.data.materials[0] if obj.data.materials else None)
        if not mat or not mat.use_nodes or not mat.node_tree:
            return (obj.name, None, None, None, None, None)
        nodes = mat.node_tree.nodes
        node_attribute = None
        node_map_range = None
        node_colorramp = None
        for node in nodes:
            if node.type == 'ATTRIBUTE' and hasattr(node, 'attribute_name'):
                node_attribute = node
            elif node.type == 'MAP_RANGE':
                node_map_range = node
            elif node.type == 'VALTORGB':
                node_colorramp = node
        attr_name = getattr(node_attribute, 'attribute_name', None) if node_attribute else None
        from_min = None
        from_max = None
        if node_map_range and 'From Min' in node_map_range.inputs and 'From Max' in node_map_range.inputs:
            from_min = float(node_map_range.inputs['From Min'].default_value)
            from_max = float(node_map_range.inputs['From Max'].default_value)
        cmap_label = None
        try:
            cmap_prop = mat.get("sciblend_colormap", None)
            if isinstance(cmap_prop, str) and cmap_prop.strip():
                cmap_label = cmap_prop.strip().upper()
        except Exception:
            pass
        if not cmap_label and node_colorramp:
            cmap_label = (node_colorramp.label or node_colorramp.name or '').strip().upper() or None
        return (obj.name, getattr(mat, 'name', None), attr_name, from_min, from_max, cmap_label)
    except Exception as e:
        logger.debug(f"Signature build failed: {e}")
        return (getattr(obj, 'name', None), None, None, None, None, None)


def _debounced_generate_overlay():
    global _timer_running
    try:
        now = time.monotonic()
        if now - _last_change_time < _DEBOUNCE_SEC:
            return 0.1  
        try:
            sc = getattr(bpy.context, 'scene', None)
            if sc and getattr(sc.legend_settings, 'legend_enabled', True):
                bpy.ops.compositor.png_overlay()
        except Exception as e:
            logger.exception("Failed to invoke png_overlay (debounced)", exc_info=e)
        return None
    finally:
        _timer_running = False


def _auto_update_legend(scene):
    global _prev_obj_name, _prev_signature, _processing_auto, _last_change_time, _timer_running
    settings = getattr(scene, 'legend_settings', None)
    if not settings:
        logger.debug("No legend_settings on scene")
        _prev_obj_name = None
        _prev_signature = None
        return
    if not settings.auto_from_shader:
        logger.debug("Auto from Shader disabled")
        _prev_obj_name = None
        _prev_signature = None
        return
    
    obj = getattr(bpy.context.view_layer.objects, 'active', None)
    obj = obj or getattr(bpy.context, 'active_object', None)
    current = obj.name if obj else None
    signature = _build_shader_signature(obj) if obj else None
    logger.debug(f"Depsgraph: active='{current}' prev='{_prev_obj_name}' sig='{signature}' prev_sig='{_prev_signature}'")
    if obj and signature != _prev_signature:
        _processing_auto = True
        try:
            ok = update_legend_from_shader(scene, obj)
            logger.info(f"update_legend_from_shader ok={ok}")
            _prev_obj_name = current
            _prev_signature = signature
            _last_change_time = time.monotonic()
            if not _timer_running:
                _timer_running = True
                try:
                    bpy.app.timers.register(_debounced_generate_overlay, first_interval=_DEBOUNCE_SEC)
                except Exception as e:
                    _timer_running = False
                    logger.exception("Failed to register debounce timer", exc_info=e)
        except Exception as e:
            logger.exception("Error updating legend from shader", exc_info=e)
        finally:
            _processing_auto = False


def _depsgraph_handler(dummy):
    try:
        sc = getattr(bpy.context, 'scene', None)
        if sc:
            _auto_update_legend(sc)
    except Exception as e:
        logger.exception("Depsgraph handler error", exc_info=e)


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            bpy.utils.unregister_class(cls)
            bpy.utils.register_class(cls)

    bpy.types.Scene.legend_settings = bpy.props.PointerProperty(type=LegendSettings)


def unregister():
    del bpy.types.Scene.legend_settings

    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

if __name__ == "__main__":
    register()
