import bpy
from bpy.types import PropertyGroup
from bpy.props import EnumProperty, FloatProperty, BoolProperty, FloatVectorProperty, StringProperty


def _get_filter_attribute_items(self, context):
    """Get available attributes for the filter dropdown.
    
    Parameters
    ----------
    self : AttributeFilterItem
        The filter item.
    context : bpy.types.Context
        Blender context.
        
    Returns
    -------
    list
        List of enum items.
    """
    items = []
    settings = getattr(context.scene, 'shader_generator_settings', None)
    if not settings or not hasattr(settings, 'collection_shaders'):
        return [('', "No attributes", "")]
    
    if settings.active_collection_index < 0 or settings.active_collection_index >= len(settings.collection_shaders):
        return [('', "No attributes", "")]
    
    item = settings.collection_shaders[settings.active_collection_index]
    coll = bpy.data.collections.get(item.collection_name)
    if not coll:
        return [('', "No attributes", "")]
    
    seen = set()
    for obj in coll.objects:
        if obj.type != 'MESH' or not obj.data.attributes:
            continue
        for attr in obj.data.attributes:
            if attr.name not in seen:
                seen.add(attr.name)
                items.append((attr.name, attr.name, f"Attribute: {attr.name}"))
    
    if not items:
        return [('', "No attributes", "")]
    
    return items


class AttributeFilterItem(PropertyGroup):
    """A single filter rule that compares a mesh attribute against a threshold value."""

    attribute_name: EnumProperty(
        name="Attribute",
        description="Mesh attribute to test",
        items=_get_filter_attribute_items,
    )

    operator: EnumProperty(
        name="Operator",
        description="Comparison operator",
        items=[
            ('EQUAL', "==", "Equal to"),
            ('NOT_EQUAL', "!=", "Not equal to"),
            ('GREATER_THAN', ">", "Greater than"),
            ('LESS_THAN', "<", "Less than"),
            ('GREATER_EQUAL', ">=", "Greater than or equal to"),
            ('LESS_EQUAL', "<=", "Less than or equal to"),
            ('IS_NAN', "is NaN", "Value is NaN or invalid"),
            ('IS_NOT_NAN', "not NaN", "Value is not NaN"),
        ],
        default='EQUAL',
    )

    value: FloatProperty(
        name="Value",
        description="Threshold value for comparison",
        default=0.0,
    )

    enabled: BoolProperty(
        name="Enabled",
        description="Whether this filter rule is active",
        default=True,
    )

    display_mode: EnumProperty(
        name="Display Mode",
        description="How to display faces matching this rule",
        items=[
            ('SOLID_COLOR', "Solid Color", "Apply a solid color"),
            ('TRANSPARENT', "Transparent", "Make matching faces transparent"),
            ('MATERIAL', "Material", "Use an existing material"),
        ],
        default='SOLID_COLOR',
    )

    display_color: FloatVectorProperty(
        name="Color",
        description="Color to apply to matching faces",
        subtype='COLOR',
        size=3,
        default=(0.8, 0.2, 0.2),
        min=0.0,
        max=1.0,
    )

    display_material: StringProperty(
        name="Material",
        description="Material to apply to matching faces",
        default="",
    )
