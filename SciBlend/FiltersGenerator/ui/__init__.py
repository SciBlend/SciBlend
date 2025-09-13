from .main_panel import (
    FILTERSGENERATOR_PT_main_panel,
    FILTERSGENERATOR_PT_stream_tracers,
    FILTERSGENERATOR_PT_volume_filter,
    FILTERSGENERATOR_PT_geometry_filters,
)
import bpy


def register():
    bpy.utils.register_class(FILTERSGENERATOR_PT_main_panel)
    bpy.utils.register_class(FILTERSGENERATOR_PT_stream_tracers)
    bpy.utils.register_class(FILTERSGENERATOR_PT_volume_filter)
    bpy.utils.register_class(FILTERSGENERATOR_PT_geometry_filters)


def unregister():
    bpy.utils.unregister_class(FILTERSGENERATOR_PT_geometry_filters)
    bpy.utils.unregister_class(FILTERSGENERATOR_PT_volume_filter)
    bpy.utils.unregister_class(FILTERSGENERATOR_PT_stream_tracers)
    bpy.utils.unregister_class(FILTERSGENERATOR_PT_main_panel) 