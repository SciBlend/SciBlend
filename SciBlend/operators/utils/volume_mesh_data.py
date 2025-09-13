import bpy


class VolumeMeshData:
	"""Container for a single volumetric mesh instance to avoid global state."""
	def __init__(self):
		self.cells = []
		self.faces = []
		self.vertices = []
		self.face_map = {}


class VolumeVertex:
	"""Represents a single vertex in the volumetric mesh."""
	def __init__(self, co, original_index):
		self.co = co
		self.original_index = original_index
		self.blender_v_index = -1


class VolumeFace:
	"""Represents a face shared by two cells or a cell and the exterior."""
	def __init__(self, vertex_objects):
		self.vertices = vertex_objects
		self.owner = None
		self.neighbour = None
		self.blender_f_index = -1

	def is_boundary(self):
		"""Return True when this face has no neighbouring cell."""
		return self.neighbour is None

	def get_vertices_for_cell(self, cell):
		"""Return vertices oriented for the given cell; reverse for the neighbour for consistent normals."""
		if cell == self.owner:
			return self.vertices
		elif cell == self.neighbour:
			return self.vertices[::-1]
		return None


class VolumeCell:
	"""Represents a volumetric cell such as tetrahedron or hexahedron, with attached attributes."""
	def __init__(self):
		self.faces = []
		self.attributes = {}


VOLUME_MODEL_REGISTRY = {}


def register_model(object_name: str, model: VolumeMeshData) -> None:
	"""Register a VolumeMeshData model under the given Blender object name."""
	VOLUME_MODEL_REGISTRY[object_name] = model


def get_model(object_name: str) -> VolumeMeshData | None:
	"""Retrieve a registered VolumeMeshData for the given Blender object name, or None."""
	return VOLUME_MODEL_REGISTRY.get(object_name)


def unregister_model(object_name: str) -> None:
	"""Remove a registered VolumeMeshData entry if present."""
	if object_name in VOLUME_MODEL_REGISTRY:
		VOLUME_MODEL_REGISTRY.pop(object_name, None) 