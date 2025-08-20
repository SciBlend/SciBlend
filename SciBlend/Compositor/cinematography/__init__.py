from . import render_settings
from . import camera_manager
from . import cinema_formats
from .render_settings_group import CinematographySettings
import bpy


def register():
    render_settings.register()
    camera_manager.register()
    cinema_formats.register()
    bpy.utils.register_class(CinematographySettings)
    bpy.types.Scene.cinematography_settings = bpy.props.PointerProperty(type=CinematographySettings)


def unregister():
    if hasattr(bpy.types.Scene, "cinematography_settings"):
        del bpy.types.Scene.cinematography_settings
    bpy.utils.unregister_class(CinematographySettings)
    cinema_formats.unregister()
    camera_manager.unregister()
    render_settings.unregister()