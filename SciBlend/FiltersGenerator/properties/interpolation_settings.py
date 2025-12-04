"""Properties for Attribute Interpolation settings."""

import bpy
from bpy.props import PointerProperty, StringProperty, EnumProperty, FloatProperty, IntProperty, BoolProperty


def _get_collections(self, context):
    """Enumerate available collections."""
    items = []
    for coll in bpy.data.collections:
        # Count mesh objects in collection
        mesh_count = sum(1 for obj in coll.objects if obj.type == 'MESH')
        if mesh_count > 0:
            items.append((coll.name, coll.name, f"{mesh_count} mesh(es)"))
    if not items:
        items = [("", "(no collections)", "No collections with meshes found")]
    return items


def _get_scalar_attributes(self, context):
    """Enumerate scalar attributes from meshes in the target collection."""
    items = []
    found_attrs = set()
    
    coll_name = getattr(self, 'target_collection', '')
    if coll_name:
        coll = bpy.data.collections.get(coll_name)
        if coll:
            for obj in coll.objects:
                if obj.type != 'MESH' or not obj.data:
                    continue
                attrs = getattr(obj.data, 'attributes', None)
                if not attrs:
                    continue
                for a in attrs:
                    if a.name.startswith('.'):
                        continue
                    if a.name in found_attrs:
                        continue
                    data_type = getattr(a, 'data_type', '')
                    domain = getattr(a, 'domain', '')
                    if data_type in {'FLOAT', 'FLOAT_VECTOR', 'INT', 'INT8', 'INT32'} and domain in {'POINT', 'VERTEX'}:
                        type_label = "scalar" if data_type == 'FLOAT' else "vector→mag" if data_type == 'FLOAT_VECTOR' else "int"
                        items.append((a.name, a.name, f"{domain} {type_label} attribute"))
                        found_attrs.add(a.name)
    
    if not items:
        items = [("", "(no attributes)", "No scalar attributes found")]
    return items


class FiltersInterpolationSettings(bpy.types.PropertyGroup):
    """Settings for the Attribute Interpolation filter."""
    
    target_collection: EnumProperty(
        name="Target Collection",
        description="Collection containing meshes to interpolate",
        items=_get_collections
    )
    
    source_attribute: EnumProperty(
        name="Source Attribute",
        description="Attribute to interpolate from",
        items=_get_scalar_attributes
    )
    
    method: EnumProperty(
        name="Method",
        description="Smoothing/interpolation method to use",
        items=[
            ('IDW', "IDW Smoothing", "Inverse distance weighted average of neighbors (excludes self)"),
            ('GAUSSIAN', "Gaussian Smoothing", "Gaussian-weighted average for smooth results"),
            ('LAPLACIAN', "Laplacian Smoothing", "Topology-based smoothing using mesh connectivity"),
            ('NEAREST', "Nearest Neighbor", "Replace with nearest neighbor's value (excludes self)"),
            ('SHEPARD', "Shepard (VTK)", "Volumetric interpolation via VTK Shepard method"),
        ],
        default='IDW'
    )
    
    k_neighbors: IntProperty(
        name="K Neighbors",
        description="Number of neighbors to consider for smoothing",
        default=8,
        min=1,
        max=128
    )
    
    idw_power: FloatProperty(
        name="IDW Power",
        description="Distance weighting power (higher = more local influence)",
        default=2.0,
        min=0.1,
        max=10.0
    )
    
    gaussian_sigma: FloatProperty(
        name="Sigma",
        description="Gaussian standard deviation (larger = smoother)",
        default=1.0,
        min=0.01,
        max=100.0
    )
    
    laplacian_iterations: IntProperty(
        name="Iterations",
        description="Number of Laplacian smoothing iterations",
        default=1,
        min=1,
        max=100
    )
    
    laplacian_factor: FloatProperty(
        name="Factor",
        description="Blend factor (0 = no change, 1 = full neighbor average)",
        default=0.5,
        min=0.0,
        max=1.0
    )
    
    shepard_power: FloatProperty(
        name="Shepard Power",
        description="Power parameter for Shepard interpolation",
        default=2.0,
        min=0.1,
        max=10.0
    )
    
    shepard_resolution: IntProperty(
        name="Resolution",
        description="Sample resolution for Shepard interpolation volume",
        default=50,
        min=10,
        max=200
    )
    
    include_self: BoolProperty(
        name="Include Self",
        description="Include vertex's own value in the average (reduces smoothing effect)",
        default=False
    )
    
    output_name: StringProperty(
        name="Output Name",
        description="Name for the new interpolated attribute",
        default="interpolated"
    )


def register():
    bpy.utils.register_class(FiltersInterpolationSettings)


def unregister():
    bpy.utils.unregister_class(FiltersInterpolationSettings)

