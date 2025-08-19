import bpy


class AnnotationProperties(bpy.types.PropertyGroup):
    annotation_text: bpy.props.StringProperty(
        name="Text",
        default="Annotation"
    )
    scale_options = [
        ('MM', 'Millimeters', 'Set scale to millimeters'),
        ('CM', 'Centimeters', 'Set scale to centimeters'),
        ('DM', 'Decimeters', 'Set scale to decimeters'),
        ('M', 'Meters', 'Set scale to meters'),
        ('DAM', 'Decameters', 'Set scale to decameters'),
        ('HM', 'Hectometers', 'Set scale to hectometers'),
        ('KM', 'Kilometers', 'Set scale to kilometers')
    ]

    annotation_scale: bpy.props.EnumProperty(
        name="Scale",
        description="Choose the scale for the annotation",
        items=scale_options,
        default='M'
    )

    annotation_length: bpy.props.FloatProperty(
        name="Length",
        default=1.0,
        min=0.001,
        max=1000.0
    )
    annotation_thickness: bpy.props.FloatProperty(
        name="Thickness",
        default=0.05,
        min=0.001,
        max=10.0
    )
    text_size: bpy.props.FloatProperty(
        name="Text Size",
        default=0.2,
        min=0.01,
        max=10.0
    )
    text_distance: bpy.props.FloatProperty(
        name="Text Distance",
        default=0.1,
        min=0.0,
        max=10.0
    )
    annotation_color: bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0, 1.0),
        size=4,
        min=0.0,
        max=1.0
    )
    emission_strength: bpy.props.FloatProperty(
        name="Emission Strength",
        default=1.0,
        min=0.0,
        max=100.0
    )