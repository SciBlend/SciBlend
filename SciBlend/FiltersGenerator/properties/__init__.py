from .emitter_settings import FiltersEmitterSettings
import bpy


def register():
    bpy.utils.register_class(FiltersEmitterSettings)


def unregister():
    bpy.utils.unregister_class(FiltersEmitterSettings) 