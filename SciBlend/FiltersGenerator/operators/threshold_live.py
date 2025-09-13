import bpy
from bpy.types import Object, Mesh
from bpy.props import StringProperty
from ...operators.utils.volume_mesh_data import get_model


def rebuild_threshold_surface_for_settings(context, settings) -> Object | None:
	"""Rebuild or create the live threshold surface object based on the provided settings.

	This function uses the in-memory volume model to compute the boundary faces of all cells
	whose selected attribute lies within [min_value, max_value]. The resulting surface is written
	to a persistent child object so the original mesh remains intact.
	"""
	src_obj = getattr(settings, 'target_object', None)
	if not src_obj or getattr(src_obj, 'type', None) != 'MESH':
		return None
	attr_name = getattr(settings, 'attribute', 'NONE')
	if not attr_name or attr_name == 'NONE':
		return None
	min_v = float(getattr(settings, 'min_value', 0.0))
	max_v = float(getattr(settings, 'max_value', 1.0))
	model = get_model(src_obj.name)
	if not model or not getattr(model, 'cells', None):
		return None

	passing = set()
	for cell in model.cells:
		val_tuple = getattr(cell, 'attributes', {}).get(attr_name)
		if val_tuple is None:
			continue
		try:
			val = float(val_tuple[0]) if isinstance(val_tuple, (list, tuple)) else float(val_tuple)
		except Exception:
			continue
		if min_v <= val <= max_v:
			passing.add(cell)

	faces_to_create = []
	owner_cells = []
	if passing:
		for cell in passing:
			for face in getattr(cell, 'faces', []):
				other = getattr(face, 'neighbour', None) if getattr(face, 'owner', None) == cell else getattr(face, 'owner', None)
				if getattr(face, 'is_boundary', lambda: False)() or other not in passing:
					face_verts = getattr(face, 'get_vertices_for_cell', lambda c: None)(cell)
					if not face_verts:
						continue
					indices = [getattr(v, 'blender_v_index', -1) for v in face_verts]
					if any(i < 0 for i in indices):
						continue
					faces_to_create.append(indices)
					owner_cells.append(cell)

	blender_vertices = [getattr(v, 'co', (0.0, 0.0, 0.0)) for v in getattr(model, 'vertices', [])]
	if not blender_vertices or not faces_to_create:
		return None

	out_name = f"{src_obj.name}_ThresholdLive"
	mesh = bpy.data.meshes.get(out_name)
	if mesh is None:
		mesh = bpy.data.meshes.new(out_name)
	obj = bpy.data.objects.get(out_name)
	if obj is None:
		obj = bpy.data.objects.new(out_name, mesh)
		try:
			# link alongside source object
			colls = src_obj.users_collection
			(colls[0] if colls else context.collection).objects.link(obj)
		except Exception:
			context.collection.objects.link(obj)

	# update geometry
	mesh.clear_geometry()
	mesh.from_pydata(blender_vertices, [], faces_to_create)
	mesh.update()

	# copy point attributes if sizes match
	src_mesh: Mesh = src_obj.data
	try:
		for src_attr in src_mesh.attributes:
			if getattr(src_attr, 'domain', '') != 'POINT' or getattr(src_attr, 'data_type', '') != 'FLOAT':
				continue
			if src_attr.data and len(src_attr.data) == len(blender_vertices):
				try:
					if src_attr.name in mesh.attributes:
						mesh.attributes.remove(mesh.attributes[src_attr.name])
				except Exception:
					pass
				dst = mesh.attributes.new(name=src_attr.name, type='FLOAT', domain='POINT')
				buf = [0.0] * len(blender_vertices)
				src_attr.data.foreach_get('value', buf)
				dst.data.foreach_set('value', buf)
	except Exception:
		pass

	# bake cell attributes to FACE domain on the output
	if owner_cells:
		all_attr = set()
		for c in owner_cells:
			for k in getattr(c, 'attributes', {}).keys():
				all_attr.add(k)
		for name in sorted(all_attr):
			values = [0.0] * len(faces_to_create)
			for i, c in enumerate(owner_cells):
				val = getattr(c, 'attributes', {}).get(name)
				if val is None:
					continue
				try:
					values[i] = float(val[0]) if isinstance(val, (list, tuple)) else float(val)
				except Exception:
					values[i] = 0.0
			try:
				if f"cell_{name}" in mesh.attributes:
					mesh.attributes.remove(mesh.attributes[f"cell_{name}"])
			except Exception:
				pass
			attr = mesh.attributes.new(name=f"cell_{name}", type='FLOAT', domain='FACE')
			attr.data.foreach_set('value', values)

	obj.display_type = 'TEXTURED'
	obj.hide_viewport = False
	obj.hide_render = False

	return obj


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