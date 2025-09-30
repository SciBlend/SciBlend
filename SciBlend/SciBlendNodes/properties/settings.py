import bpy
from bpy.types import PropertyGroup
from bpy.props import PointerProperty, StringProperty, EnumProperty, CollectionProperty, IntProperty, FloatProperty, FloatVectorProperty, BoolProperty
from .collection_item import CollectionListItem
from .preset_item import PresetListItem
from ..utils.attributes import float_attribute_items_for_context, vector_attribute_items_for_context, float_attribute_items_with_none


def _collection_items(self, context):
    items = [("", "None", "No collection selected")]
    try:
        for c in bpy.data.collections:
            items.append((c.name, c.name, c.name))
    except Exception:
        pass
    return items


def _nodegroup_items(self, context):
    items = [("", "None", "No node group selected")]
    try:
        for ng in bpy.data.node_groups:
            if getattr(ng, 'bl_idname', '') == 'GeometryNodeTree':
                items.append((ng.name, ng.name, ng.name))
    except Exception:
        pass
    return items


def _rebuild_collections_list(settings: 'SciBlendNodesSettings') -> None:
    """Rebuild the collections_list based on the current search_filter."""
    try:
        settings.collections_list.clear()
        for coll in bpy.data.collections:
            if settings.search_filter and settings.search_filter.lower() not in coll.name.lower():
                continue
            item = settings.collections_list.add()
            item.name = coll.name
    except Exception:
        pass


def _on_change_search(self, context):
    """Update callback for search_filter to rebuild the list outside of draw."""
    try:
        _rebuild_collections_list(self)
    except Exception:
        pass


def _on_change_target_collection(self, context):
    """Synchronize UI/presets when the target collection changes.

    - Logs owned SciBlend modifiers in the selected collection.
    - If a preset row exists for the collection, select it.
    - If not, and we detect an owned modifier, auto-create a preset row linked to the node group and seed key values.
    """
    try:
        coll_name = getattr(self, 'target_collection', '')
        print(f"[SciBlend Nodes][Selection] target_collection -> '{coll_name}'")
        coll = bpy.data.collections.get(coll_name) if coll_name else None
        if not coll:
            print("[SciBlend Nodes][Selection] Collection not found")
            return
        def _iter_objs(c):
            try:
                return list(getattr(c, 'all_objects', [])) or list(getattr(c, 'objects', []))
            except Exception:
                return list(getattr(c, 'objects', []))
        owned = []
        for obj in _iter_objs(coll):
            if getattr(obj, 'type', None) != 'MESH':
                continue
            for m in obj.modifiers:
                if m.type == 'NODES' and bool(m.get('sciblend_nodes', False)):
                    owned.append((obj.name, m.name, m.get('sciblend_group', '')))
        print(f"[SciBlend Nodes][Selection] Owned modifiers in '{coll_name}': {owned}")
        match_idx = next((i for i, p in enumerate(self.presets) if getattr(p, 'collection_name', '') == coll_name), -1) if getattr(self, 'presets', None) else -1
        if match_idx >= 0:
            print(f"[SciBlend Nodes][Selection] Selecting preset index {match_idx} for collection '{coll_name}'")
            self.presets_index = match_idx
        else:
            if owned:
                grp = owned[0][2]
                if grp and grp in bpy.data.node_groups:
                    item = self.presets.add()
                    item.collection_name = coll_name
                    item.node_group_name = grp
                    # Guess preset type and seed values
                    ng = bpy.data.node_groups[grp]
                    preset_type = 'POINTS_SHADER'
                    radius_val = None
                    for n in ng.nodes:
                        if n.bl_idname == 'GeometryNodeMeshToPoints':
                            try:
                                radius_val = float(getattr(n.inputs['Radius'], 'default_value', None))
                            except Exception:
                                try:
                                    radius_val = float(n.inputs[3].default_value)
                                except Exception:
                                    radius_val = None
                    if radius_val is not None:
                        item.points_radius = radius_val
                    item.preset = preset_type
                    self.presets_index = len(self.presets) - 1
                    print(f"[SciBlend Nodes][Selection] Auto-created preset row for '{coll_name}' linked to group '{grp}', seeded radius={item.points_radius}")
            else:
                print(f"[SciBlend Nodes][Selection] No presets and no owned modifiers for collection '{coll_name}'")
    except Exception as e:
        print(f"[SciBlend Nodes][Selection] Exception: {e}")


