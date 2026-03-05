import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    StringProperty, EnumProperty, FloatProperty,
    IntProperty, BoolProperty, CollectionProperty
)


# Static tuple for modifier types - available Blender modifiers useful for scientific visualization
MODIFIER_TYPE_ITEMS = [
    ('SUBSURF', "Subdivision Surface", "Subdivide mesh for smoother appearance", 'MOD_SUBSURF', 0),
    ('SMOOTH', "Smooth", "Smooth vertices based on neighbors", 'MOD_SMOOTH', 1),
    ('LAPLACIANSMOOTH', "Laplacian Smooth", "Laplacian smoothing for volume preservation", 'MOD_SMOOTH', 2),
    ('CORRECTIVE_SMOOTH', "Corrective Smooth", "Smooth while preserving volume", 'MOD_SMOOTH', 3),
    ('DECIMATE', "Decimate", "Reduce polygon count", 'MOD_DECIM', 4),
    ('REMESH', "Remesh", "Generate new topology", 'MOD_REMESH', 5),
    ('SOLIDIFY', "Solidify", "Add thickness to surface", 'MOD_SOLIDIFY', 6),
    ('WIREFRAME', "Wireframe", "Convert to wireframe representation", 'MOD_WIREFRAME', 7),
    ('TRIANGULATE', "Triangulate", "Convert to triangles", 'MOD_TRIANGULATE', 8),
    ('WELD', "Weld", "Merge nearby vertices", 'AUTOMERGE_ON', 9),
    ('WEIGHTED_NORMAL', "Weighted Normal", "Improve shading normals", 'MOD_NORMALEDIT', 10),
    ('EDGE_SPLIT', "Edge Split", "Split edges based on angle", 'MOD_EDGESPLIT', 11),
]


def _collection_items(self, context):
    """Get available collections for targeting."""
    items = [("", "None", "No collection selected")]
    try:
        for c in bpy.data.collections:
            items.append((c.name, c.name, c.name))
    except Exception:
        pass
    return items


