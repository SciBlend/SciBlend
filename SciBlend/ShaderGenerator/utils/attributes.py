import bpy
from bpy.app.handlers import persistent


_attribute_cache = {}


@persistent
def _cleanup_attribute_cache(dummy):
    """Clean up attribute cache for objects that no longer exist.
    
    This handler is called on depsgraph updates to remove stale cache entries.
    """
    global _attribute_cache
    if not _attribute_cache:
        return
    
    # Get all current object names
    current_objects = {obj.name for obj in bpy.data.objects if obj.type == 'MESH'}
    
    # Remove cache entries for objects that no longer exist
    stale_keys = [key for key in _attribute_cache.keys() if key not in current_objects]
    for key in stale_keys:
        del _attribute_cache[key]


def get_attribute_items(self, context):
    """Enumerate mesh attribute names usable for color mapping in the active object.

    Returns a list of (identifier, name, description) suitable for Blender EnumProperty items.
    The list is cached and kept stable to prevent attribute jumping when values change frame-by-frame.
    """
    obj = getattr(context, 'active_object', None)
    if not obj or getattr(obj, 'type', None) != 'MESH':
        return [("Col", "Col", "Default attribute name")]
    
    # Use object name as cache key
    obj_key = obj.name
    
    current_attrs = set()
    attr_info = {}
    try:
        depsgraph = context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        mesh_eval = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
        try:
            for attr in mesh_eval.attributes:
                # Skip internal Blender attributes (starting with '.')
                if attr.name.startswith('.'):
                    continue
                if attr.data_type in {'FLOAT', 'FLOAT_VECTOR', 'INT', 'INT8', 'INT32', 'BOOLEAN'}:
                    current_attrs.add(attr.name)
                    attr_info[attr.name] = (attr.domain, attr.data_type)
        finally:
            obj_eval.to_mesh_clear()
    except Exception:
        pass
    
    # If we have cached attributes for this object, update the cache intelligently
    if obj_key in _attribute_cache:
        cached_attrs = _attribute_cache[obj_key]
        # Keep all attributes that still exist, add new ones
        all_attrs = set(cached_attrs.keys()) | current_attrs
        # Remove attributes that haven't been seen in a while (only if we found new ones)
        if current_attrs:
            # Update or add current attributes
            for attr_name in current_attrs:
                cached_attrs[attr_name] = attr_info.get(attr_name, ('POINT', 'FLOAT'))
            # Remove attributes that are definitely gone (not in current evaluation)
            # But only if the current mesh has attributes (to avoid clearing during temporary states)
            attrs_to_remove = [name for name in cached_attrs.keys() if name not in current_attrs]
            # Only remove if we have a good sample of current attributes
            if len(current_attrs) > 0:
                pass
    else:
        # First time seeing this object, create cache entry
        _attribute_cache[obj_key] = attr_info if attr_info else {}
    
    # Build items list from cache, sorted alphabetically for stability
    # Skip internal Blender attributes (starting with '.')
    items = []
    cached_attrs = _attribute_cache.get(obj_key, {})
    for attr_name in sorted(cached_attrs.keys()):
        if attr_name.startswith('.'):
            continue
        domain, data_type = cached_attrs[attr_name]
        desc = f"Domain: {domain}, Type: {data_type}"
        items.append((attr_name, attr_name, desc))
    
    if not items:
        items = [("Col", "Col", "Default attribute name")]
    
    return items


def clear_attribute_cache(obj_name=None):
    """Clear the attribute cache for a specific object or all objects.
    
    Parameters
    ----------
    obj_name : str | None
        If provided, clear cache only for this object. If None, clear all.
    """
    global _attribute_cache
    if obj_name is None:
        _attribute_cache.clear()
    elif obj_name in _attribute_cache:
        del _attribute_cache[obj_name]


def get_color_range(obj, attribute_name, normalization='AUTO'):
    """Compute the numeric range for a named attribute with optional global normalization.
    
    NaN and infinite values are automatically filtered out from the range calculation.

    Parameters
    ----------
    obj : bpy.types.Object
        The object whose attribute range is requested.
    attribute_name : str
        The attribute name to evaluate.
    normalization : str
        One of 'AUTO', 'GLOBAL', or 'NONE'.

    Returns
    -------
    tuple[float, float]
        Minimum and maximum values (excluding NaN and inf).
    """
    import math
    
    def is_valid_value(v):
        """Check if a value is valid (not NaN and not infinite)."""
        return not (math.isnan(v) or math.isinf(v))
    
    if normalization == 'GLOBAL':
        all_values = []
        for o in bpy.data.objects:
            if getattr(o, 'type', None) == 'MESH' and hasattr(getattr(o, 'data', None), 'attributes') and attribute_name in o.data.attributes:
                attribute = o.data.attributes[attribute_name]
                try:
                    if attribute.data_type == 'FLOAT':
                        values = [data.value for data in attribute.data if is_valid_value(data.value)]
                        all_values.extend(values)
                    elif attribute.data_type == 'FLOAT_VECTOR':
                        values = [data.vector.length for data in attribute.data]
                        values = [v for v in values if is_valid_value(v)]
                        all_values.extend(values)
                    elif attribute.data_type in {'INT', 'INT8', 'INT32'}:
                        values = [float(data.value) for data in attribute.data]
                        all_values.extend(values)
                    elif attribute.data_type == 'BOOLEAN':
                        values = [float(data.value) for data in attribute.data]
                        all_values.extend(values)
                except (AttributeError, TypeError, ValueError):
                    continue
        if all_values:
            return (min(all_values), max(all_values))
        return (0, 1)

    if getattr(obj, 'type', None) != 'MESH' or attribute_name not in getattr(getattr(obj, 'data', None), 'attributes', {}):
        return (0, 1)

    attribute = obj.data.attributes[attribute_name]
    values = []
    try:
        if attribute.data_type == 'FLOAT':
            values = [data.value for data in attribute.data if is_valid_value(data.value)]
        elif attribute.data_type == 'FLOAT_VECTOR':
            values = [data.vector.length for data in attribute.data]
            values = [v for v in values if is_valid_value(v)]
        elif attribute.data_type in {'INT', 'INT8', 'INT32'}:
            values = [float(data.value) for data in attribute.data]
        elif attribute.data_type == 'BOOLEAN':
            values = [float(data.value) for data in attribute.data]
    except (AttributeError, TypeError, ValueError):
        pass
    
    if not values:
        return (0, 1)

    return (min(values), max(values)) 