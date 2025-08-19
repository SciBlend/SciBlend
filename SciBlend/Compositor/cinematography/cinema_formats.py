import bpy
from bpy.types import Operator

class CINEMATOGRAPHY_OT_set_cinema_resolution(Operator):
    bl_idname = "cinematography.set_cinema_resolution"
    bl_label = "Set Cinema Resolution"
    bl_description = "Set the render resolution to the selected cinema format"
    bl_options = {'REGISTER', 'UNDO'}

    format: bpy.props.StringProperty()

    def execute(self, context):
        print(f"Setting cinema format to: {self.format}") 
        context.scene.cinema_format = self.format
        return {'FINISHED'}

class CINEMATOGRAPHY_OT_set_camera_type(Operator):
    bl_idname = "cinematography.set_camera_type"
    bl_label = "Set Camera Type"
    bl_description = "Set the camera type to perspective or orthographic"
    bl_options = {'REGISTER', 'UNDO'}

    camera_type: bpy.props.StringProperty()

    def execute(self, context):
        camera = context.scene.camera
        if camera and camera.type == 'CAMERA':
            if self.camera_type == 'PERSP':
                camera.data.type = 'PERSP'
            elif self.camera_type == 'ORTHO':
                camera.data.type = 'ORTHO'
        return {'FINISHED'}

classes = (CINEMATOGRAPHY_OT_set_cinema_resolution, CINEMATOGRAPHY_OT_set_camera_type)

def register():
    print("Registering cinema_formats classes")  
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    print("Unregistering cinema_formats classes") 
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()