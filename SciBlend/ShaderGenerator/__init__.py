import bpy
import logging
from bpy.props import CollectionProperty

from .properties.colorramp import ColorRampColor
from .properties.collection_shader_item import CollectionShaderItem
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
from .operators.refresh_attributes import SHADER_OT_refresh_attributes
from .operators.collection_operators import (
    SHADER_OT_refresh_collections,
    SHADER_OT_remove_shader,
    SHADER_OT_apply_changes,
)
from .ui.panel import MATERIAL_PT_shader_generator
from .ui.collection_list import SHADER_UL_collection_list

logger = logging.getLogger(__name__)

__all__ = (
    'ColorRampColor',
    'CollectionShaderItem',
    'ShaderGeneratorSettings',
    'COLORRAMP_OT_add_color',
    'COLORRAMP_OT_remove_color',
    'COLORRAMP_OT_save_custom',
    'COLORRAMP_OT_load_custom',
    'COLORRAMP_OT_import_json',
    'MATERIAL_OT_create_shader',
    'SHADER_OT_refresh_attributes',
    'SHADER_OT_refresh_collections',
    'SHADER_OT_remove_shader',
    'SHADER_OT_apply_changes',
    'MATERIAL_PT_shader_generator',
    'SHADER_UL_collection_list',
    'create_colormap_material',
)


def register():
    """Register Shader Generator classes and attach scene properties."""
    bpy.utils.register_class(ColorRampColor)
    bpy.utils.register_class(CollectionShaderItem)
    bpy.utils.register_class(ShaderGeneratorSettings)
    bpy.types.Scene.custom_colorramp = CollectionProperty(type=ColorRampColor)
    bpy.types.Scene.shader_generator_settings = bpy.props.PointerProperty(type=ShaderGeneratorSettings)
    bpy.utils.register_class(COLORRAMP_OT_add_color)
    bpy.utils.register_class(COLORRAMP_OT_remove_color)
    bpy.utils.register_class(COLORRAMP_OT_save_custom)
    bpy.utils.register_class(COLORRAMP_OT_load_custom)
    bpy.utils.register_class(COLORRAMP_OT_import_json)
    bpy.utils.register_class(MATERIAL_OT_create_shader)
    bpy.utils.register_class(SHADER_OT_refresh_attributes)
    bpy.utils.register_class(SHADER_OT_refresh_collections)
    bpy.utils.register_class(SHADER_OT_remove_shader)
    bpy.utils.register_class(SHADER_OT_apply_changes)
    bpy.utils.register_class(SHADER_UL_collection_list)
    bpy.utils.register_class(MATERIAL_PT_shader_generator)
    
    from .utils.attributes import _cleanup_attribute_cache
    if _cleanup_attribute_cache not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_cleanup_attribute_cache)


def unregister():
    """Unregister classes and remove scene properties."""
    from .utils.attributes import _cleanup_attribute_cache, clear_attribute_cache
    if _cleanup_attribute_cache in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_cleanup_attribute_cache)
    clear_attribute_cache() 
    
    bpy.utils.unregister_class(MATERIAL_PT_shader_generator)
    bpy.utils.unregister_class(SHADER_UL_collection_list)
    bpy.utils.unregister_class(SHADER_OT_apply_changes)
    bpy.utils.unregister_class(SHADER_OT_remove_shader)
    bpy.utils.unregister_class(SHADER_OT_refresh_collections)
    bpy.utils.unregister_class(SHADER_OT_refresh_attributes)
    bpy.utils.unregister_class(MATERIAL_OT_create_shader)
    bpy.utils.unregister_class(COLORRAMP_OT_import_json)
    bpy.utils.unregister_class(COLORRAMP_OT_load_custom)
    bpy.utils.unregister_class(COLORRAMP_OT_save_custom)
    bpy.utils.unregister_class(COLORRAMP_OT_remove_color)
    bpy.utils.unregister_class(COLORRAMP_OT_add_color)
    
    if hasattr(bpy.types.Scene, 'shader_generator_settings'):
        del bpy.types.Scene.shader_generator_settings
    if hasattr(bpy.types.Scene, 'custom_colorramp'):
        del bpy.types.Scene.custom_colorramp
    
    bpy.utils.unregister_class(ShaderGeneratorSettings)
    bpy.utils.unregister_class(CollectionShaderItem)
    bpy.utils.unregister_class(ColorRampColor)


if __name__ == "__main__":
    register()
