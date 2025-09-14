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
	return sum(values) / float(len(values))


def rebuild_contour_surface_for_settings(context, settings) -> Object | None:
	"""Rebuild or create a contour surface object by detecting isosurface crossings using crinkle clip semantics."""
	src_obj = getattr(settings, 'target_object', None)
	if not src_obj or getattr(src_obj, 'type', None) != 'MESH':
		return None
	attr_name = getattr(settings, 'attribute', 'NONE')
	if not attr_name or attr_name == 'NONE':
		return None
	iso_value = float(getattr(settings, 'iso_value', 0.0))
	domain = getattr(settings, 'domain', 'CELL')
	agg = getattr(settings, 'aggregator', 'MEAN')
	model = get_model(src_obj.name) or ensure_model_for_object(context, src_obj)
	if not model or not getattr(model, 'cells', None) or not getattr(model, 'faces', None):
		return None

	cell_scalar = {}
	if domain == 'CELL':
		for cell in model.cells:
			val_tuple = getattr(cell, 'attributes', {}).get(attr_name)
			if val_tuple is None:
				continue
			try:
				cell_scalar[cell] = float(val_tuple[0]) if isinstance(val_tuple, (list, tuple)) else float(val_tuple)
			except Exception:
				continue
	else:
		mesh_attr = None
		try:
			mesh_attr = src_obj.data.attributes.get(attr_name)
		except Exception:
			mesh_attr = None
		if not mesh_attr or getattr(mesh_attr, 'domain', '') not in {'POINT', 'VERTEX'} or getattr(mesh_attr, 'data_type', '') != 'FLOAT':
			return None
		vals = []
		try:
			vals = [0.0] * len(src_obj.data.vertices)
			mesh_attr.data.foreach_get('value', vals)
		except Exception:
			vals = []
		if not vals:
			return None
		for cell in model.cells:
			pv = []
			for face in getattr(cell, 'faces', []) or []:
				for v in getattr(face, 'vertices', []) or []:
					idx = getattr(v, 'blender_v_index', -1)
					if 0 <= idx < len(vals):
						pv.append(float(vals[idx]))
			if not pv:
				continue
			cell_scalar[cell] = _aggregate(pv, agg)

	faces_to_create = []
	owner_cells = []
	for face in getattr(model, 'faces', []):
		owner = getattr(face, 'owner', None)
		neigh = getattr(face, 'neighbour', None)
		if not owner or not neigh:
			continue
		vo = cell_scalar.get(owner, None)
		vn = cell_scalar.get(neigh, None)
		if vo is None or vn is None:
			continue
		if (vo < iso_value and vn > iso_value) or (vo > iso_value and vn < iso_value) or vo == iso_value or vn == iso_value:
			verts_for_owner = getattr(face, 'get_vertices_for_cell', lambda c: None)(owner)
			if not verts_for_owner:
				continue
			indices = [getattr(v, 'blender_v_index', -1) for v in verts_for_owner]
			if any(i < 0 for i in indices):
				continue
			faces_to_create.append(indices)
			owner_cells.append(owner)

	blender_vertices = [getattr(v, 'co', (0.0, 0.0, 0.0)) for v in getattr(model, 'vertices', [])]
	if not blender_vertices or not faces_to_create:
		return None

	out_name = f"{src_obj.name}_ContourLive"
	mesh = bpy.data.meshes.get(out_name)
	if mesh is None:
		mesh = bpy.data.meshes.new(out_name)
	obj = bpy.data.objects.get(out_name)
	if obj is None:
		obj = bpy.data.objects.new(out_name, mesh)
		try:
			colls = src_obj.users_collection
			(colls[0] if colls else context.collection).objects.link(obj)
		except Exception:
			context.collection.objects.link(obj)

	mesh.clear_geometry()
	mesh.from_pydata(blender_vertices, [], faces_to_create)
	mesh.update()

	# Copy point attributes if sizes match
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

	# Bake cell attributes to FACE domain for selected faces (owner side)
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


class FILTERS_OT_build_contour_surface(bpy.types.Operator):
	"""Build or update a contour (isosurface) using crinkle clip semantics."""
	bl_idname = "filters.build_contour_surface"
	bl_label = "Build Contour Surface"
	bl_options = {'REGISTER', 'UNDO'}

	info: StringProperty(name="Info", default="")

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		settings = getattr(context.scene, 'filters_contour_settings', None)
		if not settings:
			self.report({'ERROR'}, "Contour settings not available")
			return {'CANCELLED'}
		obj = rebuild_contour_surface_for_settings(context, settings)
		if obj is None:
			self.report({'WARNING'}, "No geometry created (check attribute and iso value)")
			return {'CANCELLED'}
		self.report({'INFO'}, f"Contour surface updated: {obj.name}")
		return {'FINISHED'}


__all__ = ["FILTERS_OT_build_contour_surface", "rebuild_contour_surface_for_settings"] 