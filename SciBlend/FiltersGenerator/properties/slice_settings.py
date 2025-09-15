import bpy
from bpy.props import PointerProperty


class FiltersSliceSettings(bpy.types.PropertyGroup):
	"""Settings for slicing a volumetric mesh by a plane, generating a crinkle surface only."""
	
	target_object: PointerProperty(type=bpy.types.Object, name="Domain Mesh")
	plane_object: PointerProperty(type=bpy.types.Object, name="Slice Plane")


def register():
	bpy.utils.register_class(FiltersSliceSettings)


def unregister():
	bpy.utils.unregister_class(FiltersSliceSettings) 