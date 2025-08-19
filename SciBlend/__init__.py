import bpy
import os

try:
	import bpy.utils.previews
except ImportError:
	print("Warning: bpy.utils.previews not available")
	
from .operators.x3d.operators import ImportX3DOperator

try:
	from .operators.vtk.operators import ImportVTKAnimationOperator
except ImportError as e:
	import sys
	print(f"Error importing VTK operator: {e}", file=sys.stderr)
	class ImportVTKAnimationOperator(bpy.types.Operator):
		bl_idname = "import_vtk.animation"
		bl_label = "Import VTK/VTU/PVTU Animation (VTK not available)"
		def execute(self, context):
			self.report({'ERROR'}, "VTK is not available. Please install VTK package.")
			return {'CANCELLED'}

try:
	from .operators.netcdf.operators import ImportNetCDFOperator
except ImportError as e:
	import sys
	print(f"Error importing NetCDF operator: {e}", file=sys.stderr)
	class ImportNetCDFOperator(bpy.types.Operator):
		bl_idname = "import_netcdf.animation"
		bl_label = "Import NetCDF Animation (netCDF4 not available)"
		def execute(self, context):
			self.report({'ERROR'}, "netCDF4 is not available. Please install required package.")
			return {'CANCELLED'}

try:
	from .operators.shp.operators import ImportShapefileOperator
except ImportError as e:
	import sys
	print(f"Error importing Shapefile operator: {e}", file=sys.stderr)
	class ImportShapefileOperator(bpy.types.Operator):
		bl_idname = "import_shapefile.static"
		bl_label = "Import Shapefile (dependencies not available)"
		def execute(self, context):
			self.report({'ERROR'}, "Shapefile dependencies not available. Please install required packages.")
			return {'CANCELLED'}

from .operators.material_operators import CreateSharedMaterialOperator, ApplySharedMaterialOperator, RemoveAllShadersOperator
from .operators.object_operators import (
	CreateNullOperator, ParentNullToGeoOperator, NullToOriginOperator, CreateSceneOperator,
	BooleanCutterOperator, BooleanCutterHideOperator,
	AddMeshCutterOperator, GroupObjectsOperator, DeleteHierarchyOperator
)
from .operators.shp.delaunay import ShapefileDelaunayOperator
from .operators.gob_operators import (
	GOB_OT_connect_to_paraview, 
	GOB_OT_disconnect_from_paraview, 
	GOB_OT_refresh_from_paraview,
	GOBSettings
)

# Legend Generator guarded integration
LEGEND_AVAILABLE = False
legend_classes = ()
try:
	import matplotlib  # heavy dep check
	import PIL  # pillow
	from .LegendGenerator import (
		update_nodes,
		update_legend_position,
		update_legend_scale,
		update_legend_scale_mode,
		update_legend,
		get_system_fonts,
		classes as LEGEND_CLASSES,
	)
	from .LegendGenerator.properties.color_value import ColorValue
	from .LegendGenerator.ui.png_overlay_panel import PNGOverlayPanel
	# Align panel category with SciBlend
	PNGOverlayPanel.bl_category = 'SciBlend'
	LEGEND_AVAILABLE = True
	legend_classes = LEGEND_CLASSES
except ImportError:
	class PNGOverlayPanelStub(bpy.types.Panel):
		"""Stub panel for Legend Generator shown when required dependencies are missing."""
		bl_label = "Legend Generator"
		bl_idname = "OBJECT_PT_sciblend_legend_generator"
		bl_space_type = 'VIEW_3D'
		bl_region_type = 'UI'
		bl_category = 'SciBlend Advanced Core'

		def draw(self, context):
			layout = self.layout
			box = layout.box()
			box.label(text="Legend Generator unavailable", icon='ERROR')
			box.label(text="Missing dependencies: matplotlib, pillow")

	class PNGOverlayOperatorStub(bpy.types.Operator):
		"""Stub operator for Legend Generator when dependencies are missing."""
		bl_idname = "sciblend.legend_generate"
		bl_label = "Generate Legend"

		def execute(self, context):
			self.report({'ERROR'}, "Legend Generator dependencies missing.")
			return {'CANCELLED'}

	legend_classes = (
		PNGOverlayOperatorStub,
		PNGOverlayPanelStub,
	)

