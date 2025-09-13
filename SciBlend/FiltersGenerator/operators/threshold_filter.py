import bpy
from bpy.props import FloatProperty, EnumProperty
from ...operators.utils.volume_mesh_data import get_model


def get_cell_attributes(self, context):
	"""Populate EnumProperty choices from cell attributes in the active object's volume model."""
	items = []
	obj = context.active_object
	if not obj or obj.type != 'MESH':
		return [("NONE", "N/A", "Select a volumetric mesh")]
	volume_model = get_model(obj.name)
	if not volume_model or not getattr(volume_model, 'cells', None):
		return [("NONE", "N/A", "No volume data found for this object")]
	first_cell = volume_model.cells[0]
	for attr_name in first_cell.attributes.keys():
		items.append((attr_name, attr_name, f"Cell Attribute: {attr_name}"))
	if not items:
		return [("NONE", "No Attributes", "No cell attributes found in the data model")]
	return items


class FILTERS_OT_apply_threshold(bpy.types.Operator):
	"""Generate a new mesh containing only faces of cells whose selected attribute falls within a given range."""
	bl_idname = "filters.apply_volume_threshold"
	bl_label = "Apply Volume Threshold"
	bl_description = "Generates a new mesh from cells within the specified attribute range"
	bl_options = {'REGISTER', 'UNDO'}

	attribute: EnumProperty(
		name="Attribute",
		description="Cell attribute to filter by",
		items=get_cell_attributes
	)

	min_value: FloatProperty(
		name="Minimum",
		description="The minimum value for the threshold range",
		default=0.0
	)

	max_value: FloatProperty(
		name="Maximum",
		description="The maximum value for the threshold range",
		default=1.0
	)

	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return obj and obj.type == 'MESH' and get_model(obj.name) is not None

	def invoke(self, context, event):
		"""Prefill min/max with actual range from the selected attribute to improve usability."""
		obj = context.active_object
		volume_model = get_model(obj.name)
		if getattr(self, 'attribute', 'NONE') != 'NONE' and volume_model:
			all_values = []
			for cell in volume_model.cells:
				val = cell.attributes.get(self.attribute)
				if val is None:
					continue
				try:
					value = float(val[0]) if isinstance(val, (list, tuple)) else float(val)
				except Exception:
					continue
				all_values.append(value)
			if all_values:
				self.min_value = min(all_values)
				self.max_value = max(all_values)
		return context.window_manager.invoke_props_dialog(self)

	def execute(self, context):
		"""Create a filtered surface mesh comprising boundary faces of passing cells, and copy attributes."""
		active_obj = context.active_object
		volume_model = get_model(active_obj.name)
		if not volume_model or self.attribute == 'NONE':
			self.report({'WARNING'}, "No volume data or attribute selected.")
			return {'CANCELLED'}

		passing_cells = set()
		for cell in volume_model.cells:
			val_tuple = cell.attributes.get(self.attribute)
			if val_tuple is None:
				continue
			try:
				value = float(val_tuple[0]) if isinstance(val_tuple, (list, tuple)) else float(val_tuple)
			except Exception:
				continue
			if self.min_value <= value <= self.max_value:
				passing_cells.add(cell)

		if not passing_cells:
			self.report({'INFO'}, "No cells passed the threshold filter.")
			return {'FINISHED'}

		blender_faces_to_create = []
		face_owner_cells = []
		for cell in passing_cells:
			for face in cell.faces:
				other = face.neighbour if face.owner == cell else face.owner
				if face.is_boundary() or other not in passing_cells:
					face_verts = face.get_vertices_for_cell(cell)
					if not face_verts:
						continue
					face_indices = [v.blender_v_index for v in face_verts]
					blender_faces_to_create.append(face_indices)
					face_owner_cells.append(cell)

		blender_vertices = [v.co for v in volume_model.vertices]
		new_mesh_name = f"{active_obj.name}_Threshold"
		new_mesh = bpy.data.meshes.new(new_mesh_name)
		new_obj = bpy.data.objects.new(new_mesh_name, new_mesh)
		new_mesh.from_pydata(blender_vertices, [], blender_faces_to_create)
		new_mesh.update()

		src_mesh = active_obj.data
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

		active_obj.hide_viewport = True
		active_obj.hide_render = True

		self.report({'INFO'}, f"Created new mesh with {len(passing_cells)} cells passing the threshold.")
		return {'FINISHED'}


__all__ = ["FILTERS_OT_apply_threshold"] 