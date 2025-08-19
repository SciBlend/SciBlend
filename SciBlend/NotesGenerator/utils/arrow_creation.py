import bpy
import bmesh
from mathutils import Vector


def create_cylinder(start, end, thickness):
    direction = end - start
    length = direction.length

    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=32,
        radius1=thickness,
        radius2=thickness,
        depth=length,
        matrix=bpy.context.scene.cursor.matrix,
    )

    mesh = bpy.data.meshes.new("Annotation")
    bm.to_mesh(mesh)
    bm.free()

    cylinder_obj = bpy.data.objects.new("Annotation", mesh)
    bpy.context.collection.objects.link(cylinder_obj)

    cylinder_obj.rotation_mode = 'QUATERNION'
    cylinder_obj.rotation_quaternion = direction.to_track_quat('Z', 'Y')
    cylinder_obj.location = start

    return cylinder_obj


def create_text(location, text, size=0.5):
    bpy.ops.object.text_add(enter_editmode=False, location=location)
    text_obj = bpy.context.active_object
    text_obj.data.body = text
    text_obj.data.size = size
    return text_obj
