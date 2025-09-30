import bpy
from typing import List, Tuple


def _find_context_mesh_object(self, context) -> bpy.types.Object | None:
    """Return a representative mesh object based on the active object or the selected target collection.

    Preference order:
    1) Active object if it is a mesh.
    2) First mesh object found in the currently selected target collection in SciBlend Nodes settings.
    """
    obj = getattr(context, 'active_object', None)
    if obj and getattr(obj, 'type', None) == 'MESH':
        return obj
    try:
        sc = getattr(context, 'scene', None)
        settings = getattr(sc, 'sciblend_nodes_settings', None)
        coll_name = getattr(settings, 'target_collection', '') if settings else ''
        coll = bpy.data.collections.get(coll_name) if coll_name else None
        if coll:
            try:
                all_objects = list(getattr(coll, 'all_objects', [])) or list(getattr(coll, 'objects', []))
            except Exception:
                all_objects = list(getattr(coll, 'objects', []))
            for o in all_objects:
                if getattr(o, 'type', None) == 'MESH':
                    return o
    except Exception:
        pass
    return None


def _attribute_items_for_object(obj: bpy.types.Object, allowed_types: set[str], fallback: Tuple[str, str, str]) -> List[Tuple[str, str, str]]:
    """Build an EnumProperty items list for attributes on a mesh object filtered by data type.

    Parameters
    ----------
    obj: Target object. Must be a mesh.
    allowed_types: Set of Blender attribute data types to include, e.g. {'FLOAT'} or {'FLOAT_VECTOR'}.
    fallback: Single item to return when no attributes are found, as (identifier, name, description).
    """
    items: List[Tuple[str, str, str]] = []
    try:
        if not obj or getattr(obj, 'type', None) != 'MESH' or not getattr(obj, 'data', None):
            return [fallback]
        attrs = getattr(obj.data, 'attributes', None)
        if not attrs:
            return [fallback]
        for a in attrs:
            data_type = getattr(a, 'data_type', '')
            if data_type not in allowed_types:
                continue
            domain = getattr(a, 'domain', '')
            desc = f"Domain: {domain}, Type: {data_type}"
            items.append((a.name, a.name, desc))
    except Exception:
        items = []
    return items or [fallback]


def float_attribute_items_for_context(self, context):
    """Enumerate FLOAT attributes for the current context, suitable for EnumProperty items."""
    obj = _find_context_mesh_object(self, context)
    return _attribute_items_for_object(obj, {'FLOAT'}, ("Col", "Col", "Default float attribute"))


def float_attribute_items_with_none(self, context):
    """Enumerate FLOAT attributes and include a '(none)' option to disable attribute-based scaling."""
    base = float_attribute_items_for_context(self, context)
    seen = set()
    dedup = []
    for ident, name, desc in base:
        if ident in seen:
            continue
        seen.add(ident)
        dedup.append((ident, name, desc))
    return [("NONE", "(none)", "Use vector magnitude")] + dedup


def _detect_xyz_component_triplets(obj: bpy.types.Object) -> List[Tuple[str, str, str, str]]:
    """Return composite vector candidates as tuples (label, x_name, y_name, z_name).

    Recognizes suffix patterns: '_X', '_Y', '_Z' or '.X', '.Y', '.Z' or ' X', ' Y', ' Z'. Case-insensitive.
    """
    if not obj or getattr(obj, 'type', None) != 'MESH' or not getattr(obj, 'data', None):
        return []
    try:
        attrs = getattr(obj.data, 'attributes', None)
        if not attrs:
            return []
        float_names = [a.name for a in attrs if getattr(a, 'data_type', '') == 'FLOAT']
        by_base: dict[str, dict[str, str]] = {}
        def add_component(base: str, comp: str, orig_name: str):
            base_key = base.strip()
            comp_key = comp.upper()
            if comp_key not in {'X','Y','Z'}:
                return
            if base_key not in by_base:
                by_base[base_key] = {}
            by_base[base_key][comp_key] = orig_name
        for name in float_names:
            low = name.lower()
            if low.endswith('_x') or low.endswith('_y') or low.endswith('_z'):
                base = name[:-2]
                add_component(base, name[-1], name)
                continue
            if low.endswith('.x') or low.endswith('.y') or low.endswith('.z'):
                base = name[:-2]
                add_component(base, name[-1], name)
                continue
            if low.endswith(' x') or low.endswith(' y') or low.endswith(' z'):
                base = name[:-2]
                add_component(base, name[-1], name)
                continue
        items: List[Tuple[str, str, str, str]] = []
        for base, comps in by_base.items():
            if all(k in comps for k in ('X','Y','Z')):
                label = base
                items.append((label, comps['X'], comps['Y'], comps['Z']))
        return items
    except Exception:
        return []


def vector_attribute_items_for_context(self, context):
    """Enumerate vector attributes for the current context.

    Includes native FLOAT_VECTOR attributes and composite (X,Y,Z) float triplets encoded as 'COMPOSITE|X|Y|Z'.
    """
    obj = _find_context_mesh_object(self, context)
    vector_items = _attribute_items_for_object(obj, {'FLOAT_VECTOR'}, ("velocity", "velocity", "Default vector attribute"))
    try:
        composites = _detect_xyz_component_triplets(obj)
        for label, x_name, y_name, z_name in composites:
            ident = f"COMPOSITE|{x_name}|{y_name}|{z_name}"
            desc = f"Composite from {x_name}, {y_name}, {z_name}"
            vector_items.append((ident, label, desc))
    except Exception:
        pass
    seen = set()
    dedup: List[Tuple[str, str, str]] = []
    for it in vector_items:
        if it[0] in seen:
            continue
        seen.add(it[0])
        dedup.append(it)
    return dedup or [("velocity", "velocity", "Default vector attribute")] 