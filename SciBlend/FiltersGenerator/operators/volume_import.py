import bpy
import os
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator


class FILTERS_OT_volume_import_vdb_sequence(Operator, ImportHelper):
    bl_idname = "filters.volume_import_vdb_sequence"
    bl_label = "Import VDB Sequence"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".vdb"
    filter_glob: bpy.props.StringProperty(default="*.vdb", options={'HIDDEN'})

    files: bpy.props.CollectionProperty(name="File Path", type=bpy.types.PropertyGroup)

    def execute(self, context):
        directory = os.path.dirname(self.filepath)
        files = [f.name for f in self.files] or [os.path.basename(self.filepath)]
        if not files:
            self.report({'ERROR'}, "No VDB files selected")
            return {'CANCELLED'}
        
        settings = context.scene.filters_volume_settings
        is_first_volume = len(settings.volume_items) == 0
        
        filepaths_to_import = [os.path.join(directory, n) for n in files]
        
        volumes_to_remove = []
        for vol in bpy.data.volumes:
            if hasattr(vol, 'filepath') and vol.filepath in filepaths_to_import:
                volumes_to_remove.append(vol)
        
        for vol in volumes_to_remove:
            try:
                print(f"Removing cached volume datablock: {vol.name} (filepath: {vol.filepath})")
                bpy.data.volumes.remove(vol)
            except Exception as e:
                print(f"Could not remove volume {vol.name}: {e}")
        
        if is_first_volume:
            self._configure_viewport_for_volumes(context)
        
        try:
            bpy.ops.object.volume_import(directory=directory, files=[{"name": n} for n in files])
        except Exception as e:
            self.report({'ERROR'}, f"Volume import failed: {e}")
            return {'CANCELLED'}

        obj = context.active_object
        if not obj or obj.type != 'VOLUME':
            self.report({'ERROR'}, "Imported object not found or not a Volume")
            return {'CANCELLED'}
        
        collection_name = f"{obj.name}_Collection"
        new_collection = bpy.data.collections.get(collection_name)
        if not new_collection:
            new_collection = bpy.data.collections.new(collection_name)
            context.scene.collection.children.link(new_collection)
        
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        
        new_collection.objects.link(obj)

        settings = context.scene.filters_volume_settings
        settings.last_import_dir = directory
        
        from ..properties.volume_item import _UPDATING_NODES
        from ..properties import volume_item
        
        original_flag = volume_item._UPDATING_NODES
        volume_item._UPDATING_NODES = True
        
        try:
            item = settings.volume_items.add()
            item.name = obj.name
            item.volume_object = obj
            item.last_import_dir = directory
            
            try:
                item.last_import_files.clear()
                for n in files:
                    file_item = item.last_import_files.add()
                    file_item.name = n
            except Exception:
                pass
            
            if obj.data and hasattr(obj.data, 'grids'):
                try:
                    grids = list(obj.data.grids)
                    if grids:
                        item.grid_name = grids[0].name
                except Exception:
                    pass
            
            settings.volume_items_index = len(settings.volume_items) - 1
        finally:
            volume_item._UPDATING_NODES = original_flag
        
        from .volume_update import ensure_volume_material_for_object
        ensure_volume_material_for_object(context, obj, item)
        
        if obj.data and hasattr(obj.data, 'render'):
            try:
                obj.data.render.space = 'OBJECT'
                print(f"Set volume render space to OBJECT for {obj.name}")
            except Exception as e:
                print(f"Could not set volume render space: {e}")
            
            try:
                obj.data.render.clipping = 0.0
                print(f"Set volume render clipping to 0 for {obj.name}")
            except Exception as e:
                print(f"Could not set volume render clipping: {e}")

        return {'FINISHED'}
    
    def _configure_viewport_for_volumes(self, context):
        """
        Configure viewport and scene settings for optimal volume rendering on first import.
        """
        try:
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.clip_end = 100000.0
                            print(f"Set viewport clip_end to 100000m")
                            break
        except Exception as e:
            print(f"Could not set viewport clip_end: {e}")
        
        try:
            context.scene.eevee.use_volume_custom_range = False
            print("Disabled EEVEE custom volume range")
        except Exception as e:
            print(f"Could not disable custom volume range: {e}")
        
        try:
            context.scene.eevee.volumetric_tile_size = '1'
            print("Set EEVEE volumetric tile size to 1:1")
        except Exception as e:
            print(f"Could not set volumetric tile size: {e}")


def register():
    bpy.utils.register_class(FILTERS_OT_volume_import_vdb_sequence)


def unregister():
    bpy.utils.unregister_class(FILTERS_OT_volume_import_vdb_sequence)