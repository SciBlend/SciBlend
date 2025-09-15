import bpy
from bpy.types import PropertyGroup
from bpy.props import FloatProperty
from ..utils.nodes import find_shader_map_range_node


def _update_map_range_from_min(self, context):
    """Update the 'From Min' input of the Shader Generator Map Range node on the active object's material."""
    obj = getattr(context, 'active_object', None)
    mat = getattr(obj, 'active_material', None) if obj else None
    node = find_shader_map_range_node(mat) if mat else None
    try:
        if node and 'From Min' in node.inputs:
            node.inputs['From Min'].default_value = float(self.from_min)
            if mat and mat.node_tree:
                mat.node_tree.update_tag()
    except Exception:
        pass


def _update_map_range_from_max(self, context):
    """Update the 'From Max' input of the Shader Generator Map Range node on the active object's material."""
    obj = getattr(context, 'active_object', None)
    mat = getattr(obj, 'active_material', None) if obj else None
    node = find_shader_map_range_node(mat) if mat else None
    try:
        if node and 'From Max' in node.inputs:
            node.inputs['From Max'].default_value = float(self.from_max)
            if mat and mat.node_tree:
                mat.node_tree.update_tag()
    except Exception:
        pass


class ShaderGeneratorSettings(PropertyGroup):
    """Panel settings for Shader Generator to control Map Range bounds."""
    from_min: FloatProperty(
        name="From Min",
        description="Input range minimum for Map Range",
        default=0.0,
        update=_update_map_range_from_min,
    )
    from_max: FloatProperty(
        name="From Max",
        description="Input range maximum for Map Range",
        default=1.0,
        update=_update_map_range_from_max,
    ) 