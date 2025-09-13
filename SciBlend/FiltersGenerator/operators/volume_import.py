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
        try:
            bpy.ops.object.volume_import(directory=directory, files=[{"name": n} for n in files])
        except Exception as e:
            self.report({'ERROR'}, f"Volume import failed: {e}")
            return {'CANCELLED'}

        obj = context.active_object
        if not obj or obj.type != 'VOLUME':
            self.report({'ERROR'}, "Imported object not found or not a Volume")
            return {'CANCELLED'}

        s = context.scene.filters_volume_settings
        s.volume_object = obj
        s.last_import_dir = directory
        try:
            s.last_import_files.clear()
            for n in files:
                item = s.last_import_files.add()
                item.name = n
        except Exception:
            pass

        from .volume_update import ensure_volume_material_for_object
        ensure_volume_material_for_object(context, obj, s)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(FILTERS_OT_volume_import_vdb_sequence)


def unregister():
    bpy.utils.unregister_class(FILTERS_OT_volume_import_vdb_sequence)