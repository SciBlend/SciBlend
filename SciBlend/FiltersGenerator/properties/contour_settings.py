import bpy
from bpy.props import PointerProperty, FloatProperty, BoolProperty, EnumProperty
from ...operators.utils.volume_mesh_data import get_model
from ..utils.on_demand_loader import ensure_model_for_object


def _cell_attribute_items(self, context):
	"""Enumerate available cell attributes from the registered volume model of the selected object.

	Returns a list of (identifier, name, description) for EnumProperty.
	If no object or model is available, returns a placeholder entry.
	"""
	obj = getattr(self, 'target_object', None)
	if not obj or getattr(obj, 'type', None) != 'MESH':
		return [("NONE", "(select a volumetric mesh)", "")]
	model = get_model(obj.name) or ensure_model_for_object(context, obj)
	if not model or not getattr(model, 'cells', None):
		return [("NONE", "(no volume data)", "")] 
	try:
		first = model.cells[0]
		attrs = list(getattr(first, 'attributes', {}).keys())
	except Exception:
		attrs = []
	if not attrs:
		return [("NONE", "(no cell attributes)", "")]
	items = [(name, name, f"Cell attribute '{name}'") for name in attrs]
	return items


class FiltersContourSettings(bpy.types.PropertyGroup):
	"""Settings for building an isosurface contour from a volumetric mesh using crinkle clip semantics."""
	
	target_object: PointerProperty(type=bpy.types.Object, name="Domain Mesh")
	attribute: EnumProperty(name="Attribute", items=_cell_attribute_items)
	iso_value: FloatProperty(name="Iso Value", default=0.0)


def register():
	bpy.utils.register_class(FiltersContourSettings)


def unregister():
	bpy.utils.unregister_class(FiltersContourSettings) 