import bpy
import json
import logging
from bpy.types import Operator
from bpy.props import StringProperty
from ..utils.colormaps import load_colormaps_from_json, COLORMAPS

logger = logging.getLogger(__name__)


class COLORRAMP_OT_add_color(Operator):
    """Add a new color stop to the custom ColorRamp collection."""
    bl_idname = "colorramp.add_color"
    bl_label = "Add Color"
    bl_description = "Add a new color to the custom ColorRamp"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        custom_ramp = context.scene.custom_colorramp
        new_color = custom_ramp.add()
        new_color.position = len(custom_ramp) / (len(custom_ramp) + 1)
        return {'FINISHED'}


class COLORRAMP_OT_remove_color(Operator):
    """Remove the last color stop from the custom ColorRamp collection."""
    bl_idname = "colorramp.remove_color"
    bl_label = "Remove Color"
    bl_description = "Remove the last color from the custom ColorRamp"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        custom_ramp = context.scene.custom_colorramp
        if len(custom_ramp) > 2:
            custom_ramp.remove(len(custom_ramp) - 1)
        return {'FINISHED'}


class COLORRAMP_OT_save_custom(Operator):
    """Serialize the current custom ColorRamp to a JSON file."""
    bl_idname = "colorramp.save_custom"
    bl_label = "Save Custom ColorRamp"
    bl_description = "Save the current custom ColorRamp"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        custom_ramp = context.scene.custom_colorramp
        data = [{"color": list(c.color) + [1.0], "position": c.position} for c in custom_ramp]
        with open(self.filepath, 'w') as f:
            json.dump(data, f)
        self.report({'INFO'}, f"ColorRamp saved to {self.filepath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = "custom_colorramp.json"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class COLORRAMP_OT_load_custom(Operator):
    """Load a custom ColorRamp from a JSON file into the collection."""
    bl_idname = "colorramp.load_custom"
    bl_label = "Load Custom ColorRamp"
    bl_description = "Load a custom ColorRamp"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        with open(self.filepath, 'r') as f:
            data = json.load(f)

        custom_ramp = context.scene.custom_colorramp
        custom_ramp.clear()
        for item in data:
            new_color = custom_ramp.add()
            new_color.color = item['color'][:3]
            new_color.position = item['position']

        self.report({'INFO'}, f"ColorRamp loaded from {self.filepath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class COLORRAMP_OT_import_json(Operator):
    """Import ParaView-style colormaps from a JSON file into the available list."""
    bl_idname = "colorramp.import_json"
    bl_label = "Import JSON Colormaps"
    bl_description = "Import colormaps from a Paraview JSON file"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        description="Path to the JSON file",
        default="",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}

        try:
            new_colormaps = load_colormaps_from_json(self.filepath)
            COLORMAPS.update(new_colormaps)
            self.report({'INFO'}, f"Successfully imported {len(new_colormaps)} colormaps")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error importing colormaps: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'} 