import bpy

class GridSettings(bpy.types.PropertyGroup):
    unit_measure: bpy.props.EnumProperty(
        name="Unit of Measure",
        description="Select the unit of measure for the distance",
        items=[
            ('nm', "Nanometers", ""),
            ('µm', "Micrometers", ""),
            ('mm', "Millimeters", ""),
            ('cm', "Centimeters", ""),
            ('dm', "Decimeters", ""),
            ('m', "Meters", ""),
            ('dam', "Decameters", ""),
            ('hm', "Hectometers", ""),
            ('km', "Kilometers", "")
        ],
        default='m'
    )
    distance_x: bpy.props.FloatProperty(
        name="Distance X",
        description="Distance between numbers on X axis",
        default=1.0,
        min=0.1,
        max=1000.0
    )
    distance_y: bpy.props.FloatProperty(
        name="Distance Y",
        description="Distance between numbers on Y axis",
        default=1.0,
        min=0.1,
        max=1000.0
    )
    distance_z: bpy.props.FloatProperty(
        name="Distance Z",
        description="Distance between numbers on Z axis",
        default=1.0,
        min=0.1,
        max=1000.0
    )
    subdivisions: bpy.props.IntProperty(
        name="Subdivisions",
        description="Number of subdivisions in each dimension",
        default=2,
        min=1,
        max=20
    )
    show_numbers: bpy.props.BoolProperty(
        name="Show Numbers",
        description="Show numbers on nodes",
        default=True
    )
    text_size: bpy.props.FloatProperty(
        name="Text Size",
        description="Size of the text on nodes",
        default=0.5,
        min=0.1,
        max=5.0
    )
    edge_size: bpy.props.FloatProperty(
        name="Edge Size",
        description="Thickness of the grid edges",
        default=0.05,
        min=0.01,
        max=0.5
    )
    emission_color: bpy.props.FloatVectorProperty(
        name="Emission Color",
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
        max=10.0
    )
    unit_scale: bpy.props.FloatProperty(
        name="Unit Scale",
        description="Scale factor for the scene units",
        default=1.0,
        min=0.00001,
        max=1000.0
    )
    target_unit_measure: bpy.props.EnumProperty(
        name="Target Unit of Measure",
        description="Unit of measure to change the scene to",
        items=[
            ('nm', "Nanometers", ""),
            ('µm', "Micrometers", ""),
            ('mm', "Millimeters", ""),
            ('cm', "Centimeters", ""),
            ('dm', "Decimeters", ""),
            ('m', "Meters", ""),
            ('dam', "Decameters", ""),
            ('hm', "Hectometers", ""),
            ('km', "Kilometers", "")
        ],
        default='m'
    )
    use_custom_font: bpy.props.BoolProperty(
        name="Use Custom Font",
        description="Use a custom font for the text",
        default=False
    )
    custom_font: bpy.props.StringProperty(
        name="Custom Font",
        description="Path to the custom font file",
        default="",
        subtype='FILE_PATH'
    )
    grid_type: bpy.props.EnumProperty(
        name="Grid Type",
        description="Type of grid to generate",
        items=[
            ('CUBIC_INTERNAL_EDGES', "Cubic (Internal Edges)", "Generate a cubic grid with internal edges"),
            ('CUBIC_EXTERIOR', "Cubic (Exterior)", "Generate a cubic grid with only exterior edges"),
            ('EXTERIOR_EDGES_1', "Exterior Edges 1", "Generate only exterior edges (type 1)"),
            ('EXTERIOR_EDGES_2', "Exterior Edges 2", "Generate only exterior edges (type 2)"),
            ('2D_GRID', "2D Grid", "Generate a 2D square grid without internal edges"),
        ],
        default='CUBIC_INTERNAL_EDGES'
    )
    text_offset_x: bpy.props.FloatProperty(
        name="Text Offset X",
        description="Offset for text on X axis",
        default=0.0,
        min=-10.0,
        max=10.0
    )
    text_offset_y: bpy.props.FloatProperty(
        name="Text Offset Y",
        description="Offset for text on Y axis",
        default=0.0,
        min=-10.0,
        max=10.0
    )
    text_offset_z: bpy.props.FloatProperty(
        name="Text Offset Z",
        description="Offset for text on Z axis",
        default=0.0,
        min=-10.0,
        max=10.0
    )
    text_direction_x: bpy.props.EnumProperty(
        name="Text Direction X",
        description="Direction to offset text on X axis",
        items=[
            ('X', "X", "Positive X"),
            ('-X', "-X", "Negative X"),
            ('Y', "Y", "Positive Y"),
            ('-Y', "-Y", "Negative Y"),
            ('Z', "Z", "Positive Z"),
            ('-Z', "-Z", "Negative Z"),
        ],
        default='X'
    )
    text_direction_y: bpy.props.EnumProperty(
        name="Text Direction Y",
        description="Direction to offset text on Y axis",
        items=[
            ('X', "X", "Positive X"),
            ('-X', "-X", "Negative X"),
            ('Y', "Y", "Positive Y"),
            ('-Y', "-Y", "Negative Y"),
            ('Z', "Z", "Positive Z"),
            ('-Z', "-Z", "Negative Z"),
        ],
        default='Y'
    )
    text_direction_z: bpy.props.EnumProperty(
        name="Text Direction Z",
        description="Direction to offset text on Z axis",
        items=[
            ('X', "X", "Positive X"),
            ('-X', "-X", "Negative X"),
            ('Y', "Y", "Positive Y"),
            ('-Y', "-Y", "Negative Y"),
            ('Z', "Z", "Positive Z"),
            ('-Z', "-Z", "Negative Z"),
        ],
        default='Z'
    )

    base_text_size: bpy.props.FloatProperty(
        name="Base Text Size",
        description="Base size of the text on nodes",
        default=0.5,
        min=0.1,
        max=5.0
    )

    base_edge_size: bpy.props.FloatProperty(
        name="Base Edge Size",
        description="Base thickness of the grid edges",
        default=0.05,
        min=0.01,
        max=0.5
    )

    grid_2d_orientation: bpy.props.EnumProperty(
        name="2D Grid Orientation",
        description="Orientation of the 2D grid",
        items=[
            ('XY', "XY Plane", "Orient grid on XY plane"),
            ('XZ', "XZ Plane", "Orient grid on XZ plane"),
            ('YZ', "YZ Plane", "Orient grid on YZ plane"),
            ('-XY', "-XY Plane", "Orient grid on -XY plane"),
            ('-XZ', "-XZ Plane", "Orient grid on -XZ plane"),
            ('-YZ', "-YZ Plane", "Orient grid on -YZ plane"),
        ],
        default='XY'
    )

    length_axis_2d: bpy.props.EnumProperty(
        name="2D Length Axis",
        description="Axis to show lengths for 2D grid",
        items=[
            ('X', "X Axis", "Show lengths on X axis"),
            ('Y', "Y Axis", "Show lengths on Y axis"),
            ('BOTH', "Both Axes", "Show lengths on both X and Y axes"),
        ],
        default='BOTH'
    )