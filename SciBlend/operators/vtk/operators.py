import bpy
from bpy_extras.io_utils import ImportHelper, axis_conversion
from bpy.props import StringProperty, EnumProperty, CollectionProperty, FloatProperty, BoolProperty, IntProperty
from bpy.types import Operator
import os
import math
import mathutils
import time
import json
from datetime import datetime, timedelta
from ..utils.scene import clear_scene, keyframe_visibility_single_frame, enforce_constant_interpolation

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
			vertices, edges, faces, point_data = self._read_grid(filepath)
			if not vertices:
				self.report({'ERROR'}, f"Failed to read file {file_elem.name}: No vertices found.")
				continue
			obj = self._create_mesh(context, vertices, edges, faces, point_data, f"Frame_{frame}")
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
		"""Read VTK/vtu/pvtu grid and return vertices, edges, faces, and point_data."""
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
			return [], [], [], {}
		
		if data is None:
			return [], [], [], {}
		try:
			num_points = int(data.GetNumberOfPoints()) if hasattr(data, 'GetNumberOfPoints') else 0
			num_cells = int(data.GetNumberOfCells()) if hasattr(data, 'GetNumberOfCells') else 0
		except Exception:
			num_points, num_cells = 0, 0
		if num_points == 0:
			return [], [], [], {}
		
		converted_data = data
		try:
			cell_data = data.GetCellData() if hasattr(data, 'GetCellData') else None
			has_cell_arrays = bool(cell_data) and cell_data.GetNumberOfArrays() > 0
			if num_cells > 0 and has_cell_arrays:
				from vtkmodules.vtkFiltersCore import vtkCellDataToPointData
				converter = vtkCellDataToPointData()
				converter.SetInputData(data)
				converter.PassCellDataOn()
				converter.Update()
				converted_data = converter.GetOutput() or data
		except Exception:
			converted_data = data
		
		points = converted_data.GetPoints()
		if points is None:
			return [], [], [], {}
		vertices = [points.GetPoint(i) for i in range(points.GetNumberOfPoints())]
		
		faces = []
		edges = []
		for i in range(converted_data.GetNumberOfCells() if hasattr(converted_data, 'GetNumberOfCells') else 0):
			cell = converted_data.GetCell(i)
			cell_type = cell.GetCellType()
			if cell_type in [VTK_TRIANGLE, VTK_QUAD]:
				face = [cell.GetPointId(j) for j in range(cell.GetNumberOfPoints())]
				faces.append(face)
			elif cell_type == VTK_TETRA:
				for j in range(4):
					face = [cell.GetPointId(k) for k in range(4) if k != j]
					faces.append(face)
			elif cell_type == VTK_HEXAHEDRON:
				indices = [cell.GetPointId(j) for j in range(cell.GetNumberOfPoints())]
				faces.append([indices[0], indices[1], indices[2], indices[3]])
				faces.append([indices[4], indices[5], indices[6], indices[7]])
				faces.append([indices[0], indices[1], indices[5], indices[4]])
				faces.append([indices[1], indices[2], indices[6], indices[5]])
				faces.append([indices[2], indices[3], indices[7], indices[6]])
				faces.append([indices[3], indices[0], indices[4], indices[7]])
			elif cell_type == VTK_WEDGE:
				indices = [cell.GetPointId(j) for j in range(6)]
				faces.append([indices[0], indices[1], indices[2]])
				faces.append([indices[3], indices[4], indices[5]])
				faces.append([indices[0], indices[1], indices[4], indices[3]])
				faces.append([indices[1], indices[2], indices[5], indices[4]])
				faces.append([indices[2], indices[0], indices[3], indices[5]])
			elif cell_type == VTK_PYRAMID:
				indices = [cell.GetPointId(j) for j in range(5)]
				faces.append([indices[0], indices[1], indices[2], indices[3]])
				faces.append([indices[0], indices[1], indices[4]])
				faces.append([indices[1], indices[2], indices[4]])
				faces.append([indices[2], indices[3], indices[4]])
				faces.append([indices[3], indices[0], indices[4]])
			elif cell_type == VTK_VOXEL:
				indices = [cell.GetPointId(j) for j in range(8)]
				faces.append([indices[0], indices[1], indices[3], indices[2]])
				faces.append([indices[4], indices[5], indices[7], indices[6]])
				faces.append([indices[0], indices[2], indices[6], indices[4]])
				faces.append([indices[1], indices[3], indices[7], indices[5]])
				faces.append([indices[0], indices[1], indices[5], indices[4]])
				faces.append([indices[2], indices[3], indices[7], indices[6]])
			elif cell_type == VTK_HEXAGONAL_PRISM:
				indices = [cell.GetPointId(j) for j in range(12)]
				faces.append([indices[0], indices[1], indices[2], indices[3], indices[4], indices[5]])
				faces.append([indices[6], indices[7], indices[8], indices[9], indices[10], indices[11]])
				for k in range(6):
					faces.append([indices[k], indices[(k+1)%6], indices[((k+1)%6)+6], indices[k+6]])
			elif cell_type in (VTK_LINE, VTK_POLYLINE):
				num_points_cell = cell.GetNumberOfPoints()
				if num_points_cell >= 2:
					for j in range(num_points_cell - 1):
						edges.append([cell.GetPointId(j), cell.GetPointId(j+1)])
			elif cell_type == VTK_PENTAGONAL_PRISM:
				indices = [cell.GetPointId(j) for j in range(10)]
				faces.append([indices[0], indices[1], indices[2], indices[3], indices[4]])
				faces.append([indices[5], indices[6], indices[7], indices[8], indices[9]])
				for k in range(5):
					faces.append([indices[k], indices[(k+1)%5], indices[((k+1)%5)+5], indices[k+5]])
			elif cell_type == VTK_PIXEL:
				indices = [cell.GetPointId(j) for j in range(4)]
				faces.append([indices[0], indices[1], indices[3], indices[2]])
			elif cell_type == VTK_POLYGON:
				num_points_cell = cell.GetNumberOfPoints()
				indices = [cell.GetPointId(j) for j in range(num_points_cell)]
				faces.append(indices)
			elif cell_type == VTK_POLYHEDRON:
				num_faces = cell.GetNumberOfFaces()
				for k in range(num_faces):
					face = cell.GetFace(k)
					face_indices = [face.GetPointId(j) for j in range(face.GetNumberOfPoints())]
					faces.append(face_indices)
			elif cell_type == VTK_POLY_VERTEX:
				pass
			elif cell_type == VTK_QUAD:
				indices = [cell.GetPointId(j) for j in range(4)]
				faces.append(indices)
			elif cell_type == VTK_TRIANGLE_STRIP:
				num_points_cell = cell.GetNumberOfPoints()
				for k in range(num_points_cell - 2):
					if k % 2 == 0:
						faces.append([cell.GetPointId(k), cell.GetPointId(k+1), cell.GetPointId(k+2)])
					else:
						faces.append([cell.GetPointId(k+1), cell.GetPointId(k), cell.GetPointId(k+2)])
			elif cell_type == VTK_VERTEX:
				pass

		point_data = {}
		pd = converted_data.GetPointData()
		# Optional component name map from UI (JSON)
		# Example: {"Stress": ["XX", "YY", "ZZ", "XY", "YZ", "XZ"]}

		try:
			name_map = json.loads(getattr(self, 'component_name_map_json', '') or '{}')
		except Exception:
			name_map = {}
		for k in range(pd.GetNumberOfArrays()):
			array = pd.GetArray(k)
			base_name = array.GetName() or f"Array_{k}"
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
					comp_suffix = comp_name
					component_values = []
					for j in range(num_tuples):
						component_values.append(array.GetComponent(j, comp))
					point_data[f"{base_name}_{comp_suffix}"] = component_values
				magnitude_values = []
				for j in range(num_tuples):
					tup = array.GetTuple(j)
					magnitude_values.append(math.sqrt(sum(v*v for v in tup)))
				point_data[f"{base_name}_Magnitude"] = magnitude_values
		
		return vertices, edges, faces, point_data

	def _create_mesh(self, context, vertices, edges, faces, point_data, name):
		"""Create Blender mesh from VTK data."""
		mesh = bpy.data.meshes.new(name)
		obj = bpy.data.objects.new(name, mesh)
		context.collection.objects.link(obj)
		mesh.from_pydata(vertices, edges, faces)
		mesh.update()
		for attr_name, attr_values in point_data.items():

			if len(attr_values) != len(vertices) or len(attr_values) == 0:
				continue
			first_value = attr_values[0]

			if not isinstance(first_value, (tuple, list)):
				float_attribute = mesh.attributes.new(name=attr_name, type='FLOAT', domain='POINT')
				for i, value in enumerate(attr_values):
					float_attribute.data[i].value = float(value)
			else:
				component_count = len(first_value)
				for comp_index in range(component_count):
					comp_attr = mesh.attributes.new(name=f"{attr_name}_{comp_index}", type='FLOAT', domain='POINT')
					for i, value in enumerate(attr_values):
						comp_attr.data[i].value = float(value[comp_index])
		return obj

__all__ = ["ImportVTKAnimationOperator"] 