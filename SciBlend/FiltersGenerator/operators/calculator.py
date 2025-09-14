import bpy
import math
from bpy.types import Operator
from bpy.props import StringProperty


_SAFE_FUNCS = {
	'abs': abs,
	'pow': pow,
	'round': round,
	'floor': math.floor,
	'ceil': math.ceil,
	'sqrt': math.sqrt,
	'exp': math.exp,
	'log': math.log,
	'sin': math.sin,
	'cos': math.cos,
	'tan': math.tan,
	'asin': math.asin,
	'acos': math.acos,
	'atan': math.atan,
	'atan2': math.atan2,
	'pi': math.pi,
	'e': math.e,
}


class FILTERS_OT_calculator_apply(Operator):
	"""Compute a new scalar attribute from existing attributes by evaluating a Python expression."""
	bl_idname = "filters.calculator_apply"
	bl_label = "Apply Calculator"
	bl_options = {'REGISTER', 'UNDO'}

	info: StringProperty(name="Info", default="")

	def execute(self, context):
		settings = getattr(context.scene, 'filters_calculator_settings', None)
		if not settings:
			self.report({'ERROR'}, "Calculator settings not available")
			return {'CANCELLED'}
		obj = getattr(settings, 'target_object', None)
		if not obj or getattr(obj, 'type', None) != 'MESH' or not getattr(obj, 'data', None):
			self.report({'ERROR'}, "Select a mesh object")
			return {'CANCELLED'}
		domain = getattr(settings, 'domain', 'POINT')
		output_name = (getattr(settings, 'output_name', '') or 'calc_result').strip()
		if not output_name:
			self.report({'ERROR'}, "Output name is empty")
			return {'CANCELLED'}
		expression = (getattr(settings, 'expression', '') or '').strip()
		if not expression:
			self.report({'ERROR'}, "Expression is empty")
			return {'CANCELLED'}

		mesh = obj.data
		attrs = getattr(mesh, 'attributes', None)
		if not attrs:
			self.report({'ERROR'}, "Mesh has no attributes")
			return {'CANCELLED'}
		variables = {}
		if domain == 'POINT':
			for a in attrs:
				if getattr(a, 'data_type', '') != 'FLOAT' or getattr(a, 'domain', '') not in {'POINT', 'VERTEX'}:
					continue
				vals = [0.0] * len(mesh.vertices)
				try:
					a.data.foreach_get('value', vals)
				except Exception:
					continue
				var_name = _sanitize(a.name)
				variables[var_name] = vals
		elif domain == 'FACE':
			for a in attrs:
				if getattr(a, 'data_type', '') != 'FLOAT' or getattr(a, 'domain', '') != 'FACE':
					continue
				vals = [0.0] * len(mesh.polygons)
				try:
					a.data.foreach_get('value', vals)
				except Exception:
					continue
				var_name = _sanitize(a.name)
				variables[var_name] = vals
		if not variables:
			self.report({'ERROR'}, "No attributes found for selected domain")
			return {'CANCELLED'}

		try:
			length = len(mesh.vertices) if domain == 'POINT' else len(mesh.polygons)
			result = [0.0] * length
			code = compile(expression, '<calculator>', 'eval')
			local_ns = {**_SAFE_FUNCS}
			for i in range(length):
				for k, arr in variables.items():
					local_ns[k] = arr[i]
				result[i] = float(eval(code, {'__builtins__': {}}, local_ns))
		except Exception as e:
			self.report({'ERROR'}, f"Expression error: {e}")
			return {'CANCELLED'}

		try:
			if output_name in attrs:
				attrs.remove(output_name)
		except Exception:
			pass
		try:
			domain_type = 'POINT' if domain == 'POINT' else 'FACE'
			out = attrs.new(name=output_name, type='FLOAT', domain=domain_type)
			if domain == 'POINT' and len(result) == len(mesh.vertices):
				out.data.foreach_set('value', result)
			elif domain == 'FACE' and len(result) == len(mesh.polygons):
				out.data.foreach_set('value', result)
			else:
				self.report({'WARNING'}, "Result length mismatch; attribute created empty")
		except Exception as e:
			self.report({'ERROR'}, f"Failed to write attribute: {e}")
			return {'CANCELLED'}

		self.report({'INFO'}, f"Calculator wrote '{output_name}' on {domain}")
		return {'FINISHED'}


class FILTERS_OT_calculator_append_var(Operator):
	"""Append the selected variable to the expression (sanitized)."""
	bl_idname = "filters.calculator_append_var"
	bl_label = "Append Variable"
	bl_options = {'INTERNAL'}

	def execute(self, context):
		settings = getattr(context.scene, 'filters_calculator_settings', None)
		if not settings:
			return {'CANCELLED'}
		name = (getattr(settings, 'selected_variable', '') or '').strip()
		if not name:
			return {'CANCELLED'}
		san = _sanitize(name)
		expr = getattr(settings, 'expression', '') or ''
		if expr and not expr.endswith((' ', '+', '-', '*', '/', '(', '=')):
			expr += ' '
		expr += san
		settings.expression = expr
		return {'FINISHED'}


class FILTERS_OT_calculator_append_attr(Operator):
	"""Append the selected attribute (from enum) to the expression."""
	bl_idname = "filters.calculator_append_attr"
	bl_label = "Append Attribute"
	bl_options = {'INTERNAL'}

	def execute(self, context):
		settings = getattr(context.scene, 'filters_calculator_settings', None)
		if not settings:
			return {'CANCELLED'}
		name = (getattr(settings, 'variable_enum', '') or '').strip()
		if not name:
			return {'CANCELLED'}
		san = _sanitize(name)
		expr = getattr(settings, 'expression', '') or ''
		if expr and not expr.endswith((' ', '+', '-', '*', '/', '(', '=')):
			expr += ' '
		expr += san
		settings.expression = expr
		return {'FINISHED'}


class FILTERS_OT_calculator_append_func(Operator):
	"""Append the selected function token to the expression."""
	bl_idname = "filters.calculator_append_func"
	bl_label = "Append Function"
	bl_options = {'INTERNAL'}

	def execute(self, context):
		settings = getattr(context.scene, 'filters_calculator_settings', None)
		if not settings:
			return {'CANCELLED'}
		tok = (getattr(settings, 'function_enum', '') or '').strip()
		if not tok:
			return {'CANCELLED'}
		expr = getattr(settings, 'expression', '') or ''
		if expr and not expr.endswith((' ', '+', '-', '*', '/', '(', '=')):
			expr += ' '
		expr += tok
		settings.expression = expr
		return {'FINISHED'}


def _sanitize(name: str) -> str:
	return ''.join(c if c.isalnum() or c == '_' else '_' for c in name)


__all__ = [
	"FILTERS_OT_calculator_apply",
	"FILTERS_OT_calculator_append_var",
	"FILTERS_OT_calculator_append_attr",
	"FILTERS_OT_calculator_append_func",
] 