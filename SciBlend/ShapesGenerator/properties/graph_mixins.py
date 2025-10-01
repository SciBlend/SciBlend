import bpy
from typing import List, Tuple


def enum_float_attributes(self, context) -> List[Tuple[str, str, str]]:
    """Enumerate FLOAT attributes from the selected collection (preferred) or active object.

    When a collection is selected in `graph_collection`, aggregate unique FLOAT attribute
    names across all mesh objects in that collection; otherwise, fall back to the active object.
    """
    try:
        from ..utils.mesh_attributes import list_float_attributes
    except Exception:
        return [("", "(no FLOAT attributes)", "")]
    coll = getattr(self, 'graph_collection', None)
    if coll and getattr(coll, 'objects', None):
        seen = {}
        try:
            for obj in coll.objects:
                for ident, name, desc in list_float_attributes(obj):
                    if not ident:
                        continue
                    if ident not in seen:
                        seen[ident] = (ident, name, desc)
        except Exception:
            pass
        items = list(seen.values())
        return items if items else [("", "(no FLOAT attributes)", "")]
    source = getattr(context, 'active_object', None)
    return list_float_attributes(source) if source else [("", "(no FLOAT attributes)", "")] 