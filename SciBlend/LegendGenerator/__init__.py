import bpy
from bpy.props import IntProperty, StringProperty, EnumProperty, CollectionProperty, FloatProperty, BoolProperty, FloatVectorProperty
from bpy.types import PropertyGroup
from matplotlib import font_manager

from .operators.png_overlay import PNGOverlayOperator
from .operators.move_color_value import MoveColorValue
from .ui.color_values_list import COLOR_UL_Values_List
from .ui.png_overlay_panel import PNGOverlayPanel
from .properties.color_value import ColorValue
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

    bpy.types.Scene.colors_values = CollectionProperty(type=ColorValue)
    bpy.types.Scene.color_values_index = IntProperty()
    bpy.types.Scene.num_nodes = IntProperty(
        name="Number of Nodes", 
        default=2, 
        min=2, 
        update=update_nodes
    )
    bpy.types.Scene.legend_name = StringProperty(
        name="Legend Name",
        description="Name of the legend that will appear on the colorbar",
        default="Legend",
        update=update_legend
    )
    bpy.types.Scene.interpolation = EnumProperty(
        name="Interpolation",
        items=[
            ('LINEAR', "Linear", "Linear interpolation"),
            ('STEP', "Step", "Step interpolation"),
            ('CUBIC', "Cubic", "Cubic interpolation"),
            ('NEAREST', "Nearest", "Nearest neighbor interpolation")
        ],
        default='LINEAR'
    )
    bpy.types.Scene.legend_orientation = EnumProperty(
        name="Orientation",
        items=[
            ('HORIZONTAL', "Horizontal", "Horizontal orientation"),
            ('VERTICAL', "Vertical", "Vertical orientation")
        ],
        default='HORIZONTAL'
    )
    bpy.types.Scene.legend_position_x = FloatProperty(
        name="X Position",
        default=0.0,
        update=update_legend_position
    )
    bpy.types.Scene.legend_position_y = FloatProperty(
        name="Y Position",
        default=0.0,
        update=update_legend_position
    )
    bpy.types.Scene.legend_scale_uniform = BoolProperty(
        name="Uniform Scale",
        default=True,
        update=update_legend_scale
    )
    bpy.types.Scene.legend_scale_x = FloatProperty(
        name="X Scale",
        description="Scale of the legend in X direction",
        default=1.0,
        min=0.1,
        max=10.0,
        update=update_legend_scale
    )
    bpy.types.Scene.legend_scale_y = FloatProperty(
        name="Y Scale",
        description="Scale of the legend in Y direction",
        default=1.0,
        min=0.1,
        max=10.0,
        update=update_legend_scale
    )
    bpy.types.Scene.legend_scale_linked = BoolProperty(
        name="Link Scale",
        description="Link X and Y scale values",
        default=True,
        update=update_legend_scale
    )
    
    bpy.types.Scene.legend_scale_mode = EnumProperty(
        name="Scale Mode",
        items=[
            ('SCENE_SIZE', "Scene Size", "Scale relative to scene size"),
            ('RENDER_SIZE_FIT', "Render Size (Fit)", "Scale relative to render size, fit to render"),
            ('RENDER_SIZE_CROP', "Render Size (Crop)", "Scale relative to render size, crop to render")
        ],
        default='SCENE_SIZE',
        update=update_legend_scale_mode
    )
    
    bpy.types.Scene.colormap = EnumProperty(
        name="Colormap",
        description="Select a scientific colormap or use custom colors",
        items=get_colormap_items(),
        default='CUSTOM',
        update=update_colormap
    )
    
    bpy.types.Scene.colormap_start = FloatProperty(
        name="Start Value",
        description="Start value of the colormap range",
        default=0.0,
        update=update_colormap
    )
    bpy.types.Scene.colormap_end = FloatProperty(
        name="End Value",
        description="End value of the colormap range",
        default=1.0,
        update=update_colormap
    )
    bpy.types.Scene.colormap_subdivisions = IntProperty(
        name="Subdivisions",
        description="Number of subdivisions in the colormap",
        default=10,
        min=2,
        max=100,
        update=update_colormap
    )

    bpy.types.Scene.legend_width = IntProperty(
        name="Width",
        description="Width of the legend in pixels",
        default=200,
        min=1
    )
    bpy.types.Scene.legend_height = IntProperty(
        name="Height",
        description="Height of the legend in pixels",
        default=600,
        min=1
    )

    bpy.types.Scene.legend_font_type = EnumProperty(
        name="Font Type",
        description="Choose between system font or custom font",
        items=[
            ('SYSTEM', "System Font", "Use a system font"),
            ('CUSTOM', "Custom Font", "Use a custom font file")
        ],
        default='SYSTEM',
        update=update_legend
    )

    bpy.types.Scene.legend_system_font = EnumProperty(
        name="System Font",
        description="Choose a system font",
        items=get_system_fonts,
        update=update_legend
    )

    bpy.types.Scene.legend_font = StringProperty(
        name="Custom Font File",
        description="Path to custom font file",
        subtype='FILE_PATH',
        update=update_legend
    )

    bpy.types.Scene.legend_text_color = FloatVectorProperty(
        name="Legend Text Color",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),  
        min=0.0,
        max=1.0,
        description="Color del texto de la leyenda",
        update=update_legend
    )

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

    del bpy.types.Scene.colors_values
    del bpy.types.Scene.color_values_index
    del bpy.types.Scene.num_nodes
    del bpy.types.Scene.legend_name
    del bpy.types.Scene.interpolation
    del bpy.types.Scene.legend_orientation
    del bpy.types.Scene.legend_position_x
    del bpy.types.Scene.legend_position_y
    del bpy.types.Scene.legend_scale_uniform
    del bpy.types.Scene.legend_scale_x
    del bpy.types.Scene.legend_scale_y
    del bpy.types.Scene.legend_scale_linked
    
    del bpy.types.Scene.colormap
    
    del bpy.types.Scene.colormap_start
    del bpy.types.Scene.colormap_end
    del bpy.types.Scene.colormap_subdivisions

    del bpy.types.Scene.legend_width
    del bpy.types.Scene.legend_height

    del bpy.types.Scene.legend_scale_mode

    del bpy.types.Scene.legend_font_type
    del bpy.types.Scene.legend_system_font
    del bpy.types.Scene.legend_font

    del bpy.types.Scene.legend_text_color

if __name__ == "__main__":
    register()
