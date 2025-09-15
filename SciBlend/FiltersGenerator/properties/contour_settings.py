import bpy
from bpy.props import PointerProperty, FloatProperty, BoolProperty, EnumProperty
from ...operators.utils.volume_mesh_data import get_model
from ..utils.on_demand_loader import ensure_model_for_object


_DEF_AGG = (
	('MEAN', "Mean", "Average of point values in the cell"),
	('MIN', "Min", "Minimum of point values in the cell"),
	('MAX', "Max", "Maximum of point values in the cell"),
)


def _point_attribute_items(self, context):
	items = []
	obj = getattr(self, 'target_object', None)
	if obj and getattr(obj, 'type', None) == 'MESH' and getattr(obj, 'data', None):
		attrs = getattr(obj.data, 'attributes', None)
		if attrs:
			for a in attrs:
				domain = getattr(a, 'domain', "")
				if getattr(a, 'data_type', "") == 'FLOAT' and domain in {'POINT', 'VERTEX'}:
					items.append((a.name, a.name, "Point/Vertex attribute"))
	if not items:
		items = [("NONE", "(no point attributes)", "")]
	return items


def _cell_attribute_items(self, context):
	"""Enumerate available attributes depending on domain selection."""
	domain = getattr(self, 'domain', 'CELL')
	obj = getattr(self, 'target_object', None)
	if not obj or getattr(obj, 'type', None) != 'MESH':
		return [("NONE", "(select a volumetric mesh)", "")]
	if domain == 'POINT':
		return _point_attribute_items(self, context)
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
	
	domain: EnumProperty(name="Domain", items=(('CELL', "Cell", "Use cell data"), ('POINT', "Point", "Use point/vertex data")), default='CELL')
	aggregator: EnumProperty(name="Aggregator", description="How to reduce point values to a cell scalar", items=_DEF_AGG, default='MEAN')
	target_object: PointerProperty(type=bpy.types.Object, name="Domain Mesh")
	attribute: EnumProperty(name="Attribute", items=_cell_attribute_items)
	iso_value: FloatProperty(name="Iso Value", default=0.0)


def register():
	bpy.utils.register_class(FiltersContourSettings)


def unregister():
	bpy.utils.unregister_class(FiltersContourSettings) 