# Shader Generator guarded integration
SHADER_AVAILABLE = False
shader_classes = ()
try:
	from .ShaderGenerator import (
		ColorRampColor,
		COLORRAMP_OT_add_color,
		COLORRAMP_OT_remove_color,
		COLORRAMP_OT_save_custom,
		COLORRAMP_OT_load_custom,
		COLORRAMP_OT_import_json,
		MATERIAL_OT_create_shader,
		MATERIAL_PT_shader_generator,
	)
	# Align Shader Generator panel category to SciBlend
	MATERIAL_PT_shader_generator.bl_category = 'SciBlend'
	SHADER_AVAILABLE = True
	shader_classes = (
		ColorRampColor,
		COLORRAMP_OT_add_color,
		COLORRAMP_OT_remove_color,
		COLORRAMP_OT_save_custom,
		COLORRAMP_OT_load_custom,
		COLORRAMP_OT_import_json,
		MATERIAL_OT_create_shader,
		MATERIAL_PT_shader_generator,
	)
except ImportError:
	class ShaderGeneratorPanelStub(bpy.types.Panel):
		"""Stub panel for Shader Generator shown when required dependencies are missing."""
		bl_label = "Shader Generator"
		bl_idname = "OBJECT_PT_sciblend_shader_generator"
		bl_space_type = 'VIEW_3D'
		bl_region_type = 'UI'
		bl_category = 'SciBlend Advanced Core'

		def draw(self, context):
			layout = self.layout
			box = layout.box()
			box.label(text="Shader Generator unavailable", icon='ERROR')
			box.label(text="Missing dependency: scipy")

	class ShaderGeneratorOperatorStub(bpy.types.Operator):
		"""Stub operator for Shader Generator when dependencies are missing."""
		bl_idname = "sciblend.shader_generate"
		bl_label = "Generate Shader"

		def execute(self, context):
			self.report({'ERROR'}, "Shader Generator dependency missing (scipy).")
			return {'CANCELLED'}

	shader_classes = (
		ShaderGeneratorOperatorStub,
		ShaderGeneratorPanelStub,
	)

# Grid Generator guarded integration
GRID_AVAILABLE = False
grid_classes = ()
try:
	from .GridGenerator import (
		OBJECT_PT_GridGeneratorPanel,
		GenerateNodesOperator,
		CreateEdgesOperator,
		UpdateTextSizeOperator,
		UpdateEdgeSizeOperator,
		ApplyEmissiveMaterialOperator,
		ResizeSceneOperator,
		GridSettings,
	)
	# Align Grid Generator panel category to SciBlend
	OBJECT_PT_GridGeneratorPanel.bl_category = 'SciBlend'
	GRID_AVAILABLE = True
	grid_classes = (
		OBJECT_PT_GridGeneratorPanel,
		GenerateNodesOperator,
		CreateEdgesOperator,
		UpdateTextSizeOperator,
		UpdateEdgeSizeOperator,
		ApplyEmissiveMaterialOperator,
		ResizeSceneOperator,
		GridSettings,
	)
except ImportError:
	class GridGeneratorPanelStub(bpy.types.Panel):
		"""Stub panel for Grid Generator shown when required dependencies are missing."""
		bl_label = "Grid Generator"
		bl_idname = "OBJECT_PT_sciblend_grid_generator"
		bl_space_type = 'VIEW_3D'
		bl_region_type = 'UI'
		bl_category = 'SciBlend Advanced Core'

		def draw(self, context):
			layout = self.layout
			box = layout.box()
			box.label(text="Grid Generator unavailable", icon='ERROR')
			box.label(text="Missing internal modules")

	class GridGeneratorOperatorStub(bpy.types.Operator):
		"""Stub operator for Grid Generator when dependencies are missing."""
		bl_idname = "sciblend.grid_generate"
		bl_label = "Generate Grid"

		def execute(self, context):
			self.report({'ERROR'}, "Grid Generator not available.")
			return {'CANCELLED'}

	grid_classes = (
		GridGeneratorOperatorStub,
		GridGeneratorPanelStub,
	)

# Notes Generator guarded integration
NOTES_AVAILABLE = False
notes_classes = ()
try:
	from .NotesGenerator.panels.main_panel import NOTESGENERATOR_PT_main_panel
	from .NotesGenerator.operators.add_annotation import NOTESGENERATOR_OT_add_annotation
	from .NotesGenerator.properties.annotation_properties import AnnotationProperties
	# Align Notes Generator panel category to SciBlend
	NOTESGENERATOR_PT_main_panel.bl_category = 'SciBlend'
	NOTES_AVAILABLE = True
	notes_classes = (
		NOTESGENERATOR_PT_main_panel,
		NOTESGENERATOR_OT_add_annotation,
		AnnotationProperties,
	)
