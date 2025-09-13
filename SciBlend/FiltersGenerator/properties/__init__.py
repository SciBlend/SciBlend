from .emitter_settings import FiltersEmitterSettings
from .volume_settings import VolumeRenderingSettings
from .threshold_settings import FiltersThresholdSettings
import bpy


def register():
    bpy.utils.register_class(FiltersEmitterSettings)
    bpy.utils.register_class(VolumeRenderingSettings)
    bpy.utils.register_class(FiltersThresholdSettings)


def unregister():
    bpy.utils.unregister_class(FiltersThresholdSettings)
    bpy.utils.unregister_class(VolumeRenderingSettings)
    bpy.utils.unregister_class(FiltersEmitterSettings) 