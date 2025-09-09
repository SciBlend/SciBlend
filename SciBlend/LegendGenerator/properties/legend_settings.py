import bpy
from bpy.props import (
    IntProperty,
    StringProperty,
    EnumProperty,
    CollectionProperty,
    FloatProperty,
    BoolProperty,
    FloatVectorProperty,
)
from bpy.types import PropertyGroup
from matplotlib import font_manager
from ..utils.color_utils import get_colormap_items, update_colormap
from .color_value import ColorValue
from ..utils.compositor_utils import (
    update_legend_position_in_compositor,
    update_legend_scale_in_compositor,
)


def _on_toggle_auto_from_shader(self, context):
    """Handle enabling of automatic legend updates from the active object's shader and trigger an initial overlay render."""
    scene = context.scene
    settings = scene.legend_settings
    if settings.auto_from_shader:
        try:
            from ..operators.choose_shader import update_legend_from_shader
            obj = getattr(context, 'active_object', None)
            update_legend_from_shader(scene, obj)
        except Exception:
            pass
        try:
            bpy.ops.compositor.png_overlay()
        except Exception:
            pass


def update_nodes(self, context):
    """Synchronize the number of ColorValue items with `num_nodes`."""
    scene = context.scene
    settings = scene.legend_settings
    current_num_nodes = len(settings.colors_values)
    new_num_nodes = settings.num_nodes

    if new_num_nodes > current_num_nodes:
        for i in range(current_num_nodes, new_num_nodes):
            new_color = settings.colors_values.add()
            new_color.color = (1.0, 1.0, 1.0)
            new_color.value = f"{i/(new_num_nodes-1):.2f}"
    elif new_num_nodes < current_num_nodes:
        for _ in range(current_num_nodes - new_num_nodes):
            settings.colors_values.remove(len(settings.colors_values) - 1)

    for i, color_value in enumerate(settings.colors_values):
        color_value.value = f"{i/(new_num_nodes-1):.2f}"


def _update_legend_position(self, context):
    """Update compositor node tree when legend position changes."""
    update_legend_position_in_compositor(context)


def _update_legend_scale(self, context):
    """Link X and Y scale values when needed and update compositor."""
    scene = context.scene
    settings = scene.legend_settings

    if settings.legend_scale_linked:
        if settings.legend_scale_y != settings.legend_scale_x:
            settings.legend_scale_y = settings.legend_scale_x

    update_legend_scale_in_compositor(context)
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


def _update_legend_scale_mode(self, context):
    """Update the legend scale mode in compositor."""
    update_legend_scale_in_compositor(context)
    for area in context.screen.areas:
        area.tag_redraw()


def _update_legend(self, context):
    """Generic update to refresh compositor when legend attributes change."""
    update_legend_scale_in_compositor(context)


def _get_system_fonts(self, context):
    """Enumerate system fonts using matplotlib's font manager."""
    return [(f.name, f.name, f.name) for f in font_manager.fontManager.ttflist]


class LegendSettings(PropertyGroup):
    """Grouped settings for Legend Generator to avoid stray Scene properties."""

    colors_values: CollectionProperty(type=ColorValue)
    color_values_index: IntProperty()

    num_nodes: IntProperty(
        name="Number of Nodes",
        default=2,
        min=2,
        update=update_nodes,
    )

    legend_name: StringProperty(
        name="Legend Name",
        description="Name of the legend that will appear on the colorbar",
        default="Legend",
        update=_update_legend,
    )

    interpolation: EnumProperty(
        name="Interpolation",
        items=[
            ('LINEAR', "Linear", "Linear interpolation"),
            ('STEP', "Step", "Step interpolation"),
            ('CUBIC', "Cubic", "Cubic interpolation"),
            ('NEAREST', "Nearest", "Nearest neighbor interpolation"),
        ],
        default='LINEAR',
    )

    legend_orientation: EnumProperty(
        name="Orientation",
        items=[
            ('HORIZONTAL', "Horizontal", "Horizontal orientation"),
            ('VERTICAL', "Vertical", "Vertical orientation"),
        ],
        default='HORIZONTAL',
    )

    legend_position_x: FloatProperty(
        name="X Position",
        default=0.0,
        update=_update_legend_position,
    )

    legend_position_y: FloatProperty(
        name="Y Position",
        default=0.0,
        update=_update_legend_position,
    )

    legend_text_size_pt: FloatProperty(
        name="Text Size (pt)",
        description="Legend text size in points",
        default=12.0,
        min=6.0,
        max=72.0,
        step=10,
        precision=1,
        update=_update_legend,
    )

    auto_from_shader: BoolProperty(
        name="Auto from Shader",
        description="When enabled, use selected object's shader to update the legend automatically",
        default=False,
        update=_on_toggle_auto_from_shader,
    )

    legend_scale_uniform: BoolProperty(
        name="Uniform Scale",
        default=True,
        update=_update_legend_scale,
    )

    legend_scale_x: FloatProperty(
        name="X Scale",
        description="Scale of the legend in X direction",
        default=1.0,
        min=0.1,
        max=10.0,
        update=_update_legend_scale,
    )

    legend_scale_y: FloatProperty(
        name="Y Scale",
        description="Scale of the legend in Y direction",
        default=1.0,
        min=0.1,
        max=10.0,
        update=_update_legend_scale,
    )

    legend_scale_linked: BoolProperty(
        name="Link Scale",
        description="Link X and Y scale values",
        default=True,
        update=_update_legend_scale,
    )


    colormap: EnumProperty(
        name="Colormap",
        description="Select a scientific colormap or use custom colors",
        items=get_colormap_items(),
        default='CUSTOM',
        update=update_colormap,
    )

    colormap_start: FloatProperty(
        name="Start Value",
        description="Start value of the colormap range",
        default=0.0,
        update=update_colormap,
    )

    colormap_end: FloatProperty(
        name="End Value",
        description="End value of the colormap range",
        default=1.0,
        update=update_colormap,
    )

    colormap_subdivisions: IntProperty(
        name="Subdivisions",
        description="Number of subdivisions in the colormap",
        default=10,
        min=2,
        max=100,
        update=update_colormap,
    )

    legend_width: IntProperty(
        name="Width",
        description="Width of the legend in pixels",
        default=200,
        min=1,
    )

    legend_height: IntProperty(
        name="Height",
        description="Height of the legend in pixels",
        default=600,
        min=1,
    )

    legend_font_type: EnumProperty(
        name="Font Type",
        description="Choose between system font or custom font",
        items=[
            ('SYSTEM', "System Font", "Use a system font"),
            ('CUSTOM', "Custom Font", "Use a custom font file"),
        ],
        default='SYSTEM',
        update=_update_legend,
    )

    legend_system_font: EnumProperty(
        name="System Font",
        description="Choose a system font",
        items=_get_system_fonts,
        update=_update_legend,
    )

    legend_font: StringProperty(
        name="Custom Font File",
        description="Path to custom font file",
        subtype='FILE_PATH',
        update=_update_legend,
    )

    legend_text_color: FloatVectorProperty(
        name="Legend Text Color",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color of the legend text",
        update=_update_legend,
    ) 