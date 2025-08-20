import bpy
from bpy.types import PropertyGroup
from .camera_manager import CameraListItem, update_camera_list_index


def update_linked_resolution(scene):
	"""Apply aspect ratio linkage and sync to render resolution."""
	if scene.cinematography_settings.resolution_linked:
		if scene.cinematography_settings.last_updated == 'X':
			scene.cinematography_settings.custom_resolution_y = int(
				scene.cinematography_settings.custom_resolution_x / scene.cinematography_settings.aspect_ratio
			)
		else:
			scene.cinematography_settings.custom_resolution_x = int(
				scene.cinematography_settings.custom_resolution_y * scene.cinematography_settings.aspect_ratio
			)
	
	scene.render.resolution_x = scene.cinematography_settings.custom_resolution_x
	scene.render.resolution_y = scene.cinematography_settings.custom_resolution_y


def update_resolution(self, context):
	"""Update resolution and frame rate when cinema_format or orientation changes."""
	s = context.scene.cinematography_settings
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
	fmt = s.cinema_format
	if fmt in resolutions:
		width, height = resolutions[fmt]
		if s.resolution_orientation == 'VERTICAL' and width > height:
			width, height = height, width
		s.custom_resolution_x = width
		s.custom_resolution_y = height
		new_fps = frame_rates.get(fmt, 24)
		s.frame_rate = float(new_fps)
		context.scene.render.fps = int(new_fps)
	update_linked_resolution(context.scene)


def update_print_resolution(self, context):
	"""Update resolution based on print format and DPI."""
	s = context.scene.cinematography_settings
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
	if s.print_format in print_sizes:
		width_mm, height_mm = print_sizes[s.print_format]
		if s.resolution_orientation == 'VERTICAL' and width_mm > height_mm:
			width_mm, height_mm = height_mm, width_mm
		width_inches = width_mm / 25.4
		height_inches = height_mm / 25.4
		width_pixels = int(width_inches * s.print_dpi)
		height_pixels = int(height_inches * s.print_dpi)
		s.custom_resolution_x = width_pixels
		s.custom_resolution_y = height_pixels
	update_linked_resolution(context.scene)


def update_resolution_x(self, context):
	context.scene.cinematography_settings.last_updated = 'X'
	update_linked_resolution(context.scene)


def update_resolution_y(self, context):
	context.scene.cinematography_settings.last_updated = 'Y'
	update_linked_resolution(context.scene)


def update_frame_rate(self, context):
	context.scene.render.fps = int(context.scene.cinematography_settings.frame_rate)


class CinematographySettings(PropertyGroup):
	"""Grouped cinematography settings to avoid stray Scene properties."""
	# UI toggles and camera settings
	show_cinema_formats: bpy.props.BoolProperty(name="Show Cinema Formats", default=False)
	show_print_formats: bpy.props.BoolProperty(name="Show Print Formats", default=False)
	camera_type: bpy.props.EnumProperty(
		items=[('PERSP', "Perspective", ""), ('ORTHO', "Orthographic", "")],
		name="Camera Type",
		default='PERSP',
		update=lambda self, context: bpy.ops.cinematography.set_camera_type(camera_type=self.camera_type),
	)
	show_camera_manager: bpy.props.BoolProperty(name="Show Camera Manager", default=False)

	# Camera list
	camera_list: bpy.props.CollectionProperty(type=CameraListItem)
	camera_list_index: bpy.props.IntProperty(update=update_camera_list_index)

	# Render and print settings
	cinema_format: bpy.props.EnumProperty(
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
		update=update_resolution,
	)
	resolution_orientation: bpy.props.EnumProperty(
		items=[('HORIZONTAL', "Horizontal", ""), ('VERTICAL', "Vertical", "")],
		name="Resolution Orientation",
		default='HORIZONTAL',
		update=update_resolution,
	)
	frame_rate: bpy.props.FloatProperty(
		name="Frame Rate",
		default=24.0,
		min=1.0,
		max=120.0,
		precision=3,
		step=100,
		update=update_frame_rate,
	)
	print_dpi: bpy.props.IntProperty(
		name="Print DPI",
		description="DPI for print resolutions",
		default=300,
		min=72,
		max=1200,
		update=update_print_resolution,
	)
	print_format: bpy.props.EnumProperty(
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
		update=update_print_resolution,
	)
	resolution_linked: bpy.props.BoolProperty(
		name="Link Resolution",
		description="Link X and Y resolutions",
		default=False,
	)
	aspect_ratio: bpy.props.FloatProperty(
		name="Aspect Ratio",
		description="Aspect ratio of the resolution",
		default=1.0,
	)
	last_updated: bpy.props.StringProperty(
		name="Last Updated",
		description="Which resolution was last updated",
		default='Y',
	)
	custom_resolution_x: bpy.props.IntProperty(
		name="X",
		description="Number of horizontal pixels in the rendered image",
		default=1920,
		min=4,
		max=65536,
		update=update_resolution_x,
	)
	custom_resolution_y: bpy.props.IntProperty(
		name="Y",
		description="Number of vertical pixels in the rendered image",
		default=1080,
		min=4,
		max=65536,
		update=update_resolution_y,
	) 