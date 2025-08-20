import bpy


def update_resolution(self, context):
    """Update render resolution and frame rate based on cinema format and orientation."""
    format_name = context.scene.cinematography_settings.cinema_format
    print(f"Selected cinema format: {format_name}")
    orientation = context.scene.cinematography_settings.resolution_orientation

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

    if format_name in resolutions:
        width, height = resolutions[format_name]
        print(f"Resolution for {format_name}: {width}x{height}")

        if orientation == 'VERTICAL' and width > height:
            width, height = height, width

        context.scene.cinematography_settings.custom_resolution_x = width
        context.scene.cinematography_settings.custom_resolution_y = height

        new_frame_rate = frame_rates.get(format_name, 24)
        context.scene.cinematography_settings.frame_rate = float(new_frame_rate)
        context.scene.render.fps = new_frame_rate
        print(f"Frame rate set to: {new_frame_rate}")
    else:
        print(f"Unknown format: {format_name}")

    update_linked_resolution(context.scene)


def update_print_resolution(self, context):
    """Update render resolution based on print format, DPI, and orientation."""
    print_format = context.scene.cinematography_settings.print_format
    print(f"Selected print format: {print_format}")
    dpi = context.scene.cinematography_settings.print_dpi
    orientation = context.scene.cinematography_settings.resolution_orientation

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

        context.scene.cinematography_settings.custom_resolution_x = width_pixels
        context.scene.cinematography_settings.custom_resolution_y = height_pixels
    else:
        print(f"Unknown print format: {print_format}")

    update_linked_resolution(context.scene)


def update_linked_resolution(scene):
    """Maintain aspect linking between X and Y custom resolutions when enabled."""
    settings = scene.cinematography_settings
    if settings.resolution_linked:
        if settings.last_updated == 'X':
            settings.custom_resolution_y = int(settings.custom_resolution_x / settings.aspect_ratio)
        else:
            settings.custom_resolution_x = int(settings.custom_resolution_y * settings.aspect_ratio)

    scene.render.resolution_x = settings.custom_resolution_x
    scene.render.resolution_y = settings.custom_resolution_y


def update_resolution_x(self, context):
    """Handle updates to custom X resolution and propagate linked changes."""
    context.scene.cinematography_settings.last_updated = 'X'
    update_linked_resolution(context.scene)


def update_resolution_y(self, context):
    """Handle updates to custom Y resolution and propagate linked changes."""
    context.scene.cinematography_settings.last_updated = 'Y'
    update_linked_resolution(context.scene)


def update_frame_rate(self, context):
    """Apply frame rate changes to Blender render settings."""
    context.scene.render.fps = int(context.scene.cinematography_settings.frame_rate)
    print(f"Frame rate updated to: {context.scene.render.fps}")


class CINEMATOGRAPHY_OT_set_render_resolution(bpy.types.Operator):
    """Operator to set the render resolution using custom X and Y values."""
    bl_idname = "cinematography.set_render_resolution"
    bl_label = "Set Render Resolution"
    bl_options = {'REGISTER', 'UNDO'}

    resolution_x: bpy.props.IntProperty(name="X Resolution")
    resolution_y: bpy.props.IntProperty(name="Y Resolution")

    def execute(self, context):
        context.scene.cinematography_settings.custom_resolution_x = self.resolution_x
        context.scene.cinematography_settings.custom_resolution_y = self.resolution_y
        update_linked_resolution(context.scene)
        return {'FINISHED'}


class CINEMATOGRAPHY_OT_set_print_resolution(bpy.types.Operator):
    """Operator to set the print resolution by selecting a print format."""
    bl_idname = "cinematography.set_print_resolution"
    bl_label = "Set Print Resolution"
    bl_options = {'REGISTER', 'UNDO'}

    format: bpy.props.StringProperty()

    def execute(self, context):
        context.scene.cinematography_settings.print_format = self.format
        update_print_resolution(self, context)
        return {'FINISHED'}


class CINEMATOGRAPHY_OT_toggle_resolution_link(bpy.types.Operator):
    """Operator to toggle linking between X and Y resolution values."""
    bl_idname = "cinematography.toggle_resolution_link"
    bl_label = "Toggle Resolution Link"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cset = context.scene.cinematography_settings
        cset.resolution_linked = not cset.resolution_linked
        if cset.resolution_linked:
            cset.aspect_ratio = cset.custom_resolution_x / cset.custom_resolution_y
        update_linked_resolution(context.scene)
        return {'FINISHED'}


classes = (
    CINEMATOGRAPHY_OT_set_render_resolution,
    CINEMATOGRAPHY_OT_set_print_resolution,
    CINEMATOGRAPHY_OT_toggle_resolution_link,
)


def register():
    """Register cinematography render settings operators."""
    print("Registering render_settings properties")
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"Error registering {cls.__name__}: {str(e)}")


def unregister():
    """Unregister cinematography render settings operators."""
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"Error unregistering {cls.__name__}: {str(e)}")