except ImportError:
	class NotesGeneratorPanelStub(bpy.types.Panel):
		"""Stub panel for Notes Generator shown when required dependencies are missing."""
		bl_label = "Notes Generator"
		bl_idname = "OBJECT_PT_sciblend_notes_generator"
		bl_space_type = 'VIEW_3D'
		bl_region_type = 'UI'
		bl_category = 'SciBlend Advanced Core'

		def draw(self, context):
			layout = self.layout
			box = layout.box()
			box.label(text="Notes Generator unavailable", icon='ERROR')
			box.label(text="Missing internal modules")

	class NotesGeneratorOperatorStub(bpy.types.Operator):
		"""Stub operator for Notes Generator when unavailable."""
		bl_idname = "sciblend.notes_generate"
		bl_label = "Generate Notes"

		def execute(self, context):
			self.report({'ERROR'}, "Notes Generator not available.")
			return {'CANCELLED'}

	notes_classes = (
		NotesGeneratorOperatorStub,
		NotesGeneratorPanelStub,
	)

# Shapes Generator guarded integration
SHAPES_AVAILABLE = False
shapes_classes = ()
try:
	from .ShapesGenerator import (
		ShapesGeneratorItem,
		SHAPESGENERATOR_UL_List,
		SHAPESGENERATOR_PT_Panel,
		SHAPESGENERATOR_OT_UpdateShapes,
		SHAPESGENERATOR_OT_NewShape,
		SHAPESGENERATOR_OT_DeleteShape,
		SHAPESGENERATOR_OT_ImportCustomShape,
	)
	# Align Shapes Generator panel to SciBlend category
	SHAPESGENERATOR_PT_Panel.bl_category = 'SciBlend'
	SHAPES_AVAILABLE = True
	shapes_classes = (
		ShapesGeneratorItem,
		SHAPESGENERATOR_UL_List,
		SHAPESGENERATOR_PT_Panel,
		SHAPESGENERATOR_OT_UpdateShapes,
		SHAPESGENERATOR_OT_NewShape,
		SHAPESGENERATOR_OT_DeleteShape,
		SHAPESGENERATOR_OT_ImportCustomShape,
	)
except ImportError:
	class ShapesGeneratorPanelStub(bpy.types.Panel):
		"""Stub panel for Shapes Generator shown when required dependencies are missing."""
		bl_label = "Shapes Generator"
		bl_idname = "OBJECT_PT_sciblend_shapes_generator"
		bl_space_type = 'VIEW_3D'
		bl_region_type = 'UI'
		bl_category = 'SciBlend Advanced Core'
		def draw(self, context):
			box = self.layout.box()
			box.label(text="Shapes Generator unavailable", icon='ERROR')
			box.label(text="Missing dependencies: numpy, matplotlib, pillow")

	class ShapesGeneratorOperatorStub(bpy.types.Operator):
		"""Stub operator for Shapes Generator when dependencies are missing."""
		bl_idname = "sciblend.shapes_generate"
		bl_label = "Generate Shapes"
		def execute(self, context):
			self.report({'ERROR'}, "Shapes Generator dependencies missing.")
			return {'CANCELLED'}

	shapes_classes = (
		ShapesGeneratorOperatorStub,
		ShapesGeneratorPanelStub,
	)

