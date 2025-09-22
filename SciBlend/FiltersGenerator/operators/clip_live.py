import bpy
from bpy.types import Object, Mesh
from bpy.props import StringProperty
from mathutils import Vector
from ...operators.utils.volume_mesh_data import get_model
from ..utils.on_demand_loader import ensure_model_for_object


PLANE_NAME_SUFFIX = "_ClipPlane"


def _ensure_clip_plane_for_object(context, obj: Object) -> Object:
	"""Ensure a plane object exists, aligned to the object's bounding box center and oriented to +Z normal."""
	name = f"{obj.name}{PLANE_NAME_SUFFIX}"
	plane = bpy.data.objects.get(name)
	if plane and getattr(plane, 'type', None) == 'MESH':
		return plane
	mesh = bpy.data.meshes.new(f"{name}_Mesh")
	verts = [(-1.0, -1.0, 0.0), (1.0, -1.0, 0.0), (1.0, 1.0, 0.0), (-1.0, 1.0, 0.0)]
	faces = [(0, 1, 2, 3)]
	mesh.from_pydata(verts, [], faces)
	mesh.update()
	plane = bpy.data.objects.new(name, mesh)
	colls = obj.users_collection
	if colls:
		colls[0].objects.link(plane)
	else:
		context.collection.objects.link(plane)
	# position plane at bbox center; scale to bbox diagonal length
	bb = [Vector(v) for v in obj.bound_box]
	center_local = (Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb))) +
					 Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))) * 0.5
	plane.matrix_world = obj.matrix_world.copy()
	plane.location = obj.matrix_world @ center_local
	plane.scale = Vector((1.0, 1.0, 1.0))
	plane.display_type = 'WIRE'
	plane.show_in_front = True
	return plane


def rebuild_clip_surface_for_settings(context, settings) -> Object | None:
	"""Rebuild or create a clipped mesh: keep whole mesh on the chosen side plus crinkle boundary faces."""
	src_obj = getattr(settings, 'target_object', None)
	plane = getattr(settings, 'plane_object', None)
	side = getattr(settings, 'side', 'POSITIVE')
	if not src_obj or getattr(src_obj, 'type', None) != 'MESH':
		return None
	if not plane or getattr(plane, 'type', None) != 'MESH':
		plane = _ensure_clip_plane_for_object(context, src_obj)
		try:
			settings.plane_object = plane
		except Exception:
			pass
	
	# plane world normal and point
	mw_p = plane.matrix_world
	normal = Vector((0.0, 0.0, 1.0))
	normal = (mw_p.to_3x3() @ normal).normalized()
	point_on_plane = mw_p.translation.copy()

	model = get_model(src_obj.name) or ensure_model_for_object(context, src_obj)
	if not model or not getattr(model, 'cells', None) or not getattr(model, 'faces', None) or not getattr(model, 'vertices', None):
		return None

	def signed_distance_world(loc: Vector) -> float:
		return (loc - point_on_plane).dot(normal)

	# Precompute cell centers in world space and sidedness
	cell_center_ws = {}
	cell_keep_side = {}
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
		d = signed_distance_world(cent_world)
		cell_keep_side[cell] = (d >= 0.0) if side == 'POSITIVE' else (d <= 0.0)

	# Collect faces: keep faces of kept-side cells that either
	# - are boundary faces, or
	# - neighbor is a non-kept-side cell (i.e., plane boundary),
	# to ensure a closed visible half. This is effectively crinkle closure + outer shell.
	faces_to_create = []
	owner_cells = []
	added = set()
	for face in getattr(model, 'faces', []):
		owner = getattr(face, 'owner', None)
		neighbour = getattr(face, 'neighbour', None)
		# Boundary face: keep if owner is on kept side
		if neighbour is None:
			if owner is None:
				continue
			if cell_keep_side.get(owner, False):
				verts = getattr(face, 'get_vertices_for_cell', lambda c: None)(owner)
				if not verts:
					continue
				indices = tuple(getattr(v, 'blender_v_index', -1) for v in verts)
				if any(i < 0 for i in indices) or indices in added:
					continue
				faces_to_create.append(list(indices))
				owner_cells.append(owner)
				added.add(indices)
			continue
		# Internal face: if exactly one side is kept, add oriented to the kept cell
		owner_kept = cell_keep_side.get(owner, False)
		neigh_kept = cell_keep_side.get(neighbour, False)
		if owner_kept == neigh_kept:
			continue
		kept_cell = owner if owner_kept else neighbour
		verts = getattr(face, 'get_vertices_for_cell', lambda c: None)(kept_cell)
		if not verts:
			continue
		indices = tuple(getattr(v, 'blender_v_index', -1) for v in verts)
		if any(i < 0 for i in indices) or indices in added:
			continue
		faces_to_create.append(list(indices))
		owner_cells.append(kept_cell)
		added.add(indices)

	blender_vertices = [getattr(v, 'co', (0.0, 0.0, 0.0)) for v in getattr(model, 'vertices', [])]
	if not blender_vertices or not faces_to_create:
		return None

	out_name = f"{src_obj.name}_ClipLive"
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

	# Bake cell attributes to FACE domain
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

	# hide plane after update
	try:
		plane.hide_set(True)
		plane.hide_render = True
	except Exception:
		pass

	obj.display_type = 'TEXTURED'
	obj.hide_set(False)
	obj.hide_render = False

	return obj


class FILTERS_OT_clip_ensure_plane(bpy.types.Operator):
	"""Create or ensure a clip plane object aligned to the target mesh bounding box."""
	bl_idname = "filters.clip_ensure_plane"
	bl_label = "Ensure Clip Plane"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		settings = getattr(context.scene, 'filters_clip_settings', None)
		if not settings or not getattr(settings, 'target_object', None):
			self.report({'ERROR'}, "Select a Domain Mesh")
			return {'CANCELLED'}
		plane = _ensure_clip_plane_for_object(context, settings.target_object)
		try:
			settings.plane_object = plane
		except Exception:
			pass
		self.report({'INFO'}, f"Clip plane ready: {plane.name}")
		return {'FINISHED'}


class FILTERS_OT_build_clip_surface(bpy.types.Operator):
	"""Build or update a clipped mesh keeping one side of the plane, plus crinkle closure; hides plane afterward."""
	bl_idname = "filters.build_clip_surface"
	bl_label = "Build Clip Surface"
	bl_options = {'REGISTER', 'UNDO'}

	info: StringProperty(name="Info", default="")

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		settings = getattr(context.scene, 'filters_clip_settings', None)
		if not settings:
			self.report({'ERROR'}, "Clip settings not available")
			return {'CANCELLED'}
		obj = rebuild_clip_surface_for_settings(context, settings)
		if obj is None:
			self.report({'WARNING'}, "No geometry created (position/orientation plane)")
			return {'CANCELLED'}
		self.report({'INFO'}, f"Clip surface updated: {obj.name}")
		return {'FINISHED'}


__all__ = [
	"FILTERS_OT_clip_ensure_plane",
	"FILTERS_OT_build_clip_surface",
	"rebuild_clip_surface_for_settings",
] 