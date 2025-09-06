from .create_emitter import FILTERS_OT_create_emitter
from .place_emitter import FILTERS_OT_place_emitter
from .generate_streamline import FILTERS_OT_generate_streamline
import bpy


def register():
    bpy.utils.register_class(FILTERS_OT_create_emitter)
    bpy.utils.register_class(FILTERS_OT_place_emitter)
    bpy.utils.register_class(FILTERS_OT_generate_streamline)


def unregister():
    bpy.utils.unregister_class(FILTERS_OT_generate_streamline)
    bpy.utils.unregister_class(FILTERS_OT_place_emitter)
    bpy.utils.unregister_class(FILTERS_OT_create_emitter) 