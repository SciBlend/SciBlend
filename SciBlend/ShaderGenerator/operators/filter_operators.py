import bpy
from bpy.types import Operator


def _trigger_filter_rebuild(context, settings):
    """Rebuild the filter Geometry Nodes after reordering rules.
    
    Parameters
    ----------
    context : bpy.types.Context
        Blender context.
    settings : ShaderGeneratorSettings
        The shader generator settings.
    """
    if not settings.collection_shaders:
        return
    
    if settings.active_collection_index < 0 or settings.active_collection_index >= len(settings.collection_shaders):
        return
    
    item = settings.collection_shaders[settings.active_collection_index]
    coll = bpy.data.collections.get(item.collection_name)
    if not coll:
        return
    
    mat = None
    if item.material_name:
        mat = bpy.data.materials.get(item.material_name)
    
    filters_data = []
    if hasattr(settings, 'attribute_filters'):
        for f in settings.attribute_filters:
            filters_data.append({
                'attribute': f.attribute_name,
                'operator': f.operator,
                'value': f.value,
                'enabled': f.enabled,
                'display_mode': f.display_mode,
                'display_color': tuple(f.display_color),
                'display_material': f.display_material,
            })
    
    from ..utils.filter_geometry_nodes import build_filter_geometry_nodes
    build_filter_geometry_nodes(
        coll,
        mat,
        filters_data,
        settings.enable_filters,
    )


class SHADER_OT_add_filter(Operator):
    """Add a new attribute filter rule to the list."""
    bl_idname = "shader.add_filter"
    bl_label = "Add Filter"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Add a new filter item to the attribute_filters collection."""
        settings = context.scene.shader_generator_settings
        if not settings:
            self.report({'ERROR'}, "Shader Generator settings not found")
            return {'CANCELLED'}
        
        new_filter = settings.attribute_filters.add()
        new_filter.operator = 'EQUAL'
        new_filter.value = 0.0
        new_filter.enabled = True
        
        settings.active_filter_index = len(settings.attribute_filters) - 1
        
        return {'FINISHED'}


class SHADER_OT_remove_filter(Operator):
    """Remove the selected attribute filter rule from the list."""
    bl_idname = "shader.remove_filter"
    bl_label = "Remove Filter"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Remove the active filter item from the attribute_filters collection."""
        settings = context.scene.shader_generator_settings
        if not settings:
            self.report({'ERROR'}, "Shader Generator settings not found")
            return {'CANCELLED'}
        
        if settings.active_filter_index < 0 or settings.active_filter_index >= len(settings.attribute_filters):
            self.report({'WARNING'}, "No filter selected")
            return {'CANCELLED'}
        
        settings.attribute_filters.remove(settings.active_filter_index)
        
        if settings.active_filter_index >= len(settings.attribute_filters):
            settings.active_filter_index = len(settings.attribute_filters) - 1
        
        _trigger_filter_rebuild(context, settings)
        
        return {'FINISHED'}


class SHADER_OT_move_filter_up(Operator):
    """Move the active filter rule up in the priority list."""
    bl_idname = "shader.move_filter_up"
    bl_label = "Move Filter Up"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Swap the active filter with the one above it."""
        settings = context.scene.shader_generator_settings
        if not settings:
            self.report({'ERROR'}, "Shader Generator settings not found")
            return {'CANCELLED'}
        
        idx = settings.active_filter_index
        if idx <= 0 or idx >= len(settings.attribute_filters):
            return {'CANCELLED'}
        
        settings.attribute_filters.move(idx, idx - 1)
        settings.active_filter_index = idx - 1
        
        _trigger_filter_rebuild(context, settings)
        
        return {'FINISHED'}


class SHADER_OT_move_filter_down(Operator):
    """Move the active filter rule down in the priority list."""
    bl_idname = "shader.move_filter_down"
    bl_label = "Move Filter Down"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Swap the active filter with the one below it."""
        settings = context.scene.shader_generator_settings
        if not settings:
            self.report({'ERROR'}, "Shader Generator settings not found")
            return {'CANCELLED'}
        
        idx = settings.active_filter_index
        if idx < 0 or idx >= len(settings.attribute_filters) - 1:
            return {'CANCELLED'}
        
        settings.attribute_filters.move(idx, idx + 1)
        settings.active_filter_index = idx + 1
        
        _trigger_filter_rebuild(context, settings)
        
        return {'FINISHED'}
