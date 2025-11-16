import bpy
import logging
from bpy.types import Operator
from ..utils.material_updater import get_material_from_collection

logger = logging.getLogger(__name__)


def rebuild_collection_list(context):
    """Rebuild the collection shader tracking list from the scene.
    
    Parameters
    ----------
    context : bpy.types.Context
        Blender context.
    """
    settings = context.scene.shader_generator_settings
    if not settings:
        return
        
    settings.collection_shaders.clear()
    
    for coll in bpy.data.collections:
        item = settings.collection_shaders.add()
        item.collection_name = coll.name
        
        mat = get_material_from_collection(coll)
        if mat:
            item.material_name = mat.name
            item.is_shader_generator = mat.get('sciblend_colormap') is not None
        else:
            item.material_name = ""
            item.is_shader_generator = False
    
    if len(settings.collection_shaders) > 0 and settings.active_collection_index == -1:
        settings.active_collection_index = 0


class SHADER_OT_refresh_collections(Operator):
    """Refresh the collection list from the scene."""
    bl_idname = "shader.refresh_collections"
    bl_label = "Refresh Collections"
    bl_description = "Refresh the list of collections"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """Execute the refresh operation.
        
        Parameters
        ----------
        context : bpy.types.Context
            Blender context.
            
        Returns
        -------
        set
            Operator return status.
        """
        rebuild_collection_list(context)
        self.report({'INFO'}, "Collection list refreshed")
        return {'FINISHED'}


class SHADER_OT_remove_shader(Operator):
    """Remove Shader Generator material from the selected collection."""
    bl_idname = "shader.remove_shader"
    bl_label = "Remove Shader"
    bl_description = "Remove the Shader Generator material from this collection"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """Execute the remove operation.
        
        Parameters
        ----------
        context : bpy.types.Context
            Blender context.
            
        Returns
        -------
        set
            Operator return status.
        """
        settings = context.scene.shader_generator_settings
        if not settings:
            self.report({'ERROR'}, "Shader Generator settings not found")
            return {'CANCELLED'}
            
        if not settings.collection_shaders:
            self.report({'ERROR'}, "No collections in list")
            return {'CANCELLED'}
            
        if settings.active_collection_index < 0 or settings.active_collection_index >= len(settings.collection_shaders):
            self.report({'ERROR'}, "No collection selected")
            return {'CANCELLED'}
            
        item = settings.collection_shaders[settings.active_collection_index]
        coll = bpy.data.collections.get(item.collection_name)
        
        if not coll:
            self.report({'ERROR'}, f"Collection '{item.collection_name}' not found")
            return {'CANCELLED'}
            
        removed_count = 0
        for obj in coll.objects:
            if obj.type == 'MESH' and obj.data.materials:
                for i, mat in enumerate(obj.data.materials):
                    if mat and mat.get('sciblend_colormap') is not None:
                        obj.data.materials[i] = None
                        removed_count += 1
                        
        item.material_name = ""
        item.is_shader_generator = False
        
        self.report({'INFO'}, f"Removed Shader Generator material from {removed_count} objects")
        logger.info("Removed shader from collection %s", item.collection_name)
        return {'FINISHED'}


class SHADER_OT_apply_changes(Operator):
    """Apply all current shader settings to the selected collection's material."""
    bl_idname = "shader.apply_changes"
    bl_label = "Apply Changes"
    bl_description = "Apply all shader settings changes to the collection's material"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """Execute the apply operation.
        
        Parameters
        ----------
        context : bpy.types.Context
            Blender context.
            
        Returns
        -------
        set
            Operator return status.
        """
        self.report({'INFO'}, "Changes applied (real-time updates are already active)")
        return {'FINISHED'}