# Compositor guarded integration
COMPOSITOR_AVAILABLE = False
compositor_classes = ()
try:
	from .Compositor.ui.cinematography_panel import COMPOSITOR_PT_panel
	from .Compositor.cinematography.cinema_formats import (
		CINEMATOGRAPHY_OT_set_cinema_resolution,
		CINEMATOGRAPHY_OT_set_camera_type,
	)
	from .Compositor.cinematography.render_settings import (
		CINEMATOGRAPHY_OT_set_render_resolution,
		CINEMATOGRAPHY_OT_set_print_resolution,
		CINEMATOGRAPHY_OT_toggle_resolution_link,
		update_resolution, update_resolution_x, update_resolution_y,
		update_print_resolution, update_frame_rate,
	)
	from .Compositor.cinematography.camera_manager import (
		CameraListItem, CameraRangeProperties, CAMERA_UL_list,
		CAMERA_OT_add, CAMERA_OT_remove, CAMERA_OT_move, CAMERA_OT_sort,
		CAMERA_OT_update_timeline, CAMERA_OT_erase_all_keyframes, CAMERA_OT_view_selected,
		update_camera_list_index,
	)
	# Align panel to SciBlend category
	COMPOSITOR_PT_panel.bl_category = 'SciBlend'
	COMPOSITOR_AVAILABLE = True
	compositor_classes = (
		COMPOSITOR_PT_panel,
		CINEMATOGRAPHY_OT_set_cinema_resolution, CINEMATOGRAPHY_OT_set_camera_type,
		CINEMATOGRAPHY_OT_set_render_resolution, CINEMATOGRAPHY_OT_set_print_resolution,
		CINEMATOGRAPHY_OT_toggle_resolution_link,
		CameraListItem, CameraRangeProperties, CAMERA_UL_list,
		CAMERA_OT_add, CAMERA_OT_remove, CAMERA_OT_move, CAMERA_OT_sort,
		CAMERA_OT_update_timeline, CAMERA_OT_erase_all_keyframes, CAMERA_OT_view_selected,
	)
except ImportError:
	class CompositorPanelStub(bpy.types.Panel):
		"""Stub panel for Compositor shown when required modules are missing."""
		bl_label = "Compositor"
		bl_idname = "OBJECT_PT_sciblend_compositor"
		bl_space_type = 'VIEW_3D'
		bl_region_type = 'UI'
		bl_category = 'SciBlend Advanced Core'
		def draw(self, context):
			box = self.layout.box()
			box.label(text="Compositor unavailable", icon='ERROR')
			box.label(text="Missing internal modules")

	class CompositorOperatorStub(bpy.types.Operator):
		"""Stub operator for Compositor when unavailable."""
		bl_idname = "sciblend.compositor_stub"
		bl_label = "Compositor"
		def execute(self, context):
			self.report({'ERROR'}, "Compositor not available.")
			return {'CANCELLED'}

	compositor_classes = (CompositorOperatorStub, CompositorPanelStub)

preview_collection = None

class X3DImportSettings(bpy.types.PropertyGroup):
	scale_factor: bpy.props.FloatProperty(
		name="Scale",
		description="Scale factor for imported objects",
		default=1.0,
		min=0.0001,
		max=100.0
	)
	axis_forward: bpy.props.EnumProperty(
		name="Forward",
		items=[
			('X', "X", ""),
			('Y', "Y", ""),
			('Z', "Z", ""),
			('-X', "-X", ""),
			('-Y', "-Y", ""),
			('-Z', "-Z", ""),
		],
		default='Y',
	)
	axis_up: bpy.props.EnumProperty(
		name="Up",
		items=[
			('X', "X", ""),
			('Y', "Y", ""),
			('Z', "Z", ""),
			('-X', "-X", ""),
			('-Y', "-Y", ""),
			('-Z', "-Z", ""),
		],
		default='Z',
	)
	overwrite_scene: bpy.props.BoolProperty(
		name="Overwrite Scene",
		description="Delete all objects in the scene before importing new meshes",
		default=True
	)
	shared_material: bpy.props.PointerProperty(
		type=bpy.types.Material,
		name="Shared Material"
	)

