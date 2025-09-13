import bpy
import json
import os

_COLORMAPS = []
_COLORMAP_BY_ID = {}


def _colors_json_path():
    base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base, 'LegendGenerator', 'colors.json')


def load_colormaps_if_needed():
    global _COLORMAPS, _COLORMAP_BY_ID
    if _COLORMAPS:
        return
    path = _colors_json_path()
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except Exception:
        _COLORMAPS = []
        _COLORMAP_BY_ID = {}
        return

    enum_items = []
    mapping = {}
    index = 0
    for entry in data:
        name = entry.get('Name') or entry.get('name') or f'colormap_{index}'
        rgb_points = entry.get('RGBPoints', [])
        cm_id = name
        enum_items.append((cm_id, name, "", 'COLOR', index))
        mapping[cm_id] = {
            'name': name,
            'rgb_points': rgb_points,
            'nan_color': entry.get('NanColor')
        }
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
    rgb_points = data.get('rgb_points', [])
    if not rgb_points or len(rgb_points) < 4:
        return
    
    colors = []
    for i in range(0, len(rgb_points), 4):
        if i + 3 < len(rgb_points):
            position = float(rgb_points[i])
            r = float(rgb_points[i+1])
            g = float(rgb_points[i+2])
            b = float(rgb_points[i+3])
            colors.append({
                'position': position,
                'color': (r, g, b)
            })
    
    if not colors:
        return
    
    min_pos = min(color['position'] for color in colors)
    max_pos = max(color['position'] for color in colors)
    if min_pos != 0 or max_pos != 1:
        for color in colors:
            color['position'] = (color['position'] - min_pos) / (max_pos - min_pos)
    
    cr = ramp.color_ramp
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    
    first_color = colors[0]
    cr.elements[0].position = first_color['position']
    cr.elements[0].color = first_color['color'] + (1.0,)
    
    for color_data in colors[1:]:
        elem = cr.elements.new(color_data['position'])
        elem.color = color_data['color'] + (1.0,)