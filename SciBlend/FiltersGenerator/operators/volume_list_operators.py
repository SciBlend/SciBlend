import bpy
from bpy.types import Operator


class FILTERS_OT_volume_item_add(Operator):
    """
    Add a new volume item to the list.
    """
    bl_idname = "filters.volume_item_add"
    bl_label = "Add Volume"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        settings = context.scene.filters_volume_settings
        item = settings.volume_items.add()
        
        count = len(settings.volume_items)
        item.name = f"Volume {count}"
        
        settings.volume_items_index = len(settings.volume_items) - 1
        
        return {'FINISHED'}


class FILTERS_OT_volume_item_remove(Operator):
    """
    Remove the active volume item from the list.
    """
    bl_idname = "filters.volume_item_remove"
    bl_label = "Remove Volume"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        settings = context.scene.filters_volume_settings
        return len(settings.volume_items) > 0
    
    def execute(self, context):
        settings = context.scene.filters_volume_settings
        idx = settings.volume_items_index
        
        if 0 <= idx < len(settings.volume_items):
            settings.volume_items.remove(idx)
            
            if settings.volume_items_index >= len(settings.volume_items):
                settings.volume_items_index = max(0, len(settings.volume_items) - 1)
        
        return {'FINISHED'}


class FILTERS_OT_volume_item_move_up(Operator):
    """
    Move the active volume item up in the list.
    """
    bl_idname = "filters.volume_item_move_up"
    bl_label = "Move Volume Up"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        settings = context.scene.filters_volume_settings
        return settings.volume_items_index > 0
    
    def execute(self, context):
        settings = context.scene.filters_volume_settings
        idx = settings.volume_items_index
        
        settings.volume_items.move(idx, idx - 1)
        settings.volume_items_index = idx - 1
        
        return {'FINISHED'}


class FILTERS_OT_volume_item_move_down(Operator):
    """
    Move the active volume item down in the list.
    """
    bl_idname = "filters.volume_item_move_down"
    bl_label = "Move Volume Down"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        settings = context.scene.filters_volume_settings
        return settings.volume_items_index < len(settings.volume_items) - 1
    
    def execute(self, context):
        settings = context.scene.filters_volume_settings
        idx = settings.volume_items_index
        
        settings.volume_items.move(idx, idx + 1)
        settings.volume_items_index = idx + 1
        
        return {'FINISHED'}


class FILTERS_OT_volume_regenerate_material(Operator):
    """
    Regenerate the volume material from scratch to update node group structure.
    """
    bl_idname = "filters.volume_regenerate_material"
    bl_label = "Regenerate Material"
    bl_description = "Force regenerate the volume material with updated node group"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, 'filters_volume_settings', None)
        if not settings or not settings.volume_items:
            return False
        if settings.volume_items_index >= len(settings.volume_items):
            return False
        item = settings.volume_items[settings.volume_items_index]
        return item.volume_object and item.volume_object.type == 'VOLUME'
    
    def execute(self, context):
        settings = context.scene.filters_volume_settings
        item = settings.volume_items[settings.volume_items_index]
        
        if not item.volume_object or item.volume_object.type != 'VOLUME':
            self.report({'ERROR'}, "No valid volume object")
            return {'CANCELLED'}
        
        old_node_group = bpy.data.node_groups.get("SciBlend_Volume_Density")
        if old_node_group:
            bpy.data.node_groups.remove(old_node_group)
            self.report({'INFO'}, "Removed old node group")
        
        from .volume_update import ensure_volume_material_for_object
        
        try:
            mat = ensure_volume_material_for_object(context, item.volume_object, item)
            self.report({'INFO'}, f"Material regenerated for {item.volume_object.name}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to regenerate material: {e}")
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(FILTERS_OT_volume_item_add)
    bpy.utils.register_class(FILTERS_OT_volume_item_remove)
    bpy.utils.register_class(FILTERS_OT_volume_item_move_up)
    bpy.utils.register_class(FILTERS_OT_volume_item_move_down)
    bpy.utils.register_class(FILTERS_OT_volume_regenerate_material)


def unregister():
    bpy.utils.unregister_class(FILTERS_OT_volume_regenerate_material)
    bpy.utils.unregister_class(FILTERS_OT_volume_item_move_down)
    bpy.utils.unregister_class(FILTERS_OT_volume_item_move_up)
    bpy.utils.unregister_class(FILTERS_OT_volume_item_remove)
    bpy.utils.unregister_class(FILTERS_OT_volume_item_add)

