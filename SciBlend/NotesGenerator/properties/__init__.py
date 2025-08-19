import bpy
from .annotation_properties import AnnotationProperties


def register():
    try:
        bpy.utils.register_class(AnnotationProperties)
        bpy.types.Scene.annotation_properties = bpy.props.PointerProperty(
            type=AnnotationProperties)
    except Exception as e:
        print(f"Error registering properties: {str(e)}")


def unregister():
    try:
        del bpy.types.Scene.annotation_properties
        bpy.utils.unregister_class(AnnotationProperties)
    except Exception as e:
        print(f"Error unregistering properties: {str(e)}")
