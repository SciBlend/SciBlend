import bpy
from bpy.props import PointerProperty, EnumProperty


class FiltersClipSettings(bpy.types.PropertyGroup):
	"""Settings for clipping a volumetric mesh by a plane, using crinkle semantics for faces crossing the plane."""
	
	target_object: PointerProperty(type=bpy.types.Object, name="Domain Mesh")
	plane_object: PointerProperty(type=bpy.types.Object, name="Clip Plane")
	side: EnumProperty(
		name="Side",
		description="Side of the plane to keep visible",
		items=(
			('POSITIVE', "Positive", "Keep side with positive signed distance"),
			('NEGATIVE', "Negative", "Keep side with negative signed distance"),
		),
		default='POSITIVE'
	)


def register():
	bpy.utils.register_class(FiltersClipSettings)


def unregister():
	bpy.utils.unregister_class(FiltersClipSettings) 