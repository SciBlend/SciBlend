import bpy
from bpy.props import PointerProperty, StringProperty, EnumProperty


def _calc_var_items(self, context):
	items = []
	obj = getattr(self, 'target_object', None)
	domain = getattr(self, 'domain', 'POINT')
	if obj and getattr(obj, 'type', None) == 'MESH' and getattr(obj, 'data', None):
		attrs = getattr(obj.data, 'attributes', None)
		if attrs:
			for a in attrs:
				if getattr(a, 'data_type', '') != 'FLOAT':
					continue
				dom = getattr(a, 'domain', '')
				if (domain == 'POINT' and dom in {'POINT', 'VERTEX'}) or (domain == 'FACE' and dom == 'FACE'):
					items.append((a.name, a.name, f"{dom} attribute"))
	if not items:
		items = [("", "(no attributes)", "")]
	return items


def _calc_func_items(self, context):
	funcs = [
		('abs', 'abs(x)', 'Absolute value'),
		('sqrt', 'sqrt(x)', 'Square root'),
		('pow', 'pow(x,y)', 'Power'),
		('sin', 'sin(x)', 'Sine'),
		('cos', 'cos(x)', 'Cosine'),
		('tan', 'tan(x)', 'Tangent'),
		('exp', 'exp(x)', 'Exponential'),
		('log', 'log(x)', 'Natural log'),
		('min', 'MIN', 'Use Aggregator MIN (not a function token)'),
		('max', 'MAX', 'Use Aggregator MAX (not a function token)'),
		('pi', 'pi', 'Constant PI'),
		('e', 'e', 'Constant E'),
	]
	return funcs


class FiltersCalculatorSettings(bpy.types.PropertyGroup):
	"""Settings for the Calculator filter to compute new scalar attributes from existing ones."""
	
	domain: EnumProperty(name="Domain", items=(('POINT', "Point/Vertex", "Compute per-vertex"), ('FACE', "Face", "Compute per-face")), default='POINT')
	target_object: PointerProperty(type=bpy.types.Object, name="Domain Mesh")
	output_name: StringProperty(name="Output Name", default="calc_result")
	expression: StringProperty(name="Expression", default="", description="Use sanitized variable names (auto-append from the list)")
	selected_variable: StringProperty(name="Variable", default="")
	variable_enum: EnumProperty(name="Attributes", items=_calc_var_items)
	function_enum: EnumProperty(name="Functions", items=_calc_func_items)


def register():
	bpy.utils.register_class(FiltersCalculatorSettings)


def unregister():
	bpy.utils.unregister_class(FiltersCalculatorSettings) 