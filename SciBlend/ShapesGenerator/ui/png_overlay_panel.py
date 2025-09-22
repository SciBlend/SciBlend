import bpy
from bpy.types import Panel, UIList
import os

class SHAPESGENERATOR_UL_List(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon='OBJECT_DATAMODE')

class SHAPESGENERATOR_PT_Panel(Panel):
    bl_idname = "SHAPESGENERATOR_PT_main_panel"
    bl_label = "Shapes Generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SciBlend"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.template_list("SHAPESGENERATOR_UL_List", "Shapes", scene, "shapesgenerator_shapes", scene, "shapesgenerator_active_shape_index")

        col = row.column(align=True)
        col.operator("shapesgenerator.new_shape", icon='ADD', text="")
        col.operator("shapesgenerator.delete_shape", icon='REMOVE', text="")

        if len(scene.shapesgenerator_shapes) > 0 and scene.shapesgenerator_active_shape_index >= 0:
            active_shape = scene.shapesgenerator_shapes[scene.shapesgenerator_active_shape_index]
            box = layout.box()
            box.prop(active_shape, "shape_type")

            if active_shape.shape_type == 'GRAPH':
                box.prop(active_shape, "graph_type")
                box.prop(active_shape, "graph_object")
                row = box.row()
                row.prop(active_shape, "graph_attribute", text="Attr A")
                row.prop(active_shape, "graph_attribute_b", text="Attr B")
                if active_shape.graph_type == 'HIST':
                    box.prop(active_shape, "graph_bins")
                box.prop(active_shape, "graph_title")
                row = box.row()
                row.prop(active_shape, "graph_xlabel")
                row.prop(active_shape, "graph_ylabel")
                row = box.row()
                row.prop(active_shape, "graph_color", text="Color")
                row.prop(active_shape, "graph_edgecolor", text="Edge")
                row = box.row()
                row.prop(active_shape, "graph_font_size")
                row.prop(active_shape, "graph_font_color")
                box.prop(active_shape, "graph_grid")
            elif active_shape.shape_type in ['TEXT', 'LATEX']:
                if active_shape.shape_type == 'TEXT':
                    box.prop(active_shape, "text_content")
                    box.prop(active_shape, "font_size")
                    box.prop(active_shape, "font_path")
                else:
                    box.prop(active_shape, "latex_formula")
                box.prop(active_shape, "font_color")
            else:
                if active_shape.shape_type == 'ARROW' or active_shape.shape_type == 'FANCY_ARROW':
                    box.prop(active_shape, "arrow_length")
                    box.prop(active_shape, "arrow_width")
                elif active_shape.shape_type == 'CIRCLE':
                    box.prop(active_shape, "circle_radius")
                elif active_shape.shape_type == 'RECTANGLE':
                    box.prop(active_shape, "rectangle_width")
                    box.prop(active_shape, "rectangle_height")
                elif active_shape.shape_type == 'ELLIPSE':
                    box.prop(active_shape, "ellipse_width")
                    box.prop(active_shape, "ellipse_height")
                elif active_shape.shape_type == 'STAR':
                    box.prop(active_shape, "star_outer_radius")
                    box.prop(active_shape, "star_inner_radius")
                    box.prop(active_shape, "star_points")

                fill_color_row = box.row()
                fill_color_row.prop(active_shape, "fill_color")
                fill_color_row.prop(active_shape, "fill_alpha", slider=True)

                line_color_row = box.row()
                line_color_row.prop(active_shape, "line_color")
                line_color_row.prop(active_shape, "line_alpha", slider=True)

                box.prop(active_shape, "line_size")

            box.prop(active_shape, "rotation")

            dim_row = box.row(align=True)
            dim_row.prop(active_shape, "dimension_x")
            dim_row.prop(active_shape, "dimension_y")
            dim_row.prop(active_shape, "link_dimensions", text="", icon='LINKED' if active_shape.link_dimensions else 'UNLINKED')

            box.prop(active_shape, "position_x", slider=True)
            box.prop(active_shape, "position_y", slider=True)

            scale_row = box.row(align=True)
            scale_row.prop(active_shape, "scale_x", text="Scale X")
            scale_row.prop(active_shape, "scale_y", text="Scale Y")

            if active_shape.shape_type == 'CUSTOM':
                box.operator("shapesgenerator.import_custom_shape", text="Import Custom Shape")
                box.prop(active_shape, "custom_shape_path", text="")
                if active_shape.custom_shape_path:
                    box.label(text=f"Custom shape: {os.path.basename(active_shape.custom_shape_path)}")
                else:
                    box.label(text="No custom shape selected", icon='ERROR')

        layout.operator("shapesgenerator.update_shapes", text="Update Shapes")