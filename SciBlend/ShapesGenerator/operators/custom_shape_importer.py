import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty

class SHAPESGENERATOR_OT_ImportCustomShape(Operator, ImportHelper):
    bl_idname = "shapesgenerator.import_custom_shape"
    bl_label = "Import Custom Shape"
    
    filename_ext = ".png"
    filter_glob: StringProperty(default="*.png", options={'HIDDEN'})

    def execute(self, context):
        active_shape = context.scene.shapesgenerator_shapes[context.scene.shapesgenerator_active_shape_index]
        active_shape.custom_shape_path = self.filepath
        active_shape.shape_type = 'CUSTOM'
        try:
            bpy.ops.shapesgenerator.update_shapes()
        except Exception as e:
            self.report({'ERROR'}, f"Error updating shapes: {str(e)}")
        return {'FINISHED'}