class SciBlendPanel(bpy.types.Panel):
	bl_label = "Advanced Core"
	bl_idname = "OBJECT_PT_sciblend"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'SciBlend'

	def draw(self, context):
		layout = self.layout
		settings = context.scene.x3d_import_settings

		box = layout.box()
		box.label(text="Import", icon='IMPORT')
		row = box.row(align=True)
		row.operator("import_x3d.animation", text="X3D", icon='SEQUENCE')
		row.operator("import_vtk.animation", text="VTK/VTU/PVTU", icon='SEQUENCE')
		row.operator("import_netcdf.animation", text="NetCDF", icon='SEQUENCE')
		row.operator("import_shapefile.static", text="Shapefile", icon='MESH_DATA')
		row = box.row(align=True)
		row.prop(settings, "overwrite_scene")

		box = layout.box()
		box.label(text="Settings", icon='SETTINGS')
		row = box.row(align=True)
		row.prop(settings, "scale_factor")
		row.prop(settings, "axis_forward")
		row.prop(settings, "axis_up")

		box = layout.box()
		box.label(text="Material", icon='MATERIAL')
		row = box.row(align=True)
		row.prop(settings, "shared_material", text="")
		row.operator("import_x3d.create_shared_material", text="New", icon='ADD')
		row.operator("import_x3d.apply_shared_material", text="Apply", icon='CHECKMARK')
		row.operator("import_x3d.remove_all_shaders", text="Clear", icon='X')

		box = layout.box()
		box.label(text="Objects", icon='OBJECT_DATAMODE')
		row = box.row(align=True)
		row.operator("import_x3d.create_null", text="Create Null", icon='EMPTY_AXIS')
		row.operator("import_x3d.parent_null_to_geo", text="Parent to Geo", icon='OBJECT_DATAMODE')
		row.operator("import_x3d.null_to_origin", text="Center Null", icon='EMPTY_AXIS')
		row.operator("object.group_objects", text="Group", icon='GROUP')

		row = box.row(align=True)
		row.operator("object.create_scene", text="Scene Preset", icon='SCENE_DATA')

		box = layout.box()
		box.label(text="Boolean", icon='MOD_BOOLEAN')
		row = box.row(align=True)
		row.prop(context.scene, "new_cutter_mesh", text="")
		row.operator("object.add_mesh_cutter_operator", text="Add Cutter", icon='ADD')
		row = box.row(align=True)
		row.operator("object.boolean_cutter_operator", text="Apply", icon='MOD_BOOLEAN')
		row.operator("object.boolean_cutter_hide_operator", text="Hide", icon='HIDE_ON')

		box = layout.box()
		box.label(text="Organize", icon='OUTLINER')
		row = box.row(align=True)
		row.prop(context.scene, "group_type", text="")
		row.operator("object.group_objects", text="Group", icon='GROUP')
		row.operator("object.delete_hierarchy", text="Delete Hierarchy", icon='X')

		box = layout.box()
		box.label(text="GoB - Paraview Bridge", icon='LINKED')
		row = box.row(align=True)
		gob = context.scene.gob_settings
		row.prop(gob, "host", text="Host")
		row.prop(gob, "port", text="Port")
		row = box.row(align=True)
		if not gob.is_connected:
			row.operator("gob.connect_to_paraview", text="Connect", icon='LINKED')
		else:
			row.operator("gob.refresh_from_paraview", text="Refresh", icon='FILE_REFRESH')
			row.operator("gob.disconnect_from_paraview", text="Disconnect", icon='UNLINKED')

classes = (
	ImportX3DOperator,
	ImportVTKAnimationOperator,
	ImportNetCDFOperator,
	ImportShapefileOperator,
	CreateSharedMaterialOperator,
	ApplySharedMaterialOperator,
	RemoveAllShadersOperator,
	CreateNullOperator,
	ParentNullToGeoOperator,
	NullToOriginOperator,
	CreateSceneOperator,
	BooleanCutterOperator,
	BooleanCutterHideOperator,
	AddMeshCutterOperator,
	GroupObjectsOperator,
	DeleteHierarchyOperator,
	ShapefileDelaunayOperator,
	GOBSettings,
	GOB_OT_connect_to_paraview,
	GOB_OT_disconnect_from_paraview,
	GOB_OT_refresh_from_paraview,
	X3DImportSettings,
	SciBlendPanel,
) + legend_classes + shader_classes + grid_classes + notes_classes + shapes_classes + compositor_classes

