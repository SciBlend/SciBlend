import bpy
from bpy.types import Operator


class SHADER_OT_refresh_attributes(Operator):
    """Refresh the attribute cache for the active object or all objects"""
    bl_idname = "shader.refresh_attributes"
    bl_label = "Refresh Attributes"
    bl_options = {'REGISTER', 'UNDO'}

    all_objects: bpy.props.BoolProperty(
        name="All Objects",
        description="Clear attribute cache for all objects instead of just the active one",
        default=False,
    )

    def execute(self, context):
        from ..utils.attributes import clear_attribute_cache
        
        if self.all_objects:
            clear_attribute_cache()
            self.report({'INFO'}, "Cleared attribute cache for all objects")
        else:
            obj = getattr(context, 'active_object', None)
            if obj:
                clear_attribute_cache(obj.name)
                self.report({'INFO'}, f"Cleared attribute cache for {obj.name}")
            else:
                self.report({'WARNING'}, "No active object")
                return {'CANCELLED'}
        
        # Force UI update
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        
        return {'FINISHED'}

