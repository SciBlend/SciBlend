import bpy
from bpy.types import Object, Mesh
from bpy.props import StringProperty
from ...operators.utils.volume_mesh_data import get_model
from ..utils.on_demand_loader import ensure_model_for_object


def _aggregate(values, mode: str) -> float:
	if not values:
		return 0.0
	if mode == 'MIN':
		return min(values)
	if mode == 'MAX':
		return max(values)
	# default MEAN
	return sum(values) / float(len(values))


def rebuild_threshold_surface_for_settings(context, settings) -> Object | None:
	"""Rebuild or create the live threshold surface object based on the provided settings."""
	src_obj = getattr(settings, 'target_object', None)
	if not src_obj or getattr(src_obj, 'type', None) != 'MESH':
		return None
	attr_name = getattr(settings, 'attribute', 'NONE')
	if not attr_name or attr_name == 'NONE':
		return None
	min_v = float(getattr(settings, 'min_value', 0.0))
	max_v = float(getattr(settings, 'max_value', 1.0))
	domain = getattr(settings, 'domain', 'CELL')
	agg = getattr(settings, 'aggregator', 'MEAN')
	model = get_model(src_obj.name) or ensure_model_for_object(context, src_obj)
	if not model or not getattr(model, 'cells', None):
		return None

	passing_cells = set()
	if domain == 'CELL':
		for cell in model.cells:
			val_tuple = getattr(cell, 'attributes', {}).get(attr_name)
			if val_tuple is None:
				continue
			try:
				value = float(val_tuple[0]) if isinstance(val_tuple, (list, tuple)) else float(val_tuple)
			except Exception:
				continue
			if min_v <= value <= max_v:
				passing_cells.add(cell)
	else:
		# POINT domain: reduce by cell's incident point values using the mesh attribute
		mesh_attr = None
		try:
			mesh_attr = src_obj.data.attributes.get(attr_name)
		except Exception:
			mesh_attr = None
		if not mesh_attr or getattr(mesh_attr, 'domain', '') != 'POINT' or getattr(mesh_attr, 'data_type', '') != 'FLOAT':
			return None
		point_values = []
		try:
			point_values = [0.0] * len(src_obj.data.vertices)
			mesh_attr.data.foreach_get('value', point_values)
		except Exception:
			point_values = []
		if not point_values:
			return None
		for cell in model.cells:
			cell_point_vals = []
			for face in getattr(cell, 'faces', []) or []:
				for v in getattr(face, 'vertices', []) or []:
					idx = getattr(v, 'blender_v_index', -1)
					if 0 <= idx < len(point_values):
						cell_point_vals.append(float(point_values[idx]))
			if not cell_point_vals:
				continue
			value = _aggregate(cell_point_vals, agg)
			if min_v <= value <= max_v:
				passing_cells.add(cell)

	if not passing_cells:
		return None

	blender_faces_to_create = []
	face_owner_cells = []
	for cell in passing_cells:
		for face in getattr(cell, 'faces', []) or []:
			other = face.neighbour if face.owner == cell else face.owner
			if getattr(face, 'is_boundary', lambda: False)() or other not in passing_cells:
				face_verts = face.get_vertices_for_cell(cell)
				if not face_verts:
					continue
				face_indices = [v.blender_v_index for v in face_verts]
				blender_faces_to_create.append(face_indices)
				face_owner_cells.append(cell)

	blender_vertices = [v.co for v in model.vertices]
	new_mesh_name = f"{src_obj.name}_Threshold"
	new_mesh = bpy.data.meshes.new(new_mesh_name)
	new_obj = bpy.data.objects.new(new_mesh_name, new_mesh)
	new_mesh.from_pydata(blender_vertices, [], blender_faces_to_create)
	new_mesh.update()

	src_mesh = src_obj.data
	try:
		for src_attr in src_mesh.attributes:
			if getattr(src_attr, 'domain', '') != 'POINT':
				continue
			if getattr(src_attr, 'data_type', '') != 'FLOAT':
				continue
			if src_attr.data and len(src_attr.data) == len(blender_vertices):
				dst = new_mesh.attributes.new(name=src_attr.name, type='FLOAT', domain='POINT')
				buf = [0.0] * len(blender_vertices)
				src_attr.data.foreach_get('value', buf)
				dst.data.foreach_set('value', buf)
	except Exception:
		pass

	if face_owner_cells:
		all_attr_names = set()
		for cell in face_owner_cells:
			for k in cell.attributes.keys():
				all_attr_names.add(k)
		for attr_name in sorted(all_attr_names):
			values = [0.0] * len(blender_faces_to_create)
			for face_idx, cell in enumerate(face_owner_cells):
				val = cell.attributes.get(attr_name)
				if val is None:
					continue
				try:
					if isinstance(val, (list, tuple)):
						values[face_idx] = float(val[0]) if len(val) > 0 else 0.0
					else:
						values[face_idx] = float(val)
				except Exception:
					values[face_idx] = 0.0
			attr = new_mesh.attributes.new(name=f"cell_{attr_name}", type='FLOAT', domain='FACE')
			attr.data.foreach_set('value', values)

	context.collection.objects.link(new_obj)
	context.view_layer.objects.active = new_obj
	new_obj.select_set(True)
	try:
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.remove_doubles(threshold=0.0001)
		bpy.ops.mesh.delete_loose()
	finally:
		bpy.ops.object.mode_set(mode='OBJECT')

	src_obj.hide_viewport = True
	src_obj.hide_render = True

	return new_obj


class FILTERS_OT_build_threshold_surface(bpy.types.Operator):
	"""Build or update a live threshold surface. The source mesh is not modified."""
	bl_idname = "filters.build_threshold_surface"
	bl_label = "Build Threshold Surface"
	bl_options = {'REGISTER', 'UNDO'}

	info: StringProperty(name="Info", default="")

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		settings = getattr(context.scene, 'filters_threshold_settings', None)
		if not settings:
			self.report({'ERROR'}, "Threshold settings not available")
			return {'CANCELLED'}
		obj = rebuild_threshold_surface_for_settings(context, settings)
		if obj is None:
			self.report({'WARNING'}, "No geometry created (check attribute and range)")
			return {'CANCELLED'}
		self.report({'INFO'}, f"Threshold surface updated: {obj.name}")
		return {'FINISHED'}


__all__ = ["FILTERS_OT_build_threshold_surface", "rebuild_threshold_surface_for_settings"] 