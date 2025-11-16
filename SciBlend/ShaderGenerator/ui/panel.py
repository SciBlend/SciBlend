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
from ..operators.refresh_attributes import SHADER_OT_refresh_attributes
from ..operators.collection_operators import (
    SHADER_OT_refresh_collections,
    SHADER_OT_remove_shader,
    SHADER_OT_apply_changes,
)


class MATERIAL_PT_shader_generator(Panel):
    """Panel for dynamic shader management with collection list."""
    bl_label = "Shader Generator"
    bl_idname = "MATERIAL_PT_shader_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Shader Generator'

    def draw(self, context):
        """Draw the Shader Generator panel with collection list and dynamic settings.
        
        Parameters
        ----------
        context : bpy.types.Context
            Blender context.
        """
        layout = self.layout
        scene = context.scene
        settings = getattr(scene, 'shader_generator_settings', None)
        
        if not settings:
            layout.label(text="Settings not available", icon='ERROR')
            return
        
        if not hasattr(settings, 'collection_shaders'):
            box = layout.box()
            box.label(text="Error: collection_shaders not initialized", icon='ERROR')
            box.label(text="Try reloading the addon (F3 → Reload Scripts)")
            return

        layout.label(text="Collections", icon='OUTLINER_COLLECTION')
        
        if len(settings.collection_shaders) == 0:
            box = layout.box()
            box.label(text="No collections loaded", icon='INFO')
            box.operator(SHADER_OT_refresh_collections.bl_idname, text="Load Collections", icon='FILE_REFRESH')
            
            layout.separator()
            
            layout.label(text="Tools", icon='TOOL_SETTINGS')
            box = layout.box()
            box.operator(SHADER_OT_refresh_attributes.bl_idname, text="Refresh Attributes", icon='FILE_REFRESH')
            box.operator(COLORRAMP_OT_import_json.bl_idname, text="Import Colormaps", icon='IMPORT')
            
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
            return
        
        box = layout.box()
        row = box.row()
        row.template_list(
            "SHADER_UL_collection_list",
            "",
            settings,
            "collection_shaders",
            settings,
            "active_collection_index",
            rows=5
        )
        
        col = row.column(align=True)
        col.operator(SHADER_OT_refresh_collections.bl_idname, text="", icon='FILE_REFRESH')
        col.operator(SHADER_OT_remove_shader.bl_idname, text="", icon='TRASH')
        
        layout.separator()
        
        if settings.active_collection_index >= 0 and settings.active_collection_index < len(settings.collection_shaders):
            item = settings.collection_shaders[settings.active_collection_index]
            
            has_material = False
            if item.material_name:
                mat = bpy.data.materials.get(item.material_name)
                if mat and mat.get('sciblend_colormap') is not None:
                    has_material = True
            
            layout.label(text=f"Shader Settings: {item.collection_name}", icon='NODE_MATERIAL')
            
            box = layout.box()
            col = box.column(align=True)
            
            col.prop(settings, "colormap", text="Colormap")
            col.prop(settings, "interpolation", text="Interpolation")
            col.prop(settings, "gamma", text="Gamma")
            col.prop(settings, "attribute_name", text="Attribute")
            col.prop(settings, "normalization", text="Normalization")
            
            layout.separator()
            
            layout.label(text="Map Range", icon='RNDCURVE')
            box = layout.box()
            row = box.row(align=True)
            row.prop(settings, "from_min", text="From Min")
            row.prop(settings, "from_max", text="From Max")
            
            layout.separator()
            
            row = layout.row(align=True)
            row.scale_y = 1.5
            if has_material:
                row.operator(MATERIAL_OT_create_shader.bl_idname, text="Update Shader", icon='FILE_REFRESH')
            else:
                row.operator(MATERIAL_OT_create_shader.bl_idname, text="Create Shader", icon='MATERIAL')
            row.operator(SHADER_OT_apply_changes.bl_idname, text="Apply", icon='CHECKMARK')
        else:
            layout.label(text="Select a collection to manage shaders", icon='INFO')

        layout.separator()
        
        layout.label(text="Tools", icon='TOOL_SETTINGS')
        box = layout.box()
        box.operator(SHADER_OT_refresh_attributes.bl_idname, text="Refresh Attributes", icon='FILE_REFRESH')
        box.operator(COLORRAMP_OT_import_json.bl_idname, text="Import Colormaps", icon='IMPORT')

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