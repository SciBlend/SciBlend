import bpy
from bpy.types import Panel
from .color_values_list import COLOR_UL_Values_List

class PNGOverlayPanel(Panel):
    bl_idname = "VIEW3D_PT_png_overlay"
    bl_label = "Legend Generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Legend Generator"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        row = box.row(align=True)
        row.label(text="Colormap", icon='COLOR')
        row.prop(scene, "colormap", text="")
        
        if scene.colormap == 'CUSTOM':
            row = box.row()
            row.prop(scene, "num_nodes", text="Nodes", icon='POINTCLOUD_DATA')
            row = box.row()
            row.template_list("COLOR_UL_Values_List", "color_values_list",
                              scene, "colors_values", scene, "color_values_index")
            col = row.column(align=True)
            col.operator("scene.color_value_move", text="", icon='TRIA_UP').direction = 'UP'
            col.operator("scene.color_value_move", text="", icon='TRIA_DOWN').direction = 'DOWN'
        else:
            col = box.column(align=True)
            col.prop(scene, "colormap_start", text="Start", icon='SORT_ASC')
            col.prop(scene, "colormap_end", text="End", icon='SORT_DESC')
            col.prop(scene, "colormap_subdivisions", text="Subdivisions", icon='GRID')
        
        box = layout.box()
        box.label(text="Legend Properties", icon='PROPERTIES')
        col = box.column(align=True)
        col.prop(scene, "legend_name", text="Name", icon='FONT_DATA')
        col.prop(scene, "interpolation", text="Interpolation", icon='IPO_EASE_IN_OUT')
        col.prop(scene, "legend_orientation", text="Orientation", icon='ORIENTATION_VIEW')

        box = layout.box()
        box.label(text="Legend Dimension", icon='ARROW_LEFTRIGHT')
        row = box.row(align=True)
        row.prop(scene, "legend_width", text="Width")
        row.prop(scene, "legend_height", text="Height")

        box = layout.box()
        box.label(text="Scale Legend", icon='FULLSCREEN_ENTER')
        row = box.row(align=True)
        
        icon = 'LINKED' if scene.legend_scale_linked else 'UNLINKED'
        row.prop(scene, "legend_scale_linked", text="", icon=icon, toggle=True)
        row.prop(scene, "legend_scale_mode", text="")
        
        row = box.row(align=True)
        sub = row.row(align=True)
        sub.active = not scene.legend_scale_linked or scene.legend_scale_linked
        sub.prop(scene, "legend_scale_x", text="X")
        
        sub = row.row(align=True)
        sub.active = not scene.legend_scale_linked
        sub.prop(scene, "legend_scale_y", text="Y")

        box = layout.box()
        box.label(text="Legend Position", icon='OBJECT_ORIGIN')  
        col = box.column(align=True)
        col.prop(scene, "legend_position_x", text="X Position")
        col.prop(scene, "legend_position_y", text="Y Position")

        box = layout.box()
        box.label(text="Legend Font", icon='SMALL_CAPS')
        row = box.row()
        row.prop(scene, "legend_font_type", expand=True)
        if scene.legend_font_type == 'SYSTEM':
            row = box.row()
            row.prop(scene, "legend_system_font", text="System Font")
        else:
            row = box.row()
            row.prop(scene, "legend_font", text="Custom Font File")
        
        row = box.row()
        row.prop(scene, "legend_text_color", text="Text Color")

        row = layout.row()
        row.scale_y = 1.5
        row.operator("compositor.png_overlay",
                     text="Generate Legend", icon='RENDERLAYERS')