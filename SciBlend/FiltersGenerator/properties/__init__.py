from .emitter_settings import FiltersEmitterSettings
from .volume_settings import VolumeRenderingSettings
from .threshold_settings import FiltersThresholdSettings
from .contour_settings import FiltersContourSettings
from .clip_settings import FiltersClipSettings
from .slice_settings import FiltersSliceSettings
import bpy


def register():
    bpy.utils.register_class(FiltersEmitterSettings)
    bpy.utils.register_class(VolumeRenderingSettings)
    bpy.utils.register_class(FiltersThresholdSettings)
    bpy.utils.register_class(FiltersContourSettings)
    bpy.utils.register_class(FiltersClipSettings)
    bpy.utils.register_class(FiltersSliceSettings)


def unregister():
    bpy.utils.unregister_class(FiltersSliceSettings)
    bpy.utils.unregister_class(FiltersClipSettings)
    bpy.utils.unregister_class(FiltersContourSettings)
    bpy.utils.unregister_class(FiltersThresholdSettings)
    bpy.utils.unregister_class(VolumeRenderingSettings)
    bpy.utils.unregister_class(FiltersEmitterSettings) 