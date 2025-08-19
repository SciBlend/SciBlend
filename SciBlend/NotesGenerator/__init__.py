import bpy
from . import operators
from . import panels
from . import properties


def register():
    operators.register()
    panels.register()
    properties.register()


def unregister():
    panels.unregister()
    operators.unregister()
    properties.unregister()

if __name__ == "__main__":
    register()