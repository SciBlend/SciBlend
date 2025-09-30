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
    try:
        sc = getattr(bpy.context, 'scene', None)
        settings = getattr(sc, 'legend_settings', None) if sc else None
        if settings and getattr(settings, 'legend_enabled', True):
            bpy.ops.compositor.png_overlay()
    except Exception:
        pass


def _update_legend_enabled(self, context):
    """Toggle compositor overlay visibility based on the legend_enabled setting."""
    try:
        from ..utils.compositor_utils import set_legend_visibility
        set_legend_visibility(context, bool(self.legend_enabled))
    except Exception:
        pass


def _get_system_fonts(self, context):
    """Enumerate system fonts using matplotlib's font manager (lazy import)."""
    try:
        from matplotlib import font_manager
        return [(f.name, f.name, f.name) for f in font_manager.fontManager.ttflist]
    except Exception:
        return []


def _on_change_orientation(self, context):
    """Set default legend parameters based on the selected orientation.

    Vertical:
    - Dimensions: 1920x1080
    - Scale: 0.85x (X and Y)
    - Position: X 40.00, Y 0
    - Font size: 30.0 pt

    Horizontal:
    - Dimensions: 1920x1080
    - Scale: 0.6x (X and Y)
    - Position: X 0, Y -15.00
    - Font size: 25.0 pt
    """
    scene = context.scene
    settings = scene.legend_settings

    if settings.legend_orientation == 'VERTICAL':
        settings.legend_width = 1920
        settings.legend_height = 1080
        settings.legend_scale_x = 0.85
        settings.legend_scale_y = 0.85
        settings.legend_position_x = 40.0
        settings.legend_position_y = 0.0
        settings.legend_text_size_pt = 30.0
    else:
        settings.legend_width = 1920
        settings.legend_height = 1080
        settings.legend_scale_x = 0.6
        settings.legend_scale_y = 0.6
        settings.legend_position_x = 0.0
        settings.legend_position_y = -15.0
        settings.legend_text_size_pt = 25.0

    try:
        if getattr(settings, 'legend_enabled', True):
            bpy.ops.compositor.png_overlay()
    except Exception:
        pass


class LegendSettings(PropertyGroup):
    """Grouped settings for Legend Generator to avoid stray Scene properties."""

    colors_values: CollectionProperty(type=ColorValue)
    color_values_index: IntProperty()

    legend_enabled: BoolProperty(
        name="Legend Enabled",
        description="Enable legend generation and updates",
        default=True,
        update=_update_legend_enabled,
    )

    num_nodes: IntProperty(
        name="Number of Nodes",
        default=2,
        min=2,
        update=update_nodes,
    )

    multi_legend_count: IntProperty(
        name="Legends",
        description="How many legends to compose in a single PNG (one per collection)",
        default=1,
        min=1,
        soft_max=6,
        update=_update_legend,
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
        update=_update_legend,
    )

    legend_orientation: EnumProperty(
        name="Orientation",
        items=[
            ('HORIZONTAL', "Horizontal", "Horizontal orientation"),
            ('VERTICAL', "Vertical", "Vertical orientation"),
        ],
        default='HORIZONTAL',
        update=_on_change_orientation,
    )

    legend_position_x: FloatProperty(
        name="X Position",
        default=0.0,
        update=_update_legend_position,
    )

    legend_position_y: FloatProperty(
        name="Y Position",
        default=-15.0,
        update=_update_legend_position,
    )

    legend_text_size_pt: FloatProperty(
        name="Text Size (pt)",
        description="Legend text size in points",
        default=25.0,
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
        default=0.6,
        min=0.1,
        max=10.0,
        update=_update_legend_scale,
    )

    legend_scale_y: FloatProperty(
        name="Y Scale",
        description="Scale of the legend in Y direction",
        default=0.6,
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
        default=1920,
        min=1,
    )

    legend_height: IntProperty(
        name="Height",
        description="Height of the legend in pixels",
        default=1080,
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

    legend_label_padding: FloatProperty(
        name="Label Padding",
        description="Space between the colorbar and its label (points)",
        default=10.0,
        min=0.0,
        max=200.0,
        update=_update_legend,
    )

    legend_label_offset_pct: FloatProperty(
        name="Label Offset (%)",
        description="Position of the label along the colorbar, in percent of axis length",
        default=50.0,
        min=0.0,
        max=100.0,
        update=_update_legend,
    )

    legend_decimal_places: IntProperty(
        name="Decimal Places",
        description="Number of decimal places for numeric tick labels",
        default=2,
        min=0,
        max=12,
        update=_update_legend,
    )

    legend_number_format: EnumProperty(
        name="Number Format",
        description="Formatting style for numeric tick labels",
        items=[
            ('FIXED', "Fixed", "Fixed-point format, e.g., 1.23"),
            ('SCIENTIFIC_E', "Scientific (e)", "Scientific notation with 'e', e.g., 1.23e-10"),
            ('SCIENTIFIC_TEX', "Scientific (×10^)", "Scientific notation using ×10^, e.g., 1.23×10^-10"),
            ('GENERAL', "General", "General format with minimal digits"),
        ],
        default='FIXED',
        update=_update_legend,
    ) 