def register():
	global preview_collection
	preview_collection = bpy.utils.previews.new()

	for cls in classes:
		bpy.utils.register_class(cls)

	bpy.types.Scene.x3d_import_settings = bpy.props.PointerProperty(type=X3DImportSettings)
	bpy.types.Scene.boolean_cutter_object = bpy.props.PointerProperty(type=bpy.types.Object)
	bpy.types.Scene.new_cutter_mesh = bpy.props.PointerProperty(type=bpy.types.Object)
	bpy.types.Scene.group_type = bpy.props.EnumProperty(
		name="Group Type",
		items=[
			("EMPTY", "Empty", "Group under an Empty"),
			("COLLECTION", "Collection", "Group in a Collection")
		],
		default="EMPTY"
	)
	bpy.types.Scene.gob_settings = bpy.props.PointerProperty(type=GOBSettings)

	# Legend Generator properties (only when available)
	if LEGEND_AVAILABLE:
		from .LegendGenerator.utils.color_utils import get_colormap_items, update_colormap
		bpy.types.Scene.colors_values = bpy.props.CollectionProperty(type=ColorValue)
		bpy.types.Scene.color_values_index = bpy.props.IntProperty()
		bpy.types.Scene.num_nodes = bpy.props.IntProperty(
			name="Number of Nodes",
			default=2,
			min=2,
			update=update_nodes
		)
		bpy.types.Scene.legend_name = bpy.props.StringProperty(
			name="Legend Name",
			description="Name of the legend that will appear on the colorbar",
			default="Legend",
			update=update_legend
		)
		bpy.types.Scene.interpolation = bpy.props.EnumProperty(
			name="Interpolation",
			items=[
				('LINEAR', "Linear", "Linear interpolation"),
				('STEP', "Step", "Step interpolation"),
				('CUBIC', "Cubic", "Cubic interpolation"),
				('NEAREST', "Nearest", "Nearest neighbor interpolation")
			],
			default='LINEAR'
		)
		bpy.types.Scene.legend_orientation = bpy.props.EnumProperty(
			name="Orientation",
			items=[
				('HORIZONTAL', "Horizontal", "Horizontal orientation"),
				('VERTICAL', "Vertical", "Vertical orientation")
			],
			default='HORIZONTAL'
		)
		bpy.types.Scene.legend_position_x = bpy.props.FloatProperty(
			name="X Position",
			default=0.0,
			update=update_legend_position
		)
		bpy.types.Scene.legend_position_y = bpy.props.FloatProperty(
			name="Y Position",
			default=0.0,
			update=update_legend_position
		)
		bpy.types.Scene.legend_scale_uniform = bpy.props.BoolProperty(
			name="Uniform Scale",
			default=True,
			update=update_legend_scale
		)
		bpy.types.Scene.legend_scale_x = bpy.props.FloatProperty(
			name="X Scale",
			description="Scale of the legend in X direction",
			default=1.0,
			min=0.1,
			max=10.0,
			update=update_legend_scale
		)
		bpy.types.Scene.legend_scale_y = bpy.props.FloatProperty(
			name="Y Scale",
			description="Scale of the legend in Y direction",
			default=1.0,
			min=0.1,
			max=10.0,
			update=update_legend_scale
		)
		bpy.types.Scene.legend_scale_linked = bpy.props.BoolProperty(
			name="Link Scale",
			description="Link X and Y scale values",
			default=True,
			update=update_legend_scale
		)
		bpy.types.Scene.legend_scale_mode = bpy.props.EnumProperty(
			name="Scale Mode",
			items=[
				('SCENE_SIZE', "Scene Size", "Scale relative to scene size"),
				('RENDER_SIZE_FIT', "Render Size (Fit)", "Scale relative to render size, fit to render"),
				('RENDER_SIZE_CROP', "Render Size (Crop)", "Scale relative to render size, crop to render")
			],
			default='SCENE_SIZE',
			update=update_legend_scale_mode
		)
		bpy.types.Scene.colormap = bpy.props.EnumProperty(
			name="Colormap",
			description="Select a scientific colormap or use custom colors",
			items=get_colormap_items(),
			default='CUSTOM',
			update=update_colormap
		)
		bpy.types.Scene.colormap_start = bpy.props.FloatProperty(
			name="Start Value",
			description="Start value of the colormap range",
			default=0.0,
			update=update_colormap
		)
		bpy.types.Scene.colormap_end = bpy.props.FloatProperty(
			name="End Value",
			description="End value of the colormap range",
			default=1.0,
			update=update_colormap
		)
		bpy.types.Scene.colormap_subdivisions = bpy.props.IntProperty(
			name="Subdivisions",
			description="Number of subdivisions in the colormap",
			default=10,
			min=2,
			max=100,
			update=update_colormap
		)
		bpy.types.Scene.legend_width = bpy.props.IntProperty(
			name="Width",
			description="Width of the legend in pixels",
			default=200,
			min=1
		)
		bpy.types.Scene.legend_height = bpy.props.IntProperty(
			name="Height",
			description="Height of the legend in pixels",
			default=600,
			min=1
		)
		bpy.types.Scene.legend_font_type = bpy.props.EnumProperty(
			name="Font Type",
			description="Choose between system font or custom font",
			items=[
				('SYSTEM', "System Font", "Use a system font"),
				('CUSTOM', "Custom Font", "Use a custom font file")
			],
			default='SYSTEM',
			update=update_legend
		)
		bpy.types.Scene.legend_system_font = bpy.props.EnumProperty(
			name="System Font",
			description="Choose a system font",
			items=get_system_fonts,
			update=update_legend
		)
		bpy.types.Scene.legend_font = bpy.props.StringProperty(
			name="Custom Font File",
			description="Path to custom font file",
			subtype='FILE_PATH',
			update=update_legend
		)
		bpy.types.Scene.legend_text_color = bpy.props.FloatVectorProperty(
			name="Legend Text Color",
			subtype='COLOR',
			default=(1.0, 1.0, 1.0),
			min=0.0,
			max=1.0,
			description="Color of the legend text",
			update=update_legend
		)

	# Shader Generator properties (only when available)
	if SHADER_AVAILABLE:
		bpy.types.Scene.custom_colorramp = bpy.props.CollectionProperty(type=ColorRampColor)

	# Grid Generator properties (only when available)
	if GRID_AVAILABLE:
		bpy.types.Scene.grid_settings = bpy.props.PointerProperty(type=GridSettings)

	# Notes Generator properties (only when available)
	if NOTES_AVAILABLE:
		bpy.types.Scene.annotation_properties = bpy.props.PointerProperty(type=AnnotationProperties)

	# Shapes Generator properties (only when available)
	if SHAPES_AVAILABLE:
		bpy.types.Scene.shapesgenerator_shapes = bpy.props.CollectionProperty(type=ShapesGeneratorItem)
		bpy.types.Scene.shapesgenerator_active_shape_index = bpy.props.IntProperty()

	# Compositor properties (only when available)
	if COMPOSITOR_AVAILABLE:
		# Panel-level toggles and camera type
		bpy.types.Scene.show_cinema_formats = bpy.props.BoolProperty(name="Show Cinema Formats", default=False)
		bpy.types.Scene.show_print_formats = bpy.props.BoolProperty(name="Show Print Formats", default=False)
		if not hasattr(bpy.types.Scene, "camera_type"):
			bpy.types.Scene.camera_type = bpy.props.EnumProperty(
				items=[('PERSP', "Perspective", ""), ('ORTHO', "Orthographic", "")],
				name="Camera Type",
				default='PERSP',
				update=lambda self, context: bpy.ops.cinematography.set_camera_type(camera_type=self.camera_type)
			)
		bpy.types.Scene.show_camera_manager = bpy.props.BoolProperty(name="Show Camera Manager", default=False)

		# Render settings
		bpy.types.Scene.cinema_format = bpy.props.EnumProperty(
			items=[('2K_DCI', "2K DCI", ""), ('4K_DCI', "4K DCI", ""), ('8K_DCI', "8K DCI", ""),
			       ('HD', "HD", ""), ('FULL_HD', "Full HD", ""), ('2K', "2K", ""),
			       ('4K_UHD', "4K UHD", ""), ('8K_UHD', "8K UHD", ""),
			       ('ACADEMY_2_39_1', "Academy 2.39:1", ""), ('CINEMASCOPE', "Cinemascope", ""), ('IMAX', "IMAX", "")],
			name="Cinema Format", default='FULL_HD', update=update_resolution
		)
		bpy.types.Scene.resolution_orientation = bpy.props.EnumProperty(
			items=[('HORIZONTAL', "Horizontal", ""), ('VERTICAL', "Vertical", "")],
			name="Resolution Orientation", default='HORIZONTAL', update=update_resolution
		)
		bpy.types.Scene.frame_rate = bpy.props.FloatProperty(name="Frame Rate", default=24.0, min=1.0, max=120.0, precision=3, step=100, update=update_frame_rate)
		bpy.types.Scene.print_dpi = bpy.props.IntProperty(name="Print DPI", default=300, min=72, max=1200, update=update_print_resolution)
		bpy.types.Scene.print_format = bpy.props.EnumProperty(
			items=[('A4', "A4", ""), ('A3', "A3", ""), ('A2', "A2", ""), ('A1', "A1", ""), ('A0', "A0", ""),
			       ('LETTER', "Letter", ""), ('LEGAL', "Legal", ""), ('TABLOID', "Tabloid", "")],
			name="Print Format", default='A4', update=update_print_resolution
		)
		bpy.types.Scene.resolution_linked = bpy.props.BoolProperty(name="Link Resolution", default=False)
		bpy.types.Scene.aspect_ratio = bpy.props.FloatProperty(name="Aspect Ratio", default=1.0)
		bpy.types.Scene.last_updated = bpy.props.StringProperty(name="Last Updated", default='Y')
		bpy.types.Scene.custom_resolution_x = bpy.props.IntProperty(name="X", default=1920, min=4, max=65536, update=update_resolution_x)
		bpy.types.Scene.custom_resolution_y = bpy.props.IntProperty(name="Y", default=1080, min=4, max=65536, update=update_resolution_y)

		# Camera manager
		bpy.types.Object.camera_range = bpy.props.PointerProperty(type=CameraRangeProperties)
		bpy.types.Scene.camera_list = bpy.props.CollectionProperty(type=CameraListItem)
		bpy.types.Scene.camera_list_index = bpy.props.IntProperty(update=update_camera_list_index)

