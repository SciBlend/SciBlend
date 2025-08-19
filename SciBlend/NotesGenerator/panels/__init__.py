from .main_panel import NOTESGENERATOR_PT_main_panel
import bpy
print(f"bpy imported in panels/__init__.py: {bpy}")


def register():
    bpy.utils.register_class(NOTESGENERATOR_PT_main_panel)


def unregister():
    bpy.utils.unregister_class(NOTESGENERATOR_PT_main_panel)
