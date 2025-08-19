from . import render_settings
from . import camera_manager
from . import cinema_formats

def register():
    render_settings.register()
    camera_manager.register()
    cinema_formats.register()

def unregister():
    cinema_formats.unregister()
    camera_manager.unregister()
    render_settings.unregister()