import bpy

_COLORMAPS = []
_COLORMAP_BY_ID = {}




def load_colormaps_if_needed():
    global _COLORMAPS, _COLORMAP_BY_ID
    if _COLORMAPS:
        return
    try:
        from ...ShaderGenerator.utils.colormaps import COLORMAPS as SG_COLORMAPS
    except Exception:
        _COLORMAPS = []
        _COLORMAP_BY_ID = {}
        return

    enum_items = []
    mapping = {}
    index = 0
    for name, data in SG_COLORMAPS.items():
        enum_items.append((name, name, "", 'COLOR', index))
        mapping[name] = data
        index += 1
    _COLORMAPS = enum_items
    _COLORMAP_BY_ID = mapping


def get_colormap_enum():
    load_colormaps_if_needed()
    return _COLORMAPS or [("", "(no colormaps)", "")]


def apply_colormap_to_ramp(colormap_id: str, ramp: bpy.types.ShaderNodeValToRGB):
    load_colormaps_if_needed()
    data = _COLORMAP_BY_ID.get(colormap_id)
    if not data:
        return
    colors = data.get('colors')
    if not colors:
        return
    try:
        from ...ShaderGenerator.utils.colormaps import interpolate_colormap
        if len(colors) != 32:
            colors = interpolate_colormap(colors, 32)
    except Exception:
        pass

    cr = ramp.color_ramp
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])

    for i, color_data in enumerate(colors):
        if i == 0:
            elem = cr.elements[0]
        else:
            elem = cr.elements.new(color_data['position'])
        elem.color = color_data['color'] + (1.0,)