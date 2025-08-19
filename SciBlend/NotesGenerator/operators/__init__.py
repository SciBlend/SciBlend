from .add_annotation import NOTESGENERATOR_OT_add_annotation
import bpy

def register():
    bpy.utils.register_class(NOTESGENERATOR_OT_add_annotation)

def unregister():
    bpy.utils.unregister_class(NOTESGENERATOR_OT_add_annotation)