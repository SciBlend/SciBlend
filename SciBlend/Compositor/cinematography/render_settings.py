import bpy

def update_resolution(self, context):
    format = context.scene.cinema_format
    print(f"Selected cinema format: {format}") 
    orientation = context.scene.resolution_orientation
    resolutions = {
        '2K_DCI': (2048, 1080),
        '4K_DCI': (4096, 2160),
        '8K_DCI': (8192, 4320),
        'HD': (1280, 720),
        'FULL_HD': (1920, 1080),
        '2K': (2048, 1152),
        '4K_UHD': (3840, 2160),
        '8K_UHD': (7680, 4320),
        'ACADEMY_2_39_1': (2048, 858),
        'CINEMASCOPE': (2048, 858),
        'IMAX': (4096, 3072),
    }
    frame_rates = {
        '2K_DCI': 24,
        '4K_DCI': 24,
        '8K_DCI': 24,
        'HD': 30,
        'FULL_HD': 30,
        '2K': 24,
        '4K_UHD': 30,
        '8K_UHD': 30,
        'ACADEMY_2_39_1': 24,
        'CINEMASCOPE': 24,
        'IMAX': 24,
    }
    if format in resolutions:
        width, height = resolutions[format]
        print(f"Resolution for {format}: {width}x{height}")  
        if orientation == 'VERTICAL' and width > height:
            width, height = height, width
        context.scene.custom_resolution_x = width
        context.scene.custom_resolution_y = height
        new_frame_rate = frame_rates.get(format, 24)
        context.scene.frame_rate = new_frame_rate
        context.scene.render.fps = new_frame_rate  
        print(f"Frame rate set to: {new_frame_rate}")  
    else:
        print(f"Unknown format: {format}") 
    update_linked_resolution(context.scene)

def update_print_resolution(self, context):
    print_format = context.scene.print_format
    print(f"Selected print format: {print_format}") 
    dpi = context.scene.print_dpi
    orientation = context.scene.resolution_orientation
    print_sizes = {
        'A4': (210, 297),
        'A3': (297, 420),
        'A2': (420, 594),
        'A1': (594, 841),
        'A0': (841, 1189),
        'LETTER': (216, 279),
        'LEGAL': (216, 356),
        'TABLOID': (279, 432),
    }
    if print_format in print_sizes:
        width_mm, height_mm = print_sizes[print_format]
        if orientation == 'VERTICAL' and width_mm > height_mm:
            width_mm, height_mm = height_mm, width_mm
        width_inches = width_mm / 25.4
        height_inches = height_mm / 25.4
        width_pixels = int(width_inches * dpi)
        height_pixels = int(height_inches * dpi)
        print(f"Resolution for {print_format}: {width_pixels}x{height_pixels}") 
        context.scene.custom_resolution_x = width_pixels
        context.scene.custom_resolution_y = height_pixels
    else:
        print(f"Unknown print format: {print_format}") 
    update_linked_resolution(context.scene)

def update_linked_resolution(scene):
    if scene.resolution_linked:
        if scene.last_updated == 'X':
            scene.custom_resolution_y = int(scene.custom_resolution_x / scene.aspect_ratio)
        else:
            scene.custom_resolution_x = int(scene.custom_resolution_y * scene.aspect_ratio)
    
    scene.render.resolution_x = scene.custom_resolution_x
    scene.render.resolution_y = scene.custom_resolution_y

def update_resolution_x(self, context):
    context.scene.last_updated = 'X'
    update_linked_resolution(context.scene)

def update_resolution_y(self, context):
    context.scene.last_updated = 'Y'
    update_linked_resolution(context.scene)

def update_frame_rate(self, context):
    context.scene.render.fps = int(context.scene.frame_rate)
    print(f"Frame rate updated to: {context.scene.render.fps}") 

class CINEMATOGRAPHY_OT_set_render_resolution(bpy.types.Operator):
    bl_idname = "cinematography.set_render_resolution"
    bl_label = "Set Render Resolution"
    bl_options = {'REGISTER', 'UNDO'}

    resolution_x: bpy.props.IntProperty(name="X Resolution")
    resolution_y: bpy.props.IntProperty(name="Y Resolution")

    def execute(self, context):
        context.scene.custom_resolution_x = self.resolution_x
        context.scene.custom_resolution_y = self.resolution_y
        update_linked_resolution(context.scene)
        return {'FINISHED'}

class CINEMATOGRAPHY_OT_set_print_resolution(bpy.types.Operator):
    bl_idname = "cinematography.set_print_resolution"
    bl_label = "Set Print Resolution"
    bl_options = {'REGISTER', 'UNDO'}

    format: bpy.props.StringProperty()

    def execute(self, context):
        context.scene.print_format = self.format
        update_print_resolution(self, context)
        return {'FINISHED'}

