import bpy
from bpy.types import Panel
from .color_values_list import COLOR_UL_Values_List

class PNGOverlayPanel(Panel):
    bl_idname = "VIEW3D_PT_png_overlay"
    bl_label = "Legend Generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SciBlend"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = getattr(scene, 'legend_settings', None)
        
        if not settings:
            layout.label(text="Legend settings not available", icon='INFO')
            return
        
        row = layout.row(align=True)
        row.prop(settings, "legend_enabled", text="Legend Enabled", toggle=True)
        
        box = layout.box()
        row = box.row(align=True)
        row.prop(settings, "auto_from_shader", text="Auto from Shader", toggle=True)
        row.operator("legend.choose_shader", text="Read from Shader", icon='SHADING_TEXTURE')
        
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Colormap", icon='COLOR')
        row.prop(settings, "colormap", text="")
        
        if settings.colormap == 'CUSTOM':
            row = box.row()
            row.prop(settings, "num_nodes", text="Nodes", icon='POINTCLOUD_DATA')
            row = box.row()
            row.template_list("COLOR_UL_Values_List", "color_values_list",
                              settings, "colors_values", settings, "color_values_index")
            col = row.column(align=True)
            col.operator("scene.color_value_move", text="", icon='TRIA_UP').direction = 'UP'
            col.operator("scene.color_value_move", text="", icon='TRIA_DOWN').direction = 'DOWN'
        else:
            col = box.column(align=True)
            col.prop(settings, "colormap_start", text="Start", icon='SORT_ASC')
            col.prop(settings, "colormap_end", text="End", icon='SORT_DESC')
            col.prop(settings, "colormap_subdivisions", text="Subdivisions", icon='GRID')
        
        box = layout.box()
        box.label(text="Legend Properties", icon='PROPERTIES')
        col = box.column(align=True)
        col.prop(settings, "legend_name", text="Name", icon='FONT_DATA')
        col.prop(settings, "multi_legend_count", text="Legends")
        col.prop(settings, "interpolation", text="Interpolation",
                 expand=False)
        col.prop(settings, "legend_orientation", text="Orientation",
                 expand=False)
        col.prop(settings, "legend_width", text="Width")
        col.prop(settings, "legend_height", text="Height")
        col.prop(settings, "legend_scale_linked", text="Link Scale")
        row = col.row(align=True)
        row.prop(settings, "legend_scale_x", text="Scale X")
        row.prop(settings, "legend_scale_y", text="Scale Y")
        row = col.row(align=True)
        row.prop(settings, "legend_position_x", text="Position X")
        row.prop(settings, "legend_position_y", text="Position Y")
        
        box = layout.box()
        box.label(text="Font", icon='FONT_DATA')
        row = box.row(align=True)
        row.prop(settings, "legend_font_type", text="Type")
        if settings.legend_font_type == 'SYSTEM':
            row = box.row(align=True)
            row.prop(settings, "legend_system_font", text="System Font")
        else:
            row = box.row(align=True)
            row.prop(settings, "legend_font", text="Custom Font File")
        
        row = box.row(align=True)
        row.prop(settings, "legend_text_size_pt", text="Size (pt)")
        
        row = box.row()
        row.prop(settings, "legend_text_color", text="Text Color")

        row = box.row(align=True)
        row.prop(settings, "legend_number_format", text="Number Format")
        row.prop(settings, "legend_decimal_places", text="Decimals")

        row = box.row(align=True)
        row.prop(settings, "legend_label_padding", text="Label Padding")

        row = box.row(align=True)
        row.prop(settings, "legend_label_offset_pct", text="Label Offset (%)")
        
        row = layout.row()
        row.scale_y = 1.5
        row.enabled = settings.legend_enabled
        row.operator("compositor.png_overlay",
                     text="Generate Legend", icon='RENDERLAYERS')