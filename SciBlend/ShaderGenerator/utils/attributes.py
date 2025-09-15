import bpy


def get_attribute_items(self, context):
    """Enumerate mesh attribute names usable for color mapping in the active object.

    Returns a list of (identifier, name, description) suitable for Blender EnumProperty items.
    """
    items = []
    obj = getattr(context, 'active_object', None)
    if obj and getattr(obj, 'type', None) == 'MESH':
        try:
            depsgraph = context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(depsgraph)
            mesh_eval = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
            try:
                for attr in mesh_eval.attributes:
                    if attr.data_type in {'FLOAT', 'FLOAT_VECTOR'}:
                        desc = f"Domain: {attr.domain}, Type: {attr.data_type}"
                        items.append((attr.name, attr.name, desc))
            finally:
                obj_eval.to_mesh_clear()
        except Exception:
            pass
    if not items:
        items = [("Col", "Col", "Default attribute name")]
    return items


def get_color_range(obj, attribute_name, normalization='AUTO'):
    """Compute the numeric range for a named attribute with optional global normalization.

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
        Minimum and maximum values.
    """
    if normalization == 'GLOBAL':
        all_values = []
        for o in bpy.data.objects:
            if getattr(o, 'type', None) == 'MESH' and hasattr(getattr(o, 'data', None), 'attributes') and attribute_name in o.data.attributes:
                attribute = o.data.attributes[attribute_name]
                if attribute.data_type == 'FLOAT':
                    values = [data.value for data in attribute.data]
                    all_values.extend(values)
                elif attribute.data_type == 'FLOAT_VECTOR':
                    values = [data.vector.length for data in attribute.data]
                    all_values.extend(values)
        if all_values:
            return (min(all_values), max(all_values))
        return (0, 1)

    if getattr(obj, 'type', None) != 'MESH' or attribute_name not in getattr(getattr(obj, 'data', None), 'attributes', {}):
        return (0, 1)

    attribute = obj.data.attributes[attribute_name]
    if attribute.data_type == 'FLOAT':
        values = [data.value for data in attribute.data]
    elif attribute.data_type == 'FLOAT_VECTOR':
        values = [data.vector.length for data in attribute.data]
    else:
        return (0, 1)

    return (min(values), max(values)) 