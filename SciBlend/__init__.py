import bpy
import os

try:
    import bpy.utils.previews
except ImportError:
    print("Warning: bpy.utils.previews not available")
    
from .operators.x3d.operators import ImportX3DOperator
from ..ui.pref import SciBlendPreferences

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



LEGEND_AVAILABLE = False
legend_classes = ()
LEGEND_DEPS_HANDLER = None
try:
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
    from .LegendGenerator.properties.legend_settings import LegendSettings
    PNGOverlayPanel.bl_category = 'SciBlend'
    PNGOverlayPanel.bl_options = {'DEFAULT_CLOSED'}
    try:
        from .LegendGenerator import _depsgraph_handler as _LEGEND_DEPS
        LEGEND_DEPS_HANDLER = _LEGEND_DEPS
    except Exception:
        LEGEND_DEPS_HANDLER = None
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
        bl_options = {'DEFAULT_CLOSED'}

        def draw(self, context):
            layout = self.layout
            box = self.layout.box()
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
    from .ShaderGenerator.properties.settings import ShaderGeneratorSettings
    MATERIAL_PT_shader_generator.bl_category = 'SciBlend'
    MATERIAL_PT_shader_generator.bl_options = {'DEFAULT_CLOSED'}
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
        ShaderGeneratorSettings,
    )
except ImportError:
    class ShaderGeneratorPanelStub(bpy.types.Panel):
        """Stub panel for Shader Generator shown when required dependencies are missing."""
        bl_label = "Shader Generator"
        bl_idname = "OBJECT_PT_sciblend_shader_generator"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = 'SciBlend Advanced Core'
        bl_options = {'DEFAULT_CLOSED'}

        def draw(self, context):
            box = self.layout.box()
            box.label(text="Shader Generator unavailable", icon='ERROR')
            box.label(text="Missing internal modules")

    shader_classes = (ShaderGeneratorPanelStub,)

SCIBLENDNODES_AVAILABLE = False
sciblendnodes_classes = ()
try:
    from .SciBlendNodes import register as SCIBLENDNODES_register, unregister as SCIBLENDNODES_unregister
    from .SciBlendNodes.ui.panel import SCIBLENDNODES_PT_panel
    SCIBLENDNODES_PT_panel.bl_category = 'SciBlend'
    SCIBLENDNODES_PT_panel.bl_options = {'DEFAULT_CLOSED'}
    SCIBLENDNODES_AVAILABLE = True
except ImportError:
    SCIBLENDNODES_available = False

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



LEGEND_AVAILABLE = False
legend_classes = ()
LEGEND_DEPS_HANDLER = None
try:
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
    from .LegendGenerator.properties.legend_settings import LegendSettings
    PNGOverlayPanel.bl_category = 'SciBlend'
    PNGOverlayPanel.bl_options = {'DEFAULT_CLOSED'}
    try:
        from .LegendGenerator import _depsgraph_handler as _LEGEND_DEPS
        LEGEND_DEPS_HANDLER = _LEGEND_DEPS
    except Exception:
        LEGEND_DEPS_HANDLER = None
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
        bl_options = {'DEFAULT_CLOSED'}

        def draw(self, context):
            layout = self.layout
            box = self.layout.box()
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
    from .ShaderGenerator.properties.settings import ShaderGeneratorSettings
    MATERIAL_PT_shader_generator.bl_category = 'SciBlend'
    MATERIAL_PT_shader_generator.bl_options = {'DEFAULT_CLOSED'}
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
        ShaderGeneratorSettings,
    )
except ImportError:
    class ShaderGeneratorPanelStub(bpy.types.Panel):
        """Stub panel for Shader Generator shown when required dependencies are missing."""
        bl_label = "Shader Generator"
        bl_idname = "OBJECT_PT_sciblend_shader_generator"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = 'SciBlend Advanced Core'
        bl_options = {'DEFAULT_CLOSED'}

        def draw(self, context):
            box = self.layout.box()
            box.label(text="Shader Generator unavailable", icon='ERROR')
            box.label(text="Missing internal modules")

    shader_classes = (ShaderGeneratorPanelStub,)

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

    OBJECT_PT_GridGeneratorPanel.bl_category = 'SciBlend'
    OBJECT_PT_GridGeneratorPanel.bl_options = {'DEFAULT_CLOSED'}
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
        bl_options = {'DEFAULT_CLOSED'}

        def draw(self, context):
            layout = self.layout
            box = self.layout.box()
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

