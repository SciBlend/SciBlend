import bpy
from typing import List, Tuple


def enum_float_attributes(self, context) -> List[Tuple[str, str, str]]:
    """Enumerate FLOAT attributes of the selected graph source object or active object."""
    try:
        from ..utils.mesh_attributes import list_float_attributes
    except Exception:
        return [("", "(no FLOAT attributes)", "")]
    source = getattr(self, 'graph_object', None) or getattr(context, 'active_object', None)
    return list_float_attributes(source) if source else [("", "(no FLOAT attributes)", "")] 