class CINEMATOGRAPHY_OT_toggle_resolution_link(bpy.types.Operator):
    bl_idname = "cinematography.toggle_resolution_link"
    bl_label = "Toggle Resolution Link"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.resolution_linked = not context.scene.resolution_linked
        if context.scene.resolution_linked:
            context.scene.aspect_ratio = context.scene.custom_resolution_x / context.scene.custom_resolution_y
        update_linked_resolution(context.scene)
        return {'FINISHED'}

classes = (
    CINEMATOGRAPHY_OT_set_render_resolution,
    CINEMATOGRAPHY_OT_set_print_resolution,
    CINEMATOGRAPHY_OT_toggle_resolution_link,
)

def register():
    print("Registering render_settings properties")  # Log
    bpy.types.Scene.cinema_format = bpy.props.EnumProperty(
        items=[
            ('2K_DCI', "2K DCI", "2048x1080"),
            ('4K_DCI', "4K DCI", "4096x2160"),
            ('8K_DCI', "8K DCI", "8192x4320"),
            ('HD', "HD", "1280x720"),
            ('FULL_HD', "Full HD", "1920x1080"),
            ('2K', "2K", "2048x1152"),
            ('4K_UHD', "4K UHD", "3840x2160"),
            ('8K_UHD', "8K UHD", "7680x4320"),
            ('ACADEMY_2_39_1', "Academy 2.39:1", "2048x858"),
            ('CINEMASCOPE', "Cinemascope", "2048x858"),
            ('IMAX', "IMAX", "4096x3072"),
        ],
        name="Cinema Format",
        default='FULL_HD',
        update=update_resolution
    )
    bpy.types.Scene.resolution_orientation = bpy.props.EnumProperty(
        items=[
            ('HORIZONTAL', "Horizontal", "Horizontal orientation"),
            ('VERTICAL', "Vertical", "Vertical orientation"),
        ],
        name="Resolution Orientation",
        default='HORIZONTAL',
        update=update_resolution
    )
    bpy.types.Scene.frame_rate = bpy.props.FloatProperty(
        name="Frame Rate",
        default=24.0,
        min=1.0,
        max=120.0,
        precision=3,
        step=100,
        update=update_frame_rate 
    )
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"Error registering {cls.__name__}: {str(e)}")
    register_properties()

def unregister():
    del bpy.types.Scene.cinema_format
    del bpy.types.Scene.resolution_orientation
    del bpy.types.Scene.frame_rate
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"Error unregistering {cls.__name__}: {str(e)}")
    unregister_properties()

def register_properties():
    bpy.types.Scene.print_dpi = bpy.props.IntProperty(
        name="Print DPI",
        description="DPI for print resolutions",
        default=300,
        min=72,
        max=1200,
        update=update_print_resolution  
    )
    bpy.types.Scene.print_format = bpy.props.EnumProperty(
        items=[
            ('A4', "A4", "210x297mm"),
            ('A3', "A3", "297x420mm"),
            ('A2', "A2", "420x594mm"),
            ('A1', "A1", "594x841mm"),
            ('A0', "A0", "841x1189mm"),
            ('LETTER', "Letter", "216x279mm"),
            ('LEGAL', "Legal", "216x356mm"),
            ('TABLOID', "Tabloid", "279x432mm"),
        ],
        name="Print Format",
        default='A4',
        update=update_print_resolution
    )
    bpy.types.Scene.resolution_linked = bpy.props.BoolProperty(
        name="Link Resolution",
        description="Link X and Y resolutions",
        default=False
    )
    bpy.types.Scene.aspect_ratio = bpy.props.FloatProperty(
        name="Aspect Ratio",
        description="Aspect ratio of the resolution",
        default=1.0
    )
    bpy.types.Scene.last_updated = bpy.props.StringProperty(
        name="Last Updated",
        description="Which resolution was last updated",
        default='Y'
    )
    bpy.types.Scene.custom_resolution_x = bpy.props.IntProperty(
        name="X",
        description="Number of horizontal pixels in the rendered image",
        default=1920,
        min=4,
        max=65536,
        update=update_resolution_x
    )
    bpy.types.Scene.custom_resolution_y = bpy.props.IntProperty(
        name="Y",
        description="Number of vertical pixels in the rendered image",
        default=1080,
        min=4,
        max=65536,
        update=update_resolution_y
    )

def unregister_properties():
    print("Unregistering render_settings properties") 
    if hasattr(bpy.types.Scene, "cinema_format"):
        del bpy.types.Scene.cinema_format
    del bpy.types.Scene.print_dpi
    del bpy.types.Scene.print_format
    del bpy.types.Scene.resolution_linked
    del bpy.types.Scene.aspect_ratio
    del bpy.types.Scene.last_updated
    del bpy.types.Scene.custom_resolution_x
    del bpy.types.Scene.custom_resolution_y