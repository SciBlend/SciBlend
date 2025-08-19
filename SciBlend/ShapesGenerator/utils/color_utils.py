import json
import os
import bpy
import numpy as np

def load_colormaps():
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
        
        print(f"Colormaps loaded: {list(colormaps.keys())}")
        print(f"Example of colormap '{list(colormaps.keys())[0]}': {colormaps[list(colormaps.keys())[0]][:5]}")
        return colormaps
    except FileNotFoundError:
        print(f"Error: Could not find 'colors.json' file at {json_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Error: The 'colors.json' file at {json_path} is not a valid JSON")
        return {}

def get_colormap_items():
    colormaps = load_colormaps()
    items = [('CUSTOM', "Custom", "Use custom colors")]
    for name in colormaps.keys():
        items.append((name, name.title(), f"Use {name.title()} colormap"))
    return items

def update_colormap(self, context):
    scene = context.scene
    if scene.colormap != 'CUSTOM':
        colormaps = load_colormaps()
        selected_colormap = colormaps.get(scene.colormap, [])
        

        scene.colors_values.clear()
        

        start = scene.colormap_start
        end = scene.colormap_end
        subdivisions = scene.colormap_subdivisions
        
        positions = np.linspace(0, 1, subdivisions)
        values = np.linspace(start, end, subdivisions)
        
        for pos, value in zip(positions, values):
            new_color = scene.colors_values.add()

            color = interpolate_color(selected_colormap, pos)
            new_color.color = color
            new_color.value = f"{value:.2f}"
        
        scene.num_nodes = subdivisions

def interpolate_color(colormap, pos):
    if not colormap:
        return (0, 0, 0)  
    
    for i in range(len(colormap) - 1):
        pos1, color1 = colormap[i]
        pos2, color2 = colormap[i + 1]
        if pos1 <= pos <= pos2:
            t = (pos - pos1) / (pos2 - pos1) if pos2 != pos1 else 0
            interpolated_color = tuple(c1 * (1 - t) + c2 * t for c1, c2 in zip(color1, color2))
            return tuple(max(0, min(1, c)) for c in interpolated_color)
    
    return tuple(max(0, min(1, c)) for c in (colormap[0][1] if pos < colormap[0][0] else colormap[-1][1]))

__all__ = ['load_colormaps', 'get_colormap_items', 'update_colormap']