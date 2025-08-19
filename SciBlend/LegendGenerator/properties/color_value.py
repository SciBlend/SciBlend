from bpy.props import FloatVectorProperty, StringProperty
from bpy.types import PropertyGroup

class ColorValue(PropertyGroup):
    color: FloatVectorProperty(
        name="Color",
        subtype='COLOR_GAMMA',
        size=3,
        default=(1.0, 1.0, 1.0)
    )
    value: StringProperty(name="Value", default="")