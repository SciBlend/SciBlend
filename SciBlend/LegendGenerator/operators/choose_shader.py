import bpy
from bpy.types import Operator


def update_legend_from_shader(scene, obj):
    """Read shader nodes from the given object's active material and map them to legend settings (name, range and colormap)."""
    settings = scene.legend_settings
    if not obj or obj.type != 'MESH':
        return False
    if not obj.data.materials:
        return False
    mat = obj.active_material or obj.data.materials[0]
    if not mat or not mat.use_nodes or not mat.node_tree:
        return False

    nodes = mat.node_tree.nodes

    node_attribute = None
    node_map_range = None
    node_colorramp = None

    for node in nodes:
        if node.type == 'ATTRIBUTE' and hasattr(node, 'attribute_name'):
            node_attribute = node
        elif node.type == 'MAP_RANGE':
            node_map_range = node
        elif node.type in {'VALTORGB'}:
            node_colorramp = node

    if node_attribute and getattr(node_attribute, 'attribute_name', None):
        settings.legend_name = node_attribute.attribute_name

    try:
        if node_map_range and 'From Min' in node_map_range.inputs and 'From Max' in node_map_range.inputs:
            start = float(node_map_range.inputs['From Min'].default_value)
            end = float(node_map_range.inputs['From Max'].default_value)
            settings.colormap_start = start
            settings.colormap_end = end
    except Exception:
        pass

    detected = None
    try:
        cmap_prop = mat.get("sciblend_colormap", None)
        if isinstance(cmap_prop, str):
            detected = cmap_prop.strip().upper()
    except Exception:
        pass
    if not detected and node_colorramp:
        candidate = (node_colorramp.label or node_colorramp.name or '').strip().upper()
        detected = candidate or None
    if detected:
        try:
            from ..utils.color_utils import load_colormaps
            cmaps = load_colormaps()
            if detected in cmaps:
                settings.colormap = detected
        except Exception:
            pass

    return True


class LEGEND_OT_choose_shader(Operator):
    bl_idname = "legend.choose_shader"
    bl_label = "Choose Shader"
    bl_description = "Read the active object's shader to configure Legend Generator"

    def execute(self, context):
        scene = context.scene
        obj = context.active_object
        ok = update_legend_from_shader(scene, obj)
        if not ok:
            self.report({'ERROR'}, "No shader info found on active object")
            return {'CANCELLED'}
        self.report({'INFO'}, "Legend settings updated from shader")
        return {'FINISHED'} 