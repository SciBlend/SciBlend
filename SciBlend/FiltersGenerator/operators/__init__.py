from .create_emitter import FILTERS_OT_create_emitter
from .place_emitter import FILTERS_OT_place_emitter
from .generate_streamline import FILTERS_OT_generate_streamline
from .volume_import import FILTERS_OT_volume_import_vdb_sequence
from .volume_update import FILTERS_OT_volume_update_material, FILTERS_OT_volume_compute_range
import bpy


def register():
    bpy.utils.register_class(FILTERS_OT_create_emitter)
    bpy.utils.register_class(FILTERS_OT_place_emitter)
    bpy.utils.register_class(FILTERS_OT_generate_streamline)
    bpy.utils.register_class(FILTERS_OT_volume_import_vdb_sequence)
    bpy.utils.register_class(FILTERS_OT_volume_update_material)
    bpy.utils.register_class(FILTERS_OT_volume_compute_range)


def unregister():
    bpy.utils.unregister_class(FILTERS_OT_volume_compute_range)
    bpy.utils.unregister_class(FILTERS_OT_volume_update_material)
    bpy.utils.unregister_class(FILTERS_OT_volume_import_vdb_sequence)
    bpy.utils.unregister_class(FILTERS_OT_generate_streamline)
    bpy.utils.unregister_class(FILTERS_OT_place_emitter)
    bpy.utils.unregister_class(FILTERS_OT_create_emitter) 