def _on_change_collection_index(self, context):
    """Update target_collection when the user selects an entry in the Collections UI list."""
    try:
        if not getattr(self, 'collections_list', None):
            return
        idx = int(getattr(self, 'collections_list_index', -1))
        if 0 <= idx < len(self.collections_list):
            name = self.collections_list[idx].name
            print(f"[SciBlend Nodes][Selection] collections_list_index -> {idx} ('{name}')")
            try:
                self.target_collection = name
            except Exception as e:
                print(f"[SciBlend Nodes][Selection] Error setting target_collection: {e}")
    except Exception as e:
        print(f"[SciBlend Nodes][Selection] Index update exception: {e}")


class SciBlendNodesSettings(PropertyGroup):
    """Settings for SciBlend Nodes: target collection and geometry nodes filter selection."""

    target_collection: EnumProperty(
        name="Collection",
        description="Collection to target for geometry nodes filters",
        items=_collection_items,
        update=_on_change_target_collection,
    )

    node_group_name: EnumProperty(
        name="Geometry Nodes",
        description="Geometry Nodes node group to apply to meshes in the collection",
        items=_nodegroup_items,
    )

    search_filter: StringProperty(
        name="Search",
        description="Filter collections by name",
        default="",
        update=_on_change_search,
    )

    rename_collection_name: StringProperty(
        name="New Name",
        description="New name for the selected collection",
        default="",
    )

    collections_list: CollectionProperty(type=CollectionListItem)
    collections_list_index: IntProperty(default=0, update=_on_change_collection_index)

    preset: EnumProperty(
        name="Preset",
        items=[
            ('POINTS_SHADER', "Points + Shader", "Convert mesh to points and set material"),
            ('DISPLACE_NORMAL', "Displace by Attribute", "Displace vertices along normal scaled by a mesh attribute"),
            ('VECTOR_GLYPHS', "Vector Glyphs", "Instance oriented cones from a vector attribute"),
        ],
        default='POINTS_SHADER',
    )

    attribute_name: EnumProperty(name="Attribute", items=float_attribute_items_for_context)
    vector_attribute_name: EnumProperty(name="Vector Attribute", items=vector_attribute_items_for_context)
    scale_attribute_name: EnumProperty(name="Scale Attribute", items=float_attribute_items_with_none)
    material_name: StringProperty(name="Material", default="")
    scale: FloatProperty(name="Scale", default=1.0, min=0.0)

    glyph_density: FloatProperty(name="Density", description="Probability of keeping a point for glyph instancing", default=1.0, min=0.0, max=1.0)
    glyph_max_count: IntProperty(name="Max Glyphs", description="Maximum number of glyphs to instance per object (0 = no cap)", default=10000, min=0)
    glyph_primitive: EnumProperty(
        name="Primitive",
        items=[
            ('CONE', "Cone", "Cone glyph"),
            ('CYLINDER', "Cylinder", "Cylinder glyph"),
            ('UV_SPHERE', "UV Sphere", "UV Sphere glyph"),
        ],
        default='CONE',
    )

    cone_vertices: IntProperty(name="Vertices", default=16, min=3, soft_max=128)
    cone_radius_top: FloatProperty(name="Radius Top", default=0.0, min=0.0)
    cone_radius_bottom: FloatProperty(name="Radius Bottom", default=0.02, min=0.0)
    cone_depth: FloatProperty(name="Depth", default=0.1, min=0.0)

    cyl_vertices: IntProperty(name="Vertices", default=16, min=3, soft_max=128)
    cyl_radius: FloatProperty(name="Radius", default=0.02, min=0.0)
    cyl_depth: FloatProperty(name="Depth", default=0.1, min=0.0)

    sphere_segments: IntProperty(name="Segments", default=16, min=3, soft_max=256)
    sphere_rings: IntProperty(name="Rings", default=8, min=2, soft_max=256)
    sphere_radius: FloatProperty(name="Radius", default=0.05, min=0.0)

    radius: FloatProperty(name="Radius", default=0.05, min=0.0)
    voxel_size: FloatProperty(name="Voxel Size", default=0.1, min=0.0)
    threshold: FloatProperty(name="Threshold", default=0.1, min=0.0)
    plane_point: FloatVectorProperty(name="Plane Point", default=(0.0, 0.0, 0.0))
    plane_normal: FloatVectorProperty(name="Plane Normal", default=(0.0, 0.0, 1.0))

    points_radius: FloatProperty(name="Point Size", default=0.05, min=0.0)

    presets: CollectionProperty(type=PresetListItem)
    presets_index: IntProperty(default=0)

    auto_apply: BoolProperty(name="Auto-apply", default=False)
    last_applied_signature: StringProperty(name="_last_sig", default="")
    last_applied_group_name: StringProperty(name="_last_group", default="") 