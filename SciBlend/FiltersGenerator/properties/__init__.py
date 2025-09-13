from .emitter_settings import FiltersEmitterSettings
from .volume_settings import VolumeRenderingSettings
import bpy


def register():
    bpy.utils.register_class(FiltersEmitterSettings)
    bpy.utils.register_class(VolumeRenderingSettings)


def unregister():
    bpy.utils.unregister_class(VolumeRenderingSettings)
    bpy.utils.unregister_class(FiltersEmitterSettings) 