def unregister():
	global preview_collection
	if preview_collection:
		bpy.utils.previews.remove(preview_collection)

	for cls in classes:
		bpy.utils.unregister_class(cls)
	del bpy.types.Scene.x3d_import_settings
	del bpy.types.Scene.boolean_cutter_object
	del bpy.types.Scene.new_cutter_mesh
	del bpy.types.Scene.group_type
	del bpy.types.Scene.gob_settings

	if LEGEND_AVAILABLE:
		del bpy.types.Scene.colors_values
		del bpy.types.Scene.color_values_index
		del bpy.types.Scene.num_nodes
		del bpy.types.Scene.legend_name
		del bpy.types.Scene.interpolation
		del bpy.types.Scene.legend_orientation
		del bpy.types.Scene.legend_position_x
		del bpy.types.Scene.legend_position_y
		del bpy.types.Scene.legend_scale_uniform
		del bpy.types.Scene.legend_scale_x
		del bpy.types.Scene.legend_scale_y
		del bpy.types.Scene.legend_scale_linked
		del bpy.types.Scene.colormap
		del bpy.types.Scene.colormap_start
		del bpy.types.Scene.colormap_end
		del bpy.types.Scene.colormap_subdivisions
		del bpy.types.Scene.legend_width
		del bpy.types.Scene.legend_height
		del bpy.types.Scene.legend_scale_mode
		del bpy.types.Scene.legend_font_type
		del bpy.types.Scene.legend_system_font
		del bpy.types.Scene.legend_font
		del bpy.types.Scene.legend_text_color

	if SHADER_AVAILABLE:
		del bpy.types.Scene.custom_colorramp

	if GRID_AVAILABLE:
		del bpy.types.Scene.grid_settings

	if NOTES_AVAILABLE:
		del bpy.types.Scene.annotation_properties

	if SHAPES_AVAILABLE:
		del bpy.types.Scene.shapesgenerator_shapes
		del bpy.types.Scene.shapesgenerator_active_shape_index

	if COMPOSITOR_AVAILABLE:
		if hasattr(bpy.types.Scene, "camera_type"):
			del bpy.types.Scene.camera_type
		if hasattr(bpy.types.Scene, "show_camera_manager"):
			del bpy.types.Scene.show_camera_manager
		if hasattr(bpy.types.Scene, "show_cinema_formats"):
			del bpy.types.Scene.show_cinema_formats
		if hasattr(bpy.types.Scene, "show_print_formats"):
			del bpy.types.Scene.show_print_formats

		del bpy.types.Scene.cinema_format
		del bpy.types.Scene.resolution_orientation
		del bpy.types.Scene.frame_rate
		del bpy.types.Scene.print_dpi
		del bpy.types.Scene.print_format
		del bpy.types.Scene.resolution_linked
		del bpy.types.Scene.aspect_ratio
		del bpy.types.Scene.last_updated
		del bpy.types.Scene.custom_resolution_x
		del bpy.types.Scene.custom_resolution_y

		del bpy.types.Object.camera_range
		del bpy.types.Scene.camera_list
		del bpy.types.Scene.camera_list_index

if __name__ == "__main__":
	register()

bl_info = {
	"name": "SciBlend",
	"author": "José Marín",
	"version": (1, 0),
	"blender": (4, 5, 1),
	"location": "View3D > Sidebar > SciBlend",
	"description": "Scientific visualization tools for Blender",
	"warning": "",
	"doc_url": "",
	"category": "3D View",
}
