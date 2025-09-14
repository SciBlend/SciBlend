import os
from typing import Tuple
from ...operators.utils.volume_mesh_data import VolumeMeshData, VolumeVertex, VolumeFace, VolumeCell

VTK_POLYHEDRON = 42
VTK_TETRA = 10
VTK_VOXEL = 11
VTK_HEXAHEDRON = 12
VTK_WEDGE = 13
VTK_PYRAMID = 14


def _process_face(volume_data: VolumeMeshData, current_cell: VolumeCell, original_indices):
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


def read_volume_data_from_vtk(filepath: str) -> Tuple[VolumeMeshData, dict]:
	"""Read a VTK/VTU/PVTU file and return (VolumeMeshData, point_data). point_data may be empty.

	This function avoids Blender Operator/RNA construction and is safe to call on-demand.
	"""
	try:
		from vtkmodules.vtkIOLegacy import vtkPolyDataReader
		from vtkmodules.vtkIOXML import (
			vtkXMLUnstructuredGridReader,
			vtkXMLPUnstructuredGridReader,
			vtkXMLPolyDataReader,
			vtkXMLPPolyDataReader,
		)
		from vtkmodules.vtkIOLegacy import vtkDataSetReader
	except Exception as e:
		raise RuntimeError(f"VTK modules not available: {e}")

	extension = os.path.splitext(filepath)[1].lower()
	data = None
	if extension == '.vtk':
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
		reader = vtkXMLUnstructuredGridReader(); reader.SetFileName(filepath); reader.Update(); data = reader.GetOutput()
	elif extension == '.pvtu':
		reader = vtkXMLPUnstructuredGridReader(); reader.SetFileName(filepath); reader.Update(); data = reader.GetOutput()
	elif extension == '.vtp':
		reader = vtkXMLPolyDataReader(); reader.SetFileName(filepath); reader.Update(); data = reader.GetOutput()
	elif extension == '.pvtp':
		reader = vtkXMLPPolyDataReader(); reader.SetFileName(filepath); reader.Update(); data = reader.GetOutput()
	else:
		raise RuntimeError(f"Unsupported extension: {extension}")
	if data is None:
		raise RuntimeError("VTK reader returned no data")

	try:
		num_points = int(data.GetNumberOfPoints()) if hasattr(data, 'GetNumberOfPoints') else 0
	except Exception:
		num_points = 0
	if num_points == 0:
		raise RuntimeError("VTK data has no points")

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
				_process_face(volume_data, new_cell, face_indices)
		elif cell_type in cell_definitions:
			face_v_indices_list = cell_definitions[cell_type]
			for face_v_indices in face_v_indices_list:
				original_indices = [vtk_cell.GetPointId(j) for j in face_v_indices]
				_process_face(volume_data, new_cell, original_indices)
		else:
			continue

	return volume_data, {} 