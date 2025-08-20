import bpy
from bpy.props import StringProperty
from bpy.types import Operator

class MoveColorValue(Operator):
    bl_idname = "scene.color_value_move"
    bl_label = "Move Color Value"

    direction: StringProperty()

    def execute(self, context):
        settings = context.scene.legend_settings
        index = settings.color_values_index

        if self.direction == 'UP' and index > 0:
            settings.colors_values.move(index, index-1)
            settings.color_values_index -= 1
        elif self.direction == 'DOWN' and index < len(settings.colors_values) - 1:
            settings.colors_values.move(index, index+1)
            settings.color_values_index += 1

        return {'FINISHED'}