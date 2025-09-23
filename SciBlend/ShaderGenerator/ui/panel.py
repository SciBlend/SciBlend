import bpy
from bpy.types import Panel
from ..operators.colorramp import (
    COLORRAMP_OT_add_color,
    COLORRAMP_OT_remove_color,
    COLORRAMP_OT_save_custom,
    COLORRAMP_OT_load_custom,
    COLORRAMP_OT_import_json,
)
from ..operators.create_shader import MATERIAL_OT_create_shader


class MATERIAL_PT_shader_generator(Panel):
    """Panel that exposes shader generation and custom ColorRamp controls."""
    bl_label = "Shader Generator"
    bl_idname = "MATERIAL_PT_shader_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Shader Generator'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Map Range", icon='RNDCURVE')
        box = layout.box()
        settings = getattr(scene, 'shader_generator_settings', None)
        if settings:
            row = box.row(align=True)
            row.prop(settings, "from_min", text="From Min")
            row.prop(settings, "from_max", text="From Max")
        else:
            box.label(text="Create a shader to enable sliders.")

        layout.separator()

        layout.label(text="Import Colormaps", icon='IMPORT')
        layout.operator(COLORRAMP_OT_import_json.bl_idname, text="Import Scientific Colormaps", icon='FILE_NEW')

        layout.separator()

        layout.label(text="Create Shader", icon='NODE_MATERIAL')
        box = layout.box()
        col = box.column(align=True)

        op = col.operator(MATERIAL_OT_create_shader.bl_idname, text="Generate Shader", icon='MATERIAL')
        col.prop(op, "colormap", text="Colormap")
        col.prop(op, "interpolation", text="Interpolation")
        col.prop(op, "gamma", text="Gamma")
        col.prop(op, "material_name", text="Material Name")
        col.prop(op, "apply_to_all", text="Apply to All")
        col.prop(op, "target_collection", text="Collection")
        col.prop(op, "normalization", text="Normalization")
        col.prop(op, "attribute_name", text="Attribute Name")

        layout.separator()

        layout.label(text="Custom ColorRamp", icon='COLOR')
        box = layout.box()
        row = box.row(align=True)
        row.operator(COLORRAMP_OT_add_color.bl_idname, text="Add Color", icon='ADD')
        row.operator(COLORRAMP_OT_remove_color.bl_idname, text="Remove Color", icon='REMOVE')

        for i, color in enumerate(scene.custom_colorramp):
            row = box.row(align=True)
            row.prop(color, "color", text=f"Color {i+1}")
            row.prop(color, "position", text="Pos")

        layout.separator()

        layout.label(text="Save/Load ColorRamp", icon='FILE_FOLDER')
        box = layout.box()
        box.operator(COLORRAMP_OT_save_custom.bl_idname, text="Save ColorRamp", icon='FILE_TICK')
        box.operator(COLORRAMP_OT_load_custom.bl_idname, text="Load ColorRamp", icon='IMPORT') 