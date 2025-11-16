import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, BoolProperty


class CollectionShaderItem(PropertyGroup):
    """Track the association between a collection and its Shader Generator material."""
    
    collection_name: StringProperty(
        name="Collection Name",
        description="Name of the collection",
        default="",
    )
    
    material_name: StringProperty(
        name="Material Name",
        description="Name of the material associated with this collection",
        default="",
    )
    
    is_shader_generator: BoolProperty(
        name="Is Shader Generator",
        description="Whether this material was created by Shader Generator",
        default=True,
    )

