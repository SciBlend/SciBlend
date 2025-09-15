import bpy
from bpy.types import PropertyGroup
from bpy.props import FloatVectorProperty, FloatProperty


class ColorRampColor(PropertyGroup):
    """A single color stop entry for the custom ColorRamp collection."""
    color: FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color of the ColorRamp stop",
    )
    position: FloatProperty(
        name="Position",
        default=0.5,
        min=0.0,
        max=1.0,
        description="Position of the color stop",
    ) 