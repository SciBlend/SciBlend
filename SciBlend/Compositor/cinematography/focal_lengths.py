import bpy
from mathutils import Vector

def create_camera_from_view(length):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    override = {'area': area, 'region': region}
                    view3d = area.spaces[0]
                    break
    
    cam_data = bpy.data.cameras.new(name="Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    
    cam_obj.matrix_world = view3d.region_3d.view_matrix.inverted()
    
    cam_obj.data.type = bpy.context.scene.camera_type
    
    if cam_obj.data.type == 'PERSP':
        cam_obj.data.lens = length
    else:
        cam_obj.data.ortho_scale = 6.0  
    
    return cam_obj

def set_focal_length(length):
    camera = bpy.context.scene.camera
    if not camera or camera.type != 'CAMERA':
        camera = create_camera_from_view(length)
    else:
        if camera.data.type == 'PERSP':
            camera.data.lens = length
        else:
            camera.data.type = 'PERSP'
            camera.data.lens = length
    
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].region_3d.view_perspective = 'CAMERA'
            break

class CINEMATOGRAPHY_OT_set_focal_length(bpy.types.Operator):
    bl_idname = "cinematography.set_focal_length"
    bl_label = "Set Focal Length"
    bl_options = {'REGISTER', 'UNDO'}

    length: bpy.props.FloatProperty(name="Focal Length")

    def execute(self, context):
        set_focal_length(self.length)
        return {'FINISHED'}

class CINEMATOGRAPHY_OT_set_camera_type(bpy.types.Operator):
    bl_idname = "cinematography.set_camera_type"
    bl_label = "Set Camera Type"
    bl_options = {'REGISTER', 'UNDO'}

    camera_type: bpy.props.EnumProperty(
        items=[
            ('PERSP', "Perspective", "Perspective camera"),
            ('ORTHO', "Orthographic", "Orthographic camera")
        ],
        name="Camera Type"
    )

    def execute(self, context):
        camera = context.scene.camera
        if camera and camera.type == 'CAMERA':
            camera.data.type = self.camera_type
        context.scene.camera_type = self.camera_type
        return {'FINISHED'}

classes = (
    CINEMATOGRAPHY_OT_set_focal_length,
    CINEMATOGRAPHY_OT_set_camera_type,
)

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"Error registering {cls.__name__}: {str(e)}")

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"Error unregistering {cls.__name__}: {str(e)}")

def register_properties():
    if not hasattr(bpy.types.Scene, "camera_type"):
        bpy.types.Scene.camera_type = bpy.props.EnumProperty(
            items=[
                ('PERSP', "Perspective", "Perspective camera"),
                ('ORTHO', "Orthographic", "Orthographic camera")
            ],
            name="Camera Type",
            default='PERSP',
            update=lambda self, context: bpy.ops.cinematography.set_camera_type(camera_type=self.camera_type)
        )

def unregister_properties():
    if hasattr(bpy.types.Scene, "camera_type"):
        del bpy.types.Scene.camera_type