import bpy
import numpy as np
from typing import List, Tuple


def list_float_attributes(obj: bpy.types.Object) -> List[Tuple[str, str, str]]:
    """Return a list of FLOAT mesh attribute names for the given object.

    The list items are (identifier, name, description) suitable for EnumProperty items.
    If the object is not a mesh or has no numeric attributes, returns a single placeholder item.
    """
    items: List[Tuple[str, str, str]] = []
    try:
        if obj and getattr(obj, 'type', None) == 'MESH' and getattr(obj, 'data', None):
            attrs = getattr(obj.data, 'attributes', None)
            if attrs:
                for a in attrs:
                    data_type = getattr(a, 'data_type', '')
                    if data_type != 'FLOAT':
                        continue
                    domain = getattr(a, 'domain', '')
                    desc = f"Domain: {domain}, Type: {data_type}"
                    items.append((a.name, a.name, desc))
    except Exception:
        items = []
    if not items:
        items = [("", "(no FLOAT attributes)", "")]
    return items


def read_float_attribute(obj: bpy.types.Object, attribute_name: str) -> np.ndarray:
    """Read a FLOAT mesh attribute values into a 1D numpy array.

    Returns an empty array if the attribute does not exist or is not FLOAT.
    """
    try:
        if not obj or getattr(obj, 'type', None) != 'MESH' or not getattr(obj, 'data', None):
            return np.asarray([], dtype=float)
        attrs = getattr(obj.data, 'attributes', None)
        if not attrs or attribute_name not in attrs:
            return np.asarray([], dtype=float)
        attr = attrs[attribute_name]
        if getattr(attr, 'data_type', '') != 'FLOAT':
            return np.asarray([], dtype=float)
        values = [getattr(d, 'value', 0.0) for d in attr.data]
        arr = np.asarray(values, dtype=float)
        if arr.size == 0:
            return arr
        mask = np.isfinite(arr)
        return arr[mask]
    except Exception:
        return np.asarray([], dtype=float) 