NOTES_AVAILABLE = False
notes_classes = ()
try:
    from .NotesGenerator.panels.main_panel import NOTESGENERATOR_PT_main_panel
    from .NotesGenerator.operators.add_annotation import NOTESGENERATOR_OT_add_annotation
    from .NotesGenerator.properties.annotation_properties import AnnotationProperties
    # Align Notes Generator panel category to SciBlend
    NOTESGENERATOR_PT_main_panel.bl_category = 'SciBlend'
    NOTESGENERATOR_PT_main_panel.bl_options = {'DEFAULT_CLOSED'}
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
            box = self.layout.box()
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
        SHAPESGENERATOR_OT_AnimatedGraphs,
    )
    # Align Shapes Generator panel to SciBlend category
    SHAPESGENERATOR_PT_Panel.bl_category = 'SciBlend'
    SHAPESGENERATOR_PT_Panel.bl_options = {'DEFAULT_CLOSED'}
    SHAPES_AVAILABLE = True
    shapes_classes = (
        ShapesGeneratorItem,
        SHAPESGENERATOR_UL_List,
        SHAPESGENERATOR_PT_Panel,
        SHAPESGENERATOR_OT_UpdateShapes,
        SHAPESGENERATOR_OT_NewShape,
        SHAPESGENERATOR_OT_DeleteShape,
        SHAPESGENERATOR_OT_ImportCustomShape,
        SHAPESGENERATOR_OT_AnimatedGraphs,
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
            box.label(text="Missing dependencies: matplotlib, pillow")

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
    from .Compositor.cinematography.render_settings_group import CinematographySettings

    COMPOSITOR_PT_panel.bl_category = 'SciBlend'
    COMPOSITOR_PT_panel.bl_options = {'DEFAULT_CLOSED'}
    COMPOSITOR_AVAILABLE = True
    compositor_classes = (
        COMPOSITOR_PT_panel,
        CINEMATOGRAPHY_OT_set_cinema_resolution, CINEMATOGRAPHY_OT_set_camera_type,
        CINEMATOGRAPHY_OT_set_render_resolution, CINEMATOGRAPHY_OT_set_print_resolution,
        CINEMATOGRAPHY_OT_toggle_resolution_link,
        CameraListItem, CameraRangeProperties, CAMERA_UL_list,
        CAMERA_OT_add, CAMERA_OT_remove, CAMERA_OT_move, CAMERA_OT_sort,
        CAMERA_OT_update_timeline, CAMERA_OT_erase_all_keyframes, CAMERA_OT_view_selected,
        CinematographySettings,
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

FILTERS_AVAILABLE = False
filters_classes = ()
try:
    from .FiltersGenerator.properties.emitter_settings import FiltersEmitterSettings
    from .FiltersGenerator.properties.volume_item import VolumeItem
    from .FiltersGenerator.properties.volume_settings import VolumeRenderingSettings
    from .FiltersGenerator.properties.threshold_settings import FiltersThresholdSettings
    from .FiltersGenerator.properties.contour_settings import FiltersContourSettings
    from .FiltersGenerator.properties.clip_settings import FiltersClipSettings
    from .FiltersGenerator.properties.slice_settings import FiltersSliceSettings
    from .FiltersGenerator.properties.calculator_settings import FiltersCalculatorSettings
    from .FiltersGenerator.operators.create_emitter import FILTERS_OT_create_emitter
    from .FiltersGenerator.operators.place_emitter import FILTERS_OT_place_emitter
    from .FiltersGenerator.operators.generate_streamline import FILTERS_OT_generate_streamline
    from .FiltersGenerator.operators.volume_import import FILTERS_OT_volume_import_vdb_sequence
    from .FiltersGenerator.operators.volume_update import FILTERS_OT_volume_update_material, FILTERS_OT_volume_compute_range
    from .FiltersGenerator.operators.volume_list_operators import (
        FILTERS_OT_volume_item_add,
        FILTERS_OT_volume_item_remove,
        FILTERS_OT_volume_item_move_up,
        FILTERS_OT_volume_item_move_down,
    )
    from .FiltersGenerator.operators.threshold_live import FILTERS_OT_build_threshold_surface
    from .FiltersGenerator.operators.contour_live import FILTERS_OT_build_contour_surface
    from .FiltersGenerator.operators.clip_live import FILTERS_OT_clip_ensure_plane, FILTERS_OT_build_clip_surface
    from .FiltersGenerator.operators.slice_live import FILTERS_OT_slice_ensure_plane, FILTERS_OT_build_slice_surface
    from .FiltersGenerator.operators.calculator import FILTERS_OT_calculator_apply, FILTERS_OT_calculator_append_var, FILTERS_OT_calculator_append_attr, FILTERS_OT_calculator_append_func
    from .FiltersGenerator.ui.volume_list import FILTERS_UL_volume_list
    from .FiltersGenerator.ui.main_panel import FILTERSGENERATOR_PT_main_panel
    from .FiltersGenerator.ui.main_panel import FILTERSGENERATOR_PT_stream_tracers
    from .FiltersGenerator.ui.main_panel import FILTERSGENERATOR_PT_volume_filter
    from .FiltersGenerator.ui.main_panel import FILTERSGENERATOR_PT_geometry_filters
    
    VolumeRenderingSettings.__annotations__['volume_items'] = bpy.props.CollectionProperty(type=VolumeItem)
    
    FILTERS_AVAILABLE = True
    filters_classes = (
        FiltersEmitterSettings,
        VolumeItem,
        VolumeRenderingSettings,
        FiltersThresholdSettings,
        FiltersContourSettings,
        FiltersClipSettings,
        FiltersSliceSettings,
        FiltersCalculatorSettings,
        FILTERS_OT_create_emitter,
        FILTERS_OT_place_emitter,
        FILTERS_OT_generate_streamline,
        FILTERS_OT_volume_import_vdb_sequence,
        FILTERS_OT_volume_update_material,
        FILTERS_OT_volume_compute_range,
        FILTERS_OT_volume_item_add,
        FILTERS_OT_volume_item_remove,
        FILTERS_OT_volume_item_move_up,
        FILTERS_OT_volume_item_move_down,
        FILTERS_OT_build_threshold_surface,
        FILTERS_OT_build_contour_surface,
        FILTERS_OT_clip_ensure_plane,
        FILTERS_OT_build_clip_surface,
        FILTERS_OT_slice_ensure_plane,
        FILTERS_OT_build_slice_surface,
        FILTERS_OT_calculator_apply,
        FILTERS_OT_calculator_append_var,
        FILTERS_OT_calculator_append_attr,
        FILTERS_OT_calculator_append_func,
        FILTERS_UL_volume_list,
        FILTERSGENERATOR_PT_main_panel,
        FILTERSGENERATOR_PT_stream_tracers,
        FILTERSGENERATOR_PT_volume_filter,
        FILTERSGENERATOR_PT_geometry_filters,
    )
except ImportError:
    class FiltersGeneratorPanelStub(bpy.types.Panel):
        """Stub panel for Filters Generator shown when required modules are missing."""
        bl_label = "Filters Generator"
        bl_idname = "OBJECT_PT_sciblend_filters_generator"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = 'SciBlend Advanced Core'
        def draw(self, context):
            box = self.layout.box()
            box.label(text="Filters Generator unavailable", icon='ERROR')
            box.label(text="Missing internal modules")

    filters_classes = (FiltersGeneratorPanelStub,)

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
        default='-Z',
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
        default='Y',
    )
    overwrite_scene: bpy.props.BoolProperty(
        name="Overwrite Scene",
        description="Delete all objects in the scene before importing new meshes",
        default=True
    )
    import_to_new_collection: bpy.props.BoolProperty(
        name="Import to New Collection",
        description="Import created objects into a newly created collection",
        default=False
    )
    shared_material: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Shared Material"
    )
    loop_count: bpy.props.IntProperty(
        name="Loop",
        description="Number of times to repeat the imported sequence",
        default=1,
        min=1,
        soft_max=200,
    )