class ModifierItem(PropertyGroup):
    """Individual modifier configuration for collection-wide application."""
    
    name: StringProperty(
        name="Name",
        default="Modifier",
    )
    
    modifier_type: EnumProperty(
        name="Type",
        items=MODIFIER_TYPE_ITEMS,
        default='SMOOTH',
    )
    
    enabled: BoolProperty(
        name="Enabled",
        default=True,
    )
    
    # --- Subdivision Surface ---
    subsurf_levels: IntProperty(
        name="Viewport Levels",
        default=1,
        min=0,
        max=6,
    )
    subsurf_render_levels: IntProperty(
        name="Render Levels",
        default=2,
        min=0,
        max=6,
    )
    subsurf_uv_smooth: EnumProperty(
        name="UV Smooth",
        items=[
            ('NONE', "None", "UVs are not smoothed"),
            ('PRESERVE_CORNERS', "Keep Corners", "Smooth UVs, keep corners"),
            ('PRESERVE_CORNERS_AND_JUNCTIONS', "Keep Corners & Junctions", "Keep corners and junctions"),
            ('PRESERVE_CORNERS_JUNCTIONS_AND_CONCAVE', "Keep Corners, Junctions & Concave", "Full preservation"),
            ('PRESERVE_BOUNDARIES', "Keep Boundaries", "Keep UV boundaries"),
            ('SMOOTH_ALL', "Smooth All", "Smooth all UVs"),
        ],
        default='PRESERVE_CORNERS',
    )
    
    # --- Smooth ---
    smooth_factor: FloatProperty(
        name="Factor",
        default=0.5,
        min=0.0,
        max=1.0,
    )
    smooth_iterations: IntProperty(
        name="Iterations",
        default=1,
        min=0,
        max=30,
    )
    
    # --- Laplacian Smooth ---
    laplacian_iterations: IntProperty(
        name="Iterations",
        default=1,
        min=0,
        max=200,
    )
    laplacian_lambda: FloatProperty(
        name="Lambda Factor",
        default=0.01,
        min=-1000.0,
        max=1000.0,
    )
    laplacian_lambda_border: FloatProperty(
        name="Lambda Border",
        default=0.01,
        min=-1000.0,
        max=1000.0,
    )
    laplacian_use_volume_preserve: BoolProperty(
        name="Preserve Volume",
        default=True,
    )
    laplacian_use_normalized: BoolProperty(
        name="Normalized",
        default=True,
    )
    
    # --- Corrective Smooth ---
    corrective_factor: FloatProperty(
        name="Factor",
        default=0.5,
        min=0.0,
        max=1.0,
    )
    corrective_iterations: IntProperty(
        name="Iterations",
        default=5,
        min=0,
        max=200,
    )
    corrective_smooth_type: EnumProperty(
        name="Smooth Type",
        items=[
            ('SIMPLE', "Simple", "Simple smoothing"),
            ('LENGTH_WEIGHTED', "Length Weight", "Weight by edge length"),
        ],
        default='SIMPLE',
    )
    corrective_use_only_smooth: BoolProperty(
        name="Only Smooth",
        default=True,
    )
    corrective_use_pin_boundary: BoolProperty(
        name="Pin Boundaries",
        default=True,
    )
    
    # --- Decimate ---
    decimate_ratio: FloatProperty(
        name="Ratio",
        default=0.5,
        min=0.0,
        max=1.0,
    )
    decimate_mode: EnumProperty(
        name="Mode",
        items=[
            ('COLLAPSE', "Collapse", "Merge vertices to reduce face count"),
            ('UNSUBDIV', "Un-Subdivide", "Reverse subdivision"),
            ('DISSOLVE', "Planar", "Dissolve planar faces"),
        ],
        default='COLLAPSE',
    )
    decimate_angle_limit: FloatProperty(
        name="Angle Limit",
        default=0.087266,  # 5 degrees
        min=0.0,
        max=3.14159,
        subtype='ANGLE',
    )
    decimate_use_symmetry: BoolProperty(
        name="Symmetry",
        default=False,
    )
    
    # --- Remesh ---
    remesh_mode: EnumProperty(
        name="Mode",
        items=[
            ('VOXEL', "Voxel", "Voxel-based remesh"),
            ('SHARP', "Sharp", "Preserve edges"),
            ('SMOOTH', "Smooth", "Smooth output"),
            ('BLOCKS', "Blocks", "Blocky output"),
        ],
        default='VOXEL',
    )
    remesh_voxel_size: FloatProperty(
        name="Voxel Size",
        default=0.1,
        min=0.0001,
        max=10.0,
    )
    remesh_octree_depth: IntProperty(
        name="Octree Depth",
        default=4,
        min=1,
        max=12,
    )
    remesh_scale: FloatProperty(
        name="Scale",
        default=0.9,
        min=0.0,
        max=0.99,
    )
    remesh_use_smooth_shade: BoolProperty(
        name="Smooth Shading",
        default=False,
    )
    remesh_use_remove_disconnected: BoolProperty(
        name="Remove Disconnected",
        default=True,
    )
    
    # --- Solidify ---
    solidify_thickness: FloatProperty(
        name="Thickness",
        default=0.01,
        min=-10.0,
        max=10.0,
    )
    solidify_offset: FloatProperty(
        name="Offset",
        default=-1.0,
        min=-1.0,
        max=1.0,
    )
    solidify_use_even_offset: BoolProperty(
        name="Even Thickness",
        default=False,
    )
    solidify_use_rim: BoolProperty(
        name="Fill Rim",
        default=True,
    )
    solidify_use_rim_only: BoolProperty(
        name="Only Rim",
        default=False,
    )
    
    # --- Wireframe ---
    wireframe_thickness: FloatProperty(
        name="Thickness",
        default=0.02,
        min=0.0,
        max=10.0,
    )
    wireframe_use_replace: BoolProperty(
        name="Replace Original",
        default=True,
    )
    wireframe_use_even_offset: BoolProperty(
        name="Even Thickness",
        default=True,
    )
    wireframe_use_relative_offset: BoolProperty(
        name="Relative Thickness",
        default=False,
    )
    wireframe_use_boundary: BoolProperty(
        name="Boundary",
        default=True,
    )
    
    # --- Triangulate ---
    triangulate_quad_method: EnumProperty(
        name="Quad Method",
        items=[
            ('BEAUTY', "Beauty", "Split quads for best result"),
            ('FIXED', "Fixed", "Split first and third vertices"),
            ('FIXED_ALTERNATE', "Fixed Alternate", "Split second and fourth vertices"),
            ('SHORTEST_DIAGONAL', "Shortest Diagonal", "Split along shortest diagonal"),
            ('LONGEST_DIAGONAL', "Longest Diagonal", "Split along longest diagonal"),
        ],
        default='BEAUTY',
    )
    triangulate_ngon_method: EnumProperty(
        name="N-gon Method",
        items=[
            ('BEAUTY', "Beauty", "Split for best result"),
            ('CLIP', "Clip", "Use ear clipping"),
        ],
        default='BEAUTY',
    )
    triangulate_min_vertices: IntProperty(
        name="Minimum Vertices",
        default=4,
        min=4,
        max=100,
    )
    triangulate_keep_custom_normals: BoolProperty(
        name="Keep Normals",
        default=False,
    )
    
    # --- Weld ---
    weld_threshold: FloatProperty(
        name="Merge Distance",
        default=0.0001,
        min=0.0,
        max=10.0,
        precision=6,
    )
    weld_mode: EnumProperty(
        name="Mode",
        items=[
            ('ALL', "All", "Weld all vertices"),
            ('CONNECTED', "Connected", "Only weld connected vertices"),
        ],
        default='ALL',
    )
    
    # --- Weighted Normal ---
    weighted_normal_mode: EnumProperty(
        name="Weighting Mode",
        items=[
            ('FACE_AREA', "Face Area", "Weight by face area"),
            ('CORNER_ANGLE', "Corner Angle", "Weight by corner angle"),
            ('FACE_AREA_WITH_ANGLE', "Face Area & Angle", "Combine both"),
        ],
        default='FACE_AREA',
    )
    weighted_normal_weight: IntProperty(
        name="Weight",
        default=50,
        min=1,
        max=100,
    )
    weighted_normal_thresh: FloatProperty(
        name="Threshold",
        default=0.01,
        min=0.0,
        max=10.0,
    )
    weighted_normal_keep_sharp: BoolProperty(
        name="Keep Sharp",
        default=False,
    )
    weighted_normal_face_influence: BoolProperty(
        name="Face Influence",
        default=False,
    )
    
    # --- Edge Split ---
    edge_split_angle: FloatProperty(
        name="Split Angle",
        default=0.523599,  # 30 degrees
        min=0.0,
        max=3.14159,
        subtype='ANGLE',
    )
    edge_split_use_edge_angle: BoolProperty(
        name="Edge Angle",
        default=True,
    )
    edge_split_use_edge_sharp: BoolProperty(
        name="Sharp Edges",
        default=True,
    )


class CollectionModifiersSettings(PropertyGroup):
    """Container for collection modifiers with list management."""
    
    target_collection: EnumProperty(
        name="Collection",
        description="Collection to apply modifiers to",
        items=_collection_items,
    )
    
    modifier_items_index: IntProperty(
        name="Active Modifier Index",
        default=0,
        min=0,
    )
    
    auto_update: BoolProperty(
        name="Auto Update",
        description="Automatically update modifiers when settings change",
        default=False,
    )


def register():
    pass


def unregister():
    pass

