import bpy
import os
import math
import mathutils
import time
import json
from bpy_extras.io_utils import ImportHelper, axis_conversion
from bpy.props import StringProperty, EnumProperty, CollectionProperty, FloatProperty, BoolProperty, IntProperty
from bpy.types import Operator
from datetime import datetime, timedelta
from ..utils.scene import clear_scene, keyframe_visibility_single_frame, enforce_constant_interpolation
from ..utils.scene import get_import_target_collection
from ..utils.volume_mesh_data import VolumeMeshData, VolumeVertex, VolumeFace, VolumeCell, register_model

# VTK cell type ids
VTK_VERTEX = 1
VTK_POLY_VERTEX = 2
VTK_LINE = 3
VTK_POLYLINE = 4
VTK_TRIANGLE = 5
VTK_TRIANGLE_STRIP = 6
VTK_POLYGON = 7
VTK_PIXEL = 8
VTK_QUAD = 9
VTK_TETRA = 10
VTK_VOXEL = 11
VTK_HEXAHEDRON = 12
VTK_WEDGE = 13
VTK_PYRAMID = 14
VTK_PENTAGONAL_PRISM = 15
VTK_HEXAGONAL_PRISM = 16
VTK_POLYHEDRON = 42

class ImportVTKAnimationOperator(Operator, ImportHelper):
	"""Import VTK/VTU/PVTU animation files into Blender."""
	bl_idname = "import_vtk.animation"
	bl_label = "Import VTK/VTU/PVTU Animation"
	bl_options = {'PRESET', 'UNDO'}

	filename_ext = ""
	filter_glob: StringProperty(default="*.vtk;*.vtu;*.pvtu;*.vtp;*.pvtp", options={'HIDDEN'})

	files: CollectionProperty(
		name="File Path",
		type=bpy.types.OperatorFileListElement,
	)

	directory: StringProperty(subtype='DIR_PATH')

	start_frame_number: IntProperty(name="Start Frame Number", default=1, min=1)
	end_frame_number: IntProperty(name="End Frame Number", default=10, min=1)
	axis_forward: EnumProperty(name="Forward Axis", items=[('X','X',''),('Y','Y',''),('Z','Z',''),('-X','-X',''),('-Y','-Y',''),('-Z','-Z','')], default='-Z')
	axis_up: EnumProperty(name="Up Axis", items=[('X','X',''),('Y','Y',''),('Z','Z',''),('-X','-X',''),('-Y','-Y',''),('-Z','-Z','')], default='Y')
	scale_factor: FloatProperty(name="Scale Factor", default=1.0, min=0.01, max=100.0)
	create_smooth_groups: BoolProperty(name="Create Smooth Groups", default=True)
	height_scale: FloatProperty(name="Height Scale", default=1.0, min=0.01, max=100.0)
	component_name_map_json: StringProperty(name="Component Name Map (JSON)", description="Optional JSON mapping of base array name to list of component names.", default="")

	def _vtk_available(self) -> bool:
		"""Return True if VTK modules can be imported in the current environment."""
		try:
			from vtkmodules.vtkCommonCore import vtkVersion  # noqa: F401
			return True
		except Exception:
			return False

	def execute(self, context):
		"""Execute the import process across the selected files and create keyframed visibility when needed."""
		if not self._vtk_available():
			self.report({'INFO'}, "VTK core not detected; attempting vtkmodules import.")
		settings = context.scene.x3d_import_settings
		self.scale_factor = settings.scale_factor
		self.axis_forward = settings.axis_forward
		self.axis_up = settings.axis_up
		loop_count = max(1, getattr(settings, "loop_count", 1))
		if settings.overwrite_scene:
			clear_scene(context)
		self._target_collection = get_import_target_collection(context, settings.import_to_new_collection, os.path.basename(self.directory) or "VTK_Import")
		files_to_process = self.files[self.start_frame_number-1:self.end_frame_number]
		num_frames = len(files_to_process)
		context.scene.frame_start = self.start_frame_number
		context.scene.frame_end = self.start_frame_number + (num_frames * loop_count) - 1 if num_frames > 0 else self.start_frame_number
		start_wall = time.time()
		print(f"[VTK] Starting import of {num_frames} file(s) at {datetime.now().strftime('%H:%M:%S')}")
		for i, file_elem in enumerate(files_to_process):
			filepath = os.path.join(self.directory, file_elem.name)
			frame = self.start_frame_number + i
			per_item_start = time.time()
			volume_data, point_data = self._read_grid(filepath)
			if not volume_data or len(volume_data.vertices) == 0:
				self.report({'ERROR'}, f"Failed to read file {file_elem.name}: No vertices found.")
				continue
			obj = self._create_mesh(context, volume_data, point_data, f"Frame_{frame}")
			try:
				obj["sciblend_volume_source_dir"] = self.directory or ""
				obj["sciblend_volume_source_file"] = file_elem.name or ""
				obj["sciblend_volume_format"] = os.path.splitext(filepath)[1].lower()
			except Exception:
				pass
			rotation = axis_conversion(from_forward='-Z', from_up='Y', to_forward=self.axis_forward, to_up=self.axis_up).to_4x4()
			scale = mathutils.Matrix.Scale(self.scale_factor, 4)
			obj.matrix_world = rotation @ scale
			bpy.context.view_layer.update()
			if num_frames > 1 or loop_count > 1:
				for k in range(loop_count):
					occurrence = frame + (k * num_frames)
					keyframe_visibility_single_frame(obj, occurrence)
				enforce_constant_interpolation(obj)
			else:
				obj.hide_viewport = False
				obj.hide_render = False
			duration = time.time() - per_item_start
			processed = i + 1
			elapsed = time.time() - start_wall
			avg = (elapsed / processed) if processed > 0 else 0.0
			remaining = max(0, num_frames - processed)
			eta_dt = datetime.now() + timedelta(seconds=avg * remaining) if avg > 0 else datetime.now()
			print(f"[VTK] Imported {os.path.basename(file_elem.name)} ({processed}/{num_frames}) in {duration:.2f}s. ETA ~ {eta_dt.strftime('%H:%M:%S')}")
		return {'FINISHED'}

	def _read_grid(self, filepath):
		"""Read a VTK file and build an instance-based topological volume model and point data."""
		from vtkmodules.vtkIOLegacy import vtkUnstructuredGridReader, vtkPolyDataReader
		from vtkmodules.vtkIOXML import (
			vtkXMLUnstructuredGridReader,
			vtkXMLPUnstructuredGridReader,
			vtkXMLPolyDataReader,
			vtkXMLPPolyDataReader,
		)
		
		extension = os.path.splitext(filepath)[1].lower()
		if extension == '.vtk':
			from vtkmodules.vtkIOLegacy import vtkDataSetReader
			reader = vtkDataSetReader()
			reader.SetFileName(filepath)
			reader.Update()
			data = reader.GetOutput()
			if data is None or getattr(data, 'GetNumberOfPoints', lambda: 0)() == 0:
				poly_reader = vtkPolyDataReader()
				poly_reader.SetFileName(filepath)
				poly_reader.Update()
				data = poly_reader.GetOutput()
		elif extension == '.vtu':
			reader = vtkXMLUnstructuredGridReader()
			reader.SetFileName(filepath)
			reader.Update()
			data = reader.GetOutput()
		elif extension == '.pvtu':
			reader = vtkXMLPUnstructuredGridReader()
			reader.SetFileName(filepath)
			reader.Update()
			data = reader.GetOutput()
		elif extension == '.vtp':
			reader = vtkXMLPolyDataReader()
			reader.SetFileName(filepath)
			reader.Update()
			data = reader.GetOutput()
		elif extension == '.pvtp':
			reader = vtkXMLPPolyDataReader()
			reader.SetFileName(filepath)
			reader.Update()
			data = reader.GetOutput()
		else:
			return None, {}
		
		if data is None:
			return None, {}
		try:
			num_points = int(data.GetNumberOfPoints()) if hasattr(data, 'GetNumberOfPoints') else 0
		except Exception:
			num_points = 0
		if num_points == 0:
			return None, {}
		
		volume_data = VolumeMeshData()
		vtk_points = data.GetPoints()
		for i in range(vtk_points.GetNumberOfPoints()):
			volume_data.vertices.append(VolumeVertex(vtk_points.GetPoint(i), original_index=i))
		
		cell_definitions = {
			VTK_TETRA: [[0,2,1], [0,1,3], [1,2,3], [0,3,2]],
			VTK_HEXAHEDRON: [[0,3,2,1], [4,5,6,7], [0,1,5,4], [1,2,6,5], [2,3,7,6], [3,0,4,7]],
			VTK_WEDGE: [[0,2,1], [3,4,5], [0,1,4,3], [1,2,5,4], [2,0,3,5]],
			VTK_PYRAMID: [[0,1,2,3], [0,1,4], [1,2,4], [2,3,4], [3,0,4]],
			VTK_VOXEL: [[0,1,3,2], [4,5,7,6], [0,2,6,4], [1,3,7,5], [0,1,5,4], [2,3,7,6]],
		}
		
		try:
			num_cells = int(data.GetNumberOfCells()) if hasattr(data, 'GetNumberOfCells') else 0
		except Exception:
			num_cells = 0
		cd = data.GetCellData()
		for i in range(num_cells):
			vtk_cell = data.GetCell(i)
			cell_type = vtk_cell.GetCellType()
			new_cell = VolumeCell()
			volume_data.cells.append(new_cell)
			if cd is not None:
				for k in range(cd.GetNumberOfArrays()):
					array = cd.GetArray(k)
					name = array.GetName() or f"CellArray_{k}"
					try:
						val = array.GetTuple(i)
					except Exception:
						try:
							val = (array.GetValue(i),)
						except Exception:
							val = (0.0,)
					new_cell.attributes[name] = val
			if cell_type == VTK_POLYHEDRON and hasattr(vtk_cell, 'GetNumberOfFaces'):
				num_faces = vtk_cell.GetNumberOfFaces()
				for k in range(num_faces):
					face = vtk_cell.GetFace(k)
					face_indices = [face.GetPointId(j) for j in range(face.GetNumberOfPoints())]
					self._process_face(volume_data, new_cell, face_indices)
			elif cell_type in cell_definitions:
				face_v_indices_list = cell_definitions[cell_type]
				for face_v_indices in face_v_indices_list:
					original_indices = [vtk_cell.GetPointId(j) for j in face_v_indices]
					self._process_face(volume_data, new_cell, original_indices)
			elif cell_type in (VTK_TRIANGLE, VTK_QUAD, VTK_POLYGON, VTK_TRIANGLE_STRIP, VTK_PIXEL):
				if cell_type == VTK_TRIANGLE_STRIP:
					num_pts = vtk_cell.GetNumberOfPoints()
					for s in range(num_pts - 2):
						a = vtk_cell.GetPointId(s)
						b = vtk_cell.GetPointId(s + 1)
						c = vtk_cell.GetPointId(s + 2)
						if s % 2 == 0:
							self._process_face(volume_data, new_cell, [a, b, c])
						else:
							self._process_face(volume_data, new_cell, [b, a, c])
				else:
					num_pts = vtk_cell.GetNumberOfPoints()
					if num_pts >= 3:
						original_indices = [vtk_cell.GetPointId(j) for j in range(num_pts)]
						self._process_face(volume_data, new_cell, original_indices)
			else:
				continue
		
		point_data = {}
		pd = data.GetPointData()
		try:
			name_map = json.loads(getattr(self, 'component_name_map_json', '') or '{}')
		except Exception:
			name_map = {}
		for k in range(pd.GetNumberOfArrays()):
			array = pd.GetArray(k)
			base_name = array.GetName() or f"Array_{k}"
			if isinstance(base_name, str) and base_name.strip().lower() == 'id':
				base_name = 'id_attribute'
			num_components = array.GetNumberOfComponents()
			num_tuples = array.GetNumberOfTuples()
			if num_components <= 1:
				point_data[base_name] = [array.GetValue(j) for j in range(num_tuples)]
			else:
				preferred = None
				if isinstance(name_map, dict) and base_name in name_map:
					try:
						cand = name_map[base_name]
						if isinstance(cand, list) and len(cand) == num_components:
							preferred = [str(x) for x in cand]
					except Exception:
						preferred = None
				for comp in range(num_components):
					comp_raw = array.GetComponentName(comp)
					comp_name = ""
					if comp_raw is not None:
						try:
							comp_name = (comp_raw.decode('utf-8', 'ignore') if isinstance(comp_raw, (bytes, bytearray)) else str(comp_raw)).strip()
						except Exception:
							comp_name = str(comp_raw).strip()
					if preferred is not None:
						comp_name = preferred[comp]
					if comp_name == "":
						labels_3 = ['X', 'Y', 'Z']
						labels_6 = ['XX', 'YY', 'ZZ', 'XY', 'YZ', 'XZ']
						labels_9 = ['XX', 'XY', 'XZ', 'YX', 'YY', 'YZ', 'ZX', 'ZY', 'ZZ']
						if num_components == 3 and comp < 3:
							comp_name = labels_3[comp]
						elif num_components == 6 and comp < 6:
							comp_name = labels_6[comp]
						elif num_components == 9 and comp < 9:
							comp_name = labels_9[comp]
						else:
							comp_name = str(comp)
					component_values = []
					for j in range(num_tuples):
						component_values.append(array.GetComponent(j, comp))
					point_data[f"{base_name}_{comp_name}"] = component_values
				magnitude_values = []
				for j in range(num_tuples):
					tup = array.GetTuple(j)
					magnitude_values.append(math.sqrt(sum(v*v for v in tup)))
				point_data[f"{base_name}_Magnitude"] = magnitude_values
		
		return volume_data, point_data

	def _process_face(self, volume_data: VolumeMeshData, current_cell: VolumeCell, original_indices):
		"""Create or link a face for the current cell, using a canonical key to share faces between neighbouring cells."""
		face_key = tuple(sorted(original_indices))
		if face_key in volume_data.face_map:
			existing_face = volume_data.face_map[face_key]
			existing_face.neighbour = current_cell
			current_cell.faces.append(existing_face)
		else:
			vertex_objects = [volume_data.vertices[idx] for idx in original_indices]
			new_face = VolumeFace(vertex_objects)
			new_face.owner = current_cell
			volume_data.face_map[face_key] = new_face
			volume_data.faces.append(new_face)
			current_cell.faces.append(new_face)

	def _create_mesh(self, context, volume_data, point_data, name):
		"""Create Blender mesh from the boundary faces of the in-memory volume model; assigns point and cell attributes."""
		mesh = bpy.data.meshes.new(name)
		obj = bpy.data.objects.new(name, mesh)
		if hasattr(self, '_target_collection') and self._target_collection is not None:
			self._target_collection.objects.link(obj)
		else:
			context.collection.objects.link(obj)

		blender_vertices = [v.co for v in volume_data.vertices]
		for i, v_obj in enumerate(volume_data.vertices):
			v_obj.blender_v_index = i

		blender_faces = []
		boundary_face_owner_index = []
		for face_obj in volume_data.faces:
			if face_obj.is_boundary():
				owner_cell = face_obj.owner
				face_vertices = face_obj.get_vertices_for_cell(owner_cell)
				if not face_vertices:
					continue
				face_indices = [v.blender_v_index for v in face_vertices]
				blender_faces.append(face_indices)
				boundary_face_owner_index.append(owner_cell)
				face_obj.blender_f_index = len(blender_faces) - 1

		mesh.from_pydata(blender_vertices, [], blender_faces)
		mesh.update()
		try:
			mesh.calc_normals_split()
		except Exception:
			try:
				mesh.calc_normals()
			except Exception:
				pass

		if point_data:
			for attr_name, attr_values in point_data.items():
				if len(attr_values) == len(blender_vertices):
					attr = mesh.attributes.new(name=attr_name if attr_name.strip().lower() != 'id' else 'id_attribute', type='FLOAT', domain='POINT')
					attr.data.foreach_set('value', attr_values)

		# Assign cell data to FACE domain attributes
		if len(boundary_face_owner_index) > 0:
			all_attr_names = set()
			for cell in boundary_face_owner_index:
				for k in cell.attributes.keys():
					all_attr_names.add(k)
			for attr_name in sorted(all_attr_names):
				values = [0.0] * len(blender_faces)
				for face_idx, cell in enumerate(boundary_face_owner_index):
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
				attr = mesh.attributes.new(name=f"cell_{attr_name}", type='FLOAT', domain='FACE')
				attr.data.foreach_set('value', values)

		# Persist the topology model for this object name
		register_model(obj.name, volume_data)

		if hasattr(obj, 'volume_mesh_info') and getattr(obj.volume_mesh_info, 'is_volume_mesh', None) is not None:
			obj.volume_mesh_info.is_volume_mesh = True

		return obj

__all__ = ["ImportVTKAnimationOperator"] 