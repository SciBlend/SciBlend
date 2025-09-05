import json
import os
import bpy
import numpy as np

_CACHED_COLORMAPS = None


def load_colormaps():
    global _CACHED_COLORMAPS
    if _CACHED_COLORMAPS is not None:
        return _CACHED_COLORMAPS
    addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(addon_dir, 'colors.json')
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        colormaps = {}
        for colormap in data:
            name = colormap['Name']
            rgb_points = colormap['RGBPoints']
            colors = []
            for i in range(0, len(rgb_points), 4):
                pos = rgb_points[i]
                r, g, b = rgb_points[i+1:i+4]
                colors.append((pos, (r, g, b)))
            colormaps[name.upper()] = colors
        _CACHED_COLORMAPS = colormaps
        return colormaps
    except FileNotFoundError:
        print(f"Error: Could not find 'colors.json' file at {json_path}")
        _CACHED_COLORMAPS = {}
        return {}
    except json.JSONDecodeError:
        print(f"Error: The 'colors.json' file at {json_path} is not a valid JSON")
        _CACHED_COLORMAPS = {}
        return {}


def get_colormap_items():
    colormaps = load_colormaps()
    items = [('CUSTOM', "Custom", "Use custom colors")]
    for name in colormaps.keys():
        items.append((name, name.title(), f"Use {name.title()} colormap"))
    return items


def update_colormap(self, context):
    scene = context.scene
    settings = scene.legend_settings
    if settings.colormap != 'CUSTOM':
        colormaps = load_colormaps()
        selected_colormap = colormaps.get(settings.colormap, [])
        
        settings.colors_values.clear()

        start = settings.colormap_start
        end = settings.colormap_end
        subdivisions = settings.colormap_subdivisions
        
        positions = np.linspace(0, 1, subdivisions)
        values = np.linspace(start, end, subdivisions)
        
        for pos, value in zip(positions, values):
            new_color = settings.colors_values.add()
            color = interpolate_color(selected_colormap, pos)
            new_color.color = color
            new_color.value = f"{value:.2f}"
        
        settings.num_nodes = subdivisions


def interpolate_color(colormap, pos):
    if not colormap:
        return (0, 0, 0)
    if pos <= colormap[0][0]:
        return colormap[0][1]
    if pos >= colormap[-1][0]:
        return colormap[-1][1]
    for i in range(len(colormap) - 1):
        p0, c0 = colormap[i]
        p1, c1 = colormap[i+1]
        if p0 <= pos <= p1:
            t = (pos - p0) / (p1 - p0) if p1 != p0 else 0.0
            r = c0[0] + (c1[0] - c0[0]) * t
            g = c0[1] + (c1[1] - c0[1]) * t
            b = c0[2] + (c1[2] - c0[2]) * t
            return (r, g, b)
    return colormap[-1][1]

__all__ = ['load_colormaps', 'get_colormap_items', 'update_colormap']