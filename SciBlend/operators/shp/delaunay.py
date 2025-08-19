import bpy
import time
from ..utils.delaunay_voronoi import computeDelaunayTriangulation

try:
    from mathutils.geometry import delaunay_2d_cdt
except ImportError:
    NATIVE = False
else:
    NATIVE = True

import logging
log = logging.getLogger(__name__)

class Point:
    """Lightweight 3D point used by the Python Delaunay fallback."""
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

def unique(values):
    """Remove duplicated XY entries in-place preserving the last Z.

    Returns a tuple (num_duplicates, num_z_colinear).
    """
    nDupli = 0
    nZcolinear = 0
    values.sort()
    last = values[-1]
    for i in range(len(values) - 2, -1, -1):
        if last[:2] == values[i][:2]:
            if last[2] == values[i][2]:
                nDupli += 1
            else:
                nZcolinear += 1
            del values[i]
        else:
            last = values[i]
    return (nDupli, nZcolinear)

def checkEqual(lst):
    """Return True if all elements in the list are equal."""
    return lst[1:] == lst[:-1]

class ShapefileDelaunayOperator(bpy.types.Operator):
    """Apply Delaunay triangulation to selected mesh objects (2.5D)."""
    bl_idname = "object.apply_delaunay"
    bl_label = "Apply Delaunay Triangulation"
    bl_description = "Terrain points cloud Delaunay triangulation in 2.5D"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and all(obj.type == 'MESH' for obj in context.selected_objects)

    def execute(self, context):
        """Triangulate all selected mesh vertices in XY, preserving Z as height."""
        w = context.window
        w.cursor_set('WAIT')

        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objects:
            self.report({'WARNING'}, "Please select at least one mesh object")
            return {'CANCELLED'}

        try:
            all_verts = []
            vertex_offset = 0
            original_data = []

            for obj in selected_objects:
                mesh = obj.data
                if len(mesh.vertices) < 3:
                    continue

                matrix_world = obj.matrix_world
                verts = [matrix_world @ v.co for v in mesh.vertices]
                all_verts.extend([(v.x, v.y, v.z) for v in verts])
                original_data.append({'object': obj, 'vertex_count': len(verts), 'offset': vertex_offset})
                vertex_offset += len(verts)

            if len(all_verts) < 3:
                self.report({'WARNING'}, "Not enough vertices in total")
                return {'CANCELLED'}

            if NATIVE:
                verts2d = [(v[0], v[1]) for v in all_verts]
                verts_out, edges, faces, overts, _, _ = delaunay_2d_cdt(verts2d, [], [], 0, 0.1)
                verts_final = [(v.x, v.y, all_verts[overts[i][0]][2]) for i, v in enumerate(verts_out)]
            else:
                vertsPts = [Point(v[0], v[1], v[2]) for v in all_verts]
                faces = computeDelaunayTriangulation(vertsPts)
                faces = [tuple(reversed(tri)) for tri in faces]
                verts_final = all_verts

            tin_mesh = bpy.data.meshes.new("TIN")
            if NATIVE:
                tin_mesh.from_pydata(verts_final, edges, faces)
            else:
                tin_mesh.from_pydata(verts_final, [], faces)
            tin_mesh.update(calc_edges=True)

            tin_obj = bpy.data.objects.new("TIN", tin_mesh)
            context.scene.collection.objects.link(tin_obj)

            for mat in selected_objects[0].data.materials:
                tin_mesh.materials.append(mat)

            context.view_layer.objects.active = tin_obj
            tin_obj.select_set(True)
            for obj in selected_objects:
                obj.select_set(False)

        except Exception as e:
            self.report({'ERROR'}, f"Error in triangulation: {str(e)}")
            return {'CANCELLED'}
        finally:
            w.cursor_set('DEFAULT')

        return {'FINISHED'}

__all__ = ["ShapefileDelaunayOperator"] 