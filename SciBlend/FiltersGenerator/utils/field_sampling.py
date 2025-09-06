import bpy
import math
from mathutils import Vector, kdtree


class VectorFieldSampler:
    def __init__(self, obj: bpy.types.Object, attribute_name: str):
        if obj.type != 'MESH':
            raise ValueError("Domain object must be a mesh")
        self.obj = obj
        self.attribute_name = attribute_name
        self._points = []
        self._vectors = []
        self._kdtree = None
        self._bbox_min = Vector((0, 0, 0))
        self._bbox_max = Vector((0, 0, 0))
        self._build()

    def _build(self):
        mesh = self.obj.data
        attrs = getattr(mesh, "attributes", None)
        if not attrs:
            raise ValueError("Mesh has no attributes")

        is_composite = False
        comp_names = None
        if isinstance(self.attribute_name, str) and self.attribute_name.startswith("__COMP__:"):
            is_composite = True
            try:
                payload = self.attribute_name.split(":", 1)[1]
                parts = payload.split("|")
                if len(parts) != 3:
                    raise ValueError
                comp_names = (parts[0], parts[1], parts[2])
            except Exception:
                raise ValueError("Invalid composite attribute spec")

        if not is_composite:
            if self.attribute_name not in attrs:
                raise ValueError(f"Attribute '{self.attribute_name}' not found on mesh")
            attr = attrs[self.attribute_name]
            data_type = getattr(attr, "data_type", "")
            domain = getattr(attr, "domain", "")
            if data_type != 'FLOAT_VECTOR' or domain not in {'POINT', 'VERTEX'}:
                raise ValueError("Selected attribute is not a vector field on points/verts")
        else:
            for n in comp_names:
                if n not in attrs:
                    raise ValueError(f"Component attribute '{n}' not found")
                a = attrs[n]
                if getattr(a, 'data_type', '') != 'FLOAT' or getattr(a, 'domain', '') not in {'POINT', 'VERTEX'}:
                    raise ValueError("Component attributes must be FLOAT on POINT/VERTEX domain")

        self._points.clear()
        self._vectors.clear()
        world = self.obj.matrix_world

        if not is_composite:
            domain = getattr(attrs[self.attribute_name], 'domain', '')
            if domain == 'POINT':
                for i, v in enumerate(attrs[self.attribute_name].data):
                    co = world @ mesh.vertices[i].co
                    vec = Vector(v.vector)
                    self._points.append(co)
                    self._vectors.append(vec)
            else:
                vectors = [Vector(x.vector) for x in attrs[self.attribute_name].data]
                for i, vert in enumerate(mesh.vertices):
                    co = world @ vert.co
                    self._points.append(co)
                    self._vectors.append(vectors[i])
        else:
            a_x, a_y, a_z = (attrs[comp_names[0]], attrs[comp_names[1]], attrs[comp_names[2]])
            domain = getattr(a_x, 'domain', '')  # assume consistent
            if domain == 'POINT':
                for i in range(len(mesh.vertices)):
                    co = world @ mesh.vertices[i].co
                    vx = a_x.data[i].value
                    vy = a_y.data[i].value
                    vz = a_z.data[i].value
                    self._points.append(co)
                    self._vectors.append(Vector((vx, vy, vz)))
            else:
                vals_x = [d.value for d in a_x.data]
                vals_y = [d.value for d in a_y.data]
                vals_z = [d.value for d in a_z.data]
                for i, vert in enumerate(mesh.vertices):
                    co = world @ vert.co
                    self._points.append(co)
                    self._vectors.append(Vector((vals_x[i], vals_y[i], vals_z[i])))

        # KDTree
        size = len(self._points)
        tree = kdtree.KDTree(size)
        for i, p in enumerate(self._points):
            tree.insert(p, i)
        tree.balance()
        self._kdtree = tree

        mins = Vector((float('inf'),) * 3)
        maxs = Vector((float('-inf'),) * 3)
        for p in self._points:
            mins.x = min(mins.x, p.x)
            mins.y = min(mins.y, p.y)
            mins.z = min(mins.z, p.z)
            maxs.x = max(maxs.x, p.x)
            maxs.y = max(maxs.y, p.y)
            maxs.z = max(maxs.z, p.z)
        self._bbox_min = mins
        self._bbox_max = maxs

    @property
    def bbox_min(self):
        return self._bbox_min

    @property
    def bbox_max(self):
        return self._bbox_max

    def sample(self, position: Vector, k_neighbors: int = 8, normalize: bool = False) -> Vector:
        if self._kdtree is None:
            return Vector((0.0, 0.0, 0.0))
        co, idx, dist = self._kdtree.find(position)
        if idx is None:
            return Vector((0.0, 0.0, 0.0))
        neighbors = self._kdtree.find_n(position, max(1, k_neighbors))
        weighted = Vector((0.0, 0.0, 0.0))
        total_w = 0.0
        for _co, i, d in neighbors:
            v = self._vectors[i]
            w = 1.0 / max(d, 1e-8)
            weighted += v * w
            total_w += w
        if total_w <= 0.0:
            return Vector((0.0, 0.0, 0.0))
        v = weighted / total_w
        if normalize:
            l = v.length
            if l > 1e-12:
                v = v / l
        return v

    def inside_bbox(self, position: Vector, margin: float = 0.0) -> bool:
        bmin = self._bbox_min.copy()
        bmax = self._bbox_max.copy()
        if margin > 0.0:
            size = bmax - bmin
            expand = size * margin
            bmin -= expand
            bmax += expand
        return (bmin.x <= position.x <= bmax.x and
                bmin.y <= position.y <= bmax.y and
                bmin.z <= position.z <= bmax.z) 