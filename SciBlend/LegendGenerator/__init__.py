import bpy
from bpy.props import IntProperty, StringProperty, EnumProperty, CollectionProperty, FloatProperty, BoolProperty, FloatVectorProperty
from bpy.types import PropertyGroup
from matplotlib import font_manager

from .operators.png_overlay import PNGOverlayOperator
from .operators.move_color_value import MoveColorValue
from .ui.color_values_list import COLOR_UL_Values_List
from .ui.png_overlay_panel import PNGOverlayPanel
from .properties.color_value import ColorValue
from .properties.legend_settings import LegendSettings
from .utils.gradient_bar import create_gradient_bar
from .utils.compositor_utils import update_legend_position_in_compositor, update_legend_scale_in_compositor
from .utils.color_utils import get_colormap_items, update_colormap


def update_nodes(self, context):
    scene = context.scene
    current_num_nodes = len(scene.colors_values)
    new_num_nodes = scene.num_nodes

    if new_num_nodes > current_num_nodes:
        for i in range(current_num_nodes, new_num_nodes):
            new_color = scene.colors_values.add()
            new_color.color = (1.0, 1.0, 1.0)  
            new_color.value = f"{i/(new_num_nodes-1):.2f}"
    elif new_num_nodes < current_num_nodes:
        for i in range(current_num_nodes - new_num_nodes):
            scene.colors_values.remove(len(scene.colors_values) - 1)


    for i, color_value in enumerate(scene.colors_values):
        color_value.value = f"{i/(new_num_nodes-1):.2f}"

def update_legend_position(self, context):
    update_legend_position_in_compositor(context)

def update_legend_scale(self, context):
    scene = context.scene
    if scene.legend_scale_linked:
        current_x = scene.legend_scale_x
        current_y = scene.legend_scale_y
        
        if self == scene.legend_scale_x and current_x != current_y:
            scene.legend_scale_y = current_x
        elif self == scene.legend_scale_y and current_y != current_x:
            scene.legend_scale_x = current_y
    
    update_legend_scale_in_compositor(context)
    
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

def update_legend_scale_mode(self, context):
    from .utils.compositor_utils import update_legend_scale_in_compositor
    update_legend_scale_in_compositor(context)
    
    # Forzar una actualización de la vista
    for area in context.screen.areas:
        area.tag_redraw()

def update_legend(self, context):
    from .utils.compositor_utils import update_legend_scale_in_compositor
    update_legend_scale_in_compositor(context)

def get_system_fonts(self, context):
    return [(f.name, f.name, f.name) for f in font_manager.fontManager.ttflist]

classes = (
    ColorValue,
    LegendSettings,
    PNGOverlayOperator,
    MoveColorValue,
    COLOR_UL_Values_List,
    PNGOverlayPanel,
)

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            bpy.utils.unregister_class(cls)
            bpy.utils.register_class(cls)

    bpy.types.Scene.legend_settings = bpy.props.PointerProperty(type=LegendSettings)


def unregister():
    del bpy.types.Scene.legend_settings

    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

if __name__ == "__main__":
    register()
