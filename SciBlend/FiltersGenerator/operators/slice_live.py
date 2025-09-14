import bpy
from bpy.types import Object, Mesh
from bpy.props import StringProperty
from mathutils import Vector
from ...operators.utils.volume_mesh_data import get_model
from ..utils.on_demand_loader import ensure_model_for_object
from .clip_live import _ensure_clip_plane_for_object


def rebuild_slice_surface_for_settings(context, settings) -> Object | None:
	"""Create a crinkle slice surface using the provided plane and domain mesh."""
	src_obj = getattr(settings, 'target_object', None)
	plane = getattr(settings, 'plane_object', None)
	if not src_obj or getattr(src_obj, 'type', None) != 'MESH':
		return None
	if not plane or getattr(plane, 'type', None) != 'MESH':
		plane = _ensure_clip_plane_for_object(context, src_obj)
		try:
			settings.plane_object = plane
		except Exception:
			pass

	mw_p = plane.matrix_world
	normal = Vector((0.0, 0.0, 1.0))
	normal = (mw_p.to_3x3() @ normal).normalized()
	point_on_plane = mw_p.translation.copy()

	model = get_model(src_obj.name) or ensure_model_for_object(context, src_obj)
	if not model or not getattr(model, 'cells', None) or not getattr(model, 'faces', None):
		return None

	def signed_distance_world(loc: Vector) -> float:
		return (loc - point_on_plane).dot(normal)

	cell_center_ws = {}
	for cell in model.cells:
		coords = []
		for face in getattr(cell, 'faces', []) or []:
			for v in getattr(face, 'vertices', []) or []:
				coords.append(v.co)
		if not coords:
			continue
		cent_local = Vector((0.0, 0.0, 0.0))
		for c in coords:
			cent_local += Vector(c)
		cent_local /= max(1, len(coords))
		cent_world = src_obj.matrix_world @ cent_local
		cell_center_ws[cell] = cent_world

	faces_to_create = []
	owner_cells = []
	for face in getattr(model, 'faces', []):
		owner = getattr(face, 'owner', None)
		neighbour = getattr(face, 'neighbour', None)
		if not owner or not neighbour:
			continue
		p_owner = cell_center_ws.get(owner)
		p_neigh = cell_center_ws.get(neighbour)
		if p_owner is None or p_neigh is None:
			continue
		d0 = signed_distance_world(p_owner)
		d1 = signed_distance_world(p_neigh)
		if d0 == 0.0 or d1 == 0.0 or (d0 < 0.0 and d1 > 0.0) or (d0 > 0.0 and d1 < 0.0):
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

	out_name = f"{src_obj.name}_SliceLive"
	mesh = bpy.data.meshes.get(out_name)
	if mesh is None:
		mesh = bpy.data.meshes.new(out_name)
	obj = bpy.data.objects.get(out_name)
	if obj is None:
		obj = bpy.data.objects.new(out_name, mesh)
		colls = src_obj.users_collection
		if colls:
			colls[0].objects.link(obj)
		else:
			context.collection.objects.link(obj)

	mesh.clear_geometry()
	mesh.from_pydata(blender_vertices, [], faces_to_create)
	mesh.update()

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

	try:
		plane.hide_viewport = True
		plane.hide_render = True
	except Exception:
		pass

	obj.display_type = 'TEXTURED'
	obj.hide_viewport = False
	obj.hide_render = False

	return obj


class FILTERS_OT_slice_ensure_plane(bpy.types.Operator):
	"""Create or ensure a slice plane object aligned to the target mesh bounding box."""
	bl_idname = "filters.slice_ensure_plane"
	bl_label = "Ensure Slice Plane"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		settings = getattr(context.scene, 'filters_slice_settings', None)
		if not settings or not getattr(settings, 'target_object', None):
			self.report({'ERROR'}, "Select a Domain Mesh")
			return {'CANCELLED'}
		plane = _ensure_clip_plane_for_object(context, settings.target_object)
		try:
			settings.plane_object = plane
		except Exception:
			pass
		self.report({'INFO'}, f"Slice plane ready: {plane.name}")
		return {'FINISHED'}


class FILTERS_OT_build_slice_surface(bpy.types.Operator):
	"""Build or update a slice surface using crinkle semantics; hides the plane after update."""
	bl_idname = "filters.build_slice_surface"
	bl_label = "Build Slice Surface"
	bl_options = {'REGISTER', 'UNDO'}

	info: StringProperty(name="Info", default="")

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		settings = getattr(context.scene, 'filters_slice_settings', None)
		if not settings:
			self.report({'ERROR'}, "Slice settings not available")
			return {'CANCELLED'}
		obj = rebuild_slice_surface_for_settings(context, settings)
		if obj is None:
			self.report({'WARNING'}, "No geometry created (position/orientation plane)")
			return {'CANCELLED'}
		self.report({'INFO'}, f"Slice surface updated: {obj.name}")
		return {'FINISHED'}


__all__ = [
	"FILTERS_OT_slice_ensure_plane",
	"FILTERS_OT_build_slice_surface",
	"rebuild_slice_surface_for_settings",
] 