class VolumeMeshInfo(bpy.types.PropertyGroup):
    """Metadata for objects created from a managed volumetric mesh."""
    is_volume_mesh: bpy.props.BoolProperty(default=False)

class SCIBLEND_OT_clear_on_demand_cache(bpy.types.Operator):
    bl_idname = "sciblend.clear_on_demand_cache"
    bl_label = "Clear On-demand Volume Cache"
    bl_options = {'REGISTER'}

    def execute(self, context):
        try:
            from .FiltersGenerator.utils.on_demand_loader import clear_on_demand_cache
            clear_on_demand_cache()
            self.report({'INFO'}, "On-demand cache cleared")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to clear cache: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}

class SciBlendPanel(bpy.types.Panel):
    bl_label = "Advanced Core"
    bl_idname = "OBJECT_PT_sciblend"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SciBlend'
    bl_options = {'DEFAULT_CLOSED'}

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
        row.prop(settings, "import_to_new_collection")

        box = layout.box()
        box.label(text="Settings", icon='SETTINGS')
        row = box.row(align=True)
        row.prop(settings, "scale_factor")
        row.prop(settings, "axis_forward")
        row.prop(settings, "axis_up")
        row = box.row(align=True)
        row.prop(settings, "loop_count")

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

        box = layout.box()
        box.label(text="On-demand Volume Topology", icon='OUTLINER_DATA_VOLUME')
        col = box.column(align=True)
        col.prop(context.scene, "on_demand_volume_enabled", text="Enabled")
        col.prop(context.scene, "on_demand_data_root", text="Data Root")
        col.prop(context.scene, "on_demand_max_cached", text="Max Cached Models")
        col.operator("sciblend.clear_on_demand_cache", text="Clear Cache", icon='TRASH')

classes_pre = (
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
    VolumeMeshInfo,
    SciBlendPanel,
    SciBlendPreferences,
    SCIBLEND_OT_clear_on_demand_cache
) + shader_classes + legend_classes + shapes_classes + grid_classes + notes_classes + filters_classes

classes_post = compositor_classes

classes = classes_pre + classes_post


def register():
    global preview_collection
    preview_collection = bpy.utils.previews.new()

    for cls in classes_pre:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            try:
                bpy.utils.unregister_class(cls)
            except Exception:
                pass
            bpy.utils.register_class(cls)

    if SCIBLENDNODES_AVAILABLE:
        try:
            SCIBLENDNODES_register()
        except Exception as e:
            print(f"SciBlend Nodes registration failed: {e}")

    for cls in classes_post:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            try:
                bpy.utils.unregister_class(cls)
            except Exception:
                pass
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
    bpy.types.Object.volume_mesh_info = bpy.props.PointerProperty(type=VolumeMeshInfo)
    bpy.types.Scene.on_demand_volume_enabled = bpy.props.BoolProperty(name="On-demand Volume Topology", default=False)
    bpy.types.Scene.on_demand_data_root = bpy.props.StringProperty(name="Data Root", default="", subtype='DIR_PATH')
    bpy.types.Scene.on_demand_max_cached = bpy.props.IntProperty(name="Max Cached Models", default=4, min=0, soft_max=32)

    if LEGEND_AVAILABLE:
        bpy.types.Scene.legend_settings = bpy.props.PointerProperty(type=LegendSettings)
        if LEGEND_DEPS_HANDLER and LEGEND_DEPS_HANDLER not in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(LEGEND_DEPS_HANDLER)
            print("SciBlend: Legend depsgraph handler registered")

    if SHADER_AVAILABLE:
        bpy.types.Scene.custom_colorramp = bpy.props.CollectionProperty(type=ColorRampColor)
        bpy.types.Scene.shader_generator_settings = bpy.props.PointerProperty(type=ShaderGeneratorSettings)

    if GRID_AVAILABLE:
        bpy.types.Scene.grid_settings = bpy.props.PointerProperty(type=GridSettings)

    if NOTES_AVAILABLE:
        bpy.types.Scene.annotation_properties = bpy.props.PointerProperty(type=AnnotationProperties)

    if SHAPES_AVAILABLE:
        bpy.types.Scene.shapesgenerator_shapes = bpy.props.CollectionProperty(type=ShapesGeneratorItem)
        bpy.types.Scene.shapesgenerator_active_shape_index = bpy.props.IntProperty()
        if not hasattr(bpy.types.Scene, 'shapesgenerator_animated_graphs'):
            bpy.types.Scene.shapesgenerator_animated_graphs = bpy.props.BoolProperty(
                name="Generate Animated Graphs",
                description="When enabled, Update Shapes configures graphs as Image Sequence and uses the generated sequence folder",
                default=False,
            )
        if not hasattr(bpy.types.Scene, 'shapesgenerator_animated_graphs_dir'):
            bpy.types.Scene.shapesgenerator_animated_graphs_dir = bpy.props.StringProperty(
                name="Animated Graphs Directory",
                description="Last generated graphs directory for image sequence",
                default="",
                subtype='DIR_PATH',
            )

    if COMPOSITOR_AVAILABLE:
        bpy.types.Scene.cinematography_settings = bpy.props.PointerProperty(type=CinematographySettings)
        bpy.types.Object.camera_range = bpy.props.PointerProperty(type=CameraRangeProperties)

    if FILTERS_AVAILABLE:
        from .FiltersGenerator.properties.emitter_settings import FiltersEmitterSettings
        from .FiltersGenerator.properties.volume_settings import VolumeRenderingSettings
        from .FiltersGenerator.properties.threshold_settings import FiltersThresholdSettings
        from .FiltersGenerator.properties.contour_settings import FiltersContourSettings
        from .FiltersGenerator.properties.clip_settings import FiltersClipSettings
        from .FiltersGenerator.properties.slice_settings import FiltersSliceSettings
        from .FiltersGenerator.properties.calculator_settings import FiltersCalculatorSettings
        bpy.types.Scene.filters_emitter_settings = bpy.props.PointerProperty(type=FiltersEmitterSettings)
        bpy.types.Scene.filters_volume_settings = bpy.props.PointerProperty(type=VolumeRenderingSettings)
        bpy.types.Scene.filters_threshold_settings = bpy.props.PointerProperty(type=FiltersThresholdSettings)
        bpy.types.Scene.filters_contour_settings = bpy.props.PointerProperty(type=FiltersContourSettings)
        bpy.types.Scene.filters_clip_settings = bpy.props.PointerProperty(type=FiltersClipSettings)
        bpy.types.Scene.filters_slice_settings = bpy.props.PointerProperty(type=FiltersSliceSettings)
        bpy.types.Scene.filters_calculator_settings = bpy.props.PointerProperty(type=FiltersCalculatorSettings)


def unregister():
    global preview_collection
    if preview_collection:
        bpy.utils.previews.remove(preview_collection)

    if LEGEND_DEPS_HANDLER and LEGEND_DEPS_HANDLER in bpy.app.handlers.depsgraph_update_post:
        try:
            bpy.app.handlers.depsgraph_update_post.remove(LEGEND_DEPS_HANDLER)
            print("SciBlend: Legend depsgraph handler unregistered")
        except Exception:
            pass

    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

    if hasattr(bpy.types.Scene, 'legend_settings'):
        del bpy.types.Scene.legend_settings
    if hasattr(bpy.types.Scene, 'custom_colorramp'):
        del bpy.types.Scene.custom_colorramp
    if hasattr(bpy.types.Scene, 'shader_generator_settings'):
        del bpy.types.Scene.shader_generator_settings
    if hasattr(bpy.types.Scene, 'grid_settings'):
        del bpy.types.Scene.grid_settings
    if hasattr(bpy.types.Scene, 'annotation_properties'):
        del bpy.types.Scene.annotation_properties
    if hasattr(bpy.types.Scene, 'shapesgenerator_shapes'):
        del bpy.types.Scene.shapesgenerator_shapes
        del bpy.types.Scene.shapesgenerator_active_shape_index
    if hasattr(bpy.types.Scene, 'shapesgenerator_animated_graphs'):
        del bpy.types.Scene.shapesgenerator_animated_graphs
    if hasattr(bpy.types.Scene, 'shapesgenerator_animated_graphs_dir'):
        del bpy.types.Scene.shapesgenerator_animated_graphs_dir
    if hasattr(bpy.types.Scene, 'cinematography_settings'):
        if hasattr(bpy.types.Scene, "cinematography_settings"):
            del bpy.types.Scene.cinematography_settings
        if hasattr(bpy.types.Object, "camera_range"):
            del bpy.types.Object.camera_range
    if hasattr(bpy.types.Object, 'volume_mesh_info'):
        del bpy.types.Object.volume_mesh_info
    if hasattr(bpy.types.Scene, 'on_demand_volume_enabled'):
        del bpy.types.Scene.on_demand_volume_enabled
    if hasattr(bpy.types.Scene, 'on_demand_data_root'):
        del bpy.types.Scene.on_demand_data_root
    if hasattr(bpy.types.Scene, 'on_demand_max_cached'):
        del bpy.types.Scene.on_demand_max_cached
    if hasattr(bpy.types.Scene, 'filters_emitter_settings'):
        del bpy.types.Scene.filters_emitter_settings
    if hasattr(bpy.types.Scene, 'filters_volume_settings'):
        del bpy.types.Scene.filters_volume_settings
    if hasattr(bpy.types.Scene, 'filters_threshold_settings'):
        del bpy.types.Scene.filters_threshold_settings
    if hasattr(bpy.types.Scene, 'filters_contour_settings'):
        del bpy.types.Scene.filters_contour_settings
    if hasattr(bpy.types.Scene, 'filters_clip_settings'):
        del bpy.types.Scene.filters_clip_settings
    if hasattr(bpy.types.Scene, 'filters_slice_settings'):
        del bpy.types.Scene.filters_slice_settings
    if hasattr(bpy.types.Scene, 'filters_calculator_settings'):
        del bpy.types.Scene.filters_calculator_settings

    if SCIBLENDNODES_AVAILABLE:
        try:
            SCIBLENDNODES_unregister()
        except Exception:
            pass

if __name__ == "__main__":
    register()

bl_info = {
    "name": "SciBlend",
    "author": "José Marín",
    "version": (1, 2, 0),
    "blender": (4, 5, 1),
    "location": "View3D > Sidebar > SciBlend",
    "description": "Scientific visualization tools for Blender",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}
