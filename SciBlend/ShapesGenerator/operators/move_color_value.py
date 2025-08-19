import bpy
from bpy.props import StringProperty
from bpy.types import Operator

class MoveColorValue(Operator):
    bl_idname = "scene.color_value_move"
    bl_label = "Move Color Value"

    direction: StringProperty()

    def execute(self, context):
        scene = context.scene
        index = scene.color_values_index

        if self.direction == 'UP' and index > 0:
            scene.colors_values.move(index, index-1)
            scene.color_values_index -= 1
        elif self.direction == 'DOWN' and index < len(scene.colors_values) - 1:
            scene.colors_values.move(index, index+1)
            scene.color_values_index += 1

        return {'FINISHED'}