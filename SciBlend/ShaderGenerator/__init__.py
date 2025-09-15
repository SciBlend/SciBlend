import bpy
import logging
from bpy.props import CollectionProperty

from .properties.colorramp import ColorRampColor
from .properties.settings import ShaderGeneratorSettings
from .operators.colorramp import (
    COLORRAMP_OT_add_color,
    COLORRAMP_OT_remove_color,
    COLORRAMP_OT_save_custom,
    COLORRAMP_OT_load_custom,
    COLORRAMP_OT_import_json,
)
from .operators.create_shader import (
    MATERIAL_OT_create_shader,
    create_colormap_material,
)
from .ui.panel import MATERIAL_PT_shader_generator


logger = logging.getLogger(__name__)

__all__ = (
    'ColorRampColor',
    'COLORRAMP_OT_add_color',
    'COLORRAMP_OT_remove_color',
    'COLORRAMP_OT_save_custom',
    'COLORRAMP_OT_load_custom',
    'COLORRAMP_OT_import_json',
    'MATERIAL_OT_create_shader',
    'MATERIAL_PT_shader_generator',
    'create_colormap_material',
)


def register():
    """Register Shader Generator classes and attach scene properties."""
    bpy.utils.register_class(ColorRampColor)
    bpy.utils.register_class(ShaderGeneratorSettings)
    bpy.types.Scene.custom_colorramp = CollectionProperty(type=ColorRampColor)
    bpy.types.Scene.shader_generator_settings = bpy.props.PointerProperty(type=ShaderGeneratorSettings)
    bpy.utils.register_class(COLORRAMP_OT_add_color)
    bpy.utils.register_class(COLORRAMP_OT_remove_color)
    bpy.utils.register_class(COLORRAMP_OT_save_custom)
    bpy.utils.register_class(COLORRAMP_OT_load_custom)
    bpy.utils.register_class(COLORRAMP_OT_import_json)
    bpy.utils.register_class(MATERIAL_OT_create_shader)
    bpy.utils.register_class(MATERIAL_PT_shader_generator)


def unregister():
    """Unregister classes and remove scene properties."""
    if hasattr(bpy.types.Scene, 'shader_generator_settings'):
        del bpy.types.Scene.shader_generator_settings
    if hasattr(bpy.types.Scene, 'custom_colorramp'):
        del bpy.types.Scene.custom_colorramp
    bpy.utils.unregister_class(ColorRampColor)
    bpy.utils.unregister_class(ShaderGeneratorSettings)
    bpy.utils.unregister_class(COLORRAMP_OT_add_color)
    bpy.utils.unregister_class(COLORRAMP_OT_remove_color)
    bpy.utils.unregister_class(COLORRAMP_OT_save_custom)
    bpy.utils.unregister_class(COLORRAMP_OT_load_custom)
    bpy.utils.unregister_class(COLORRAMP_OT_import_json)
    bpy.utils.unregister_class(MATERIAL_OT_create_shader)
    bpy.utils.unregister_class(MATERIAL_PT_shader_generator)


if __name__ == "__main__":
    register()
