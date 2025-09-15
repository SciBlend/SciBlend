import os
import json
import numpy as np
import logging

logger = logging.getLogger(__name__)


def load_colormaps_from_json(filepath):
    """Load colormaps from a ParaView JSON file and normalize stop positions to [0, 1].

    Parameters
    ----------
    filepath : str
        Absolute path to the JSON file containing colormap definitions.

    Returns
    -------
    dict
        Mapping from colormap name to a dict with keys 'colors', 'nan_color', and 'color_space'.
    """
    with open(filepath, 'r') as f:
        data = json.load(f)

    colormaps = {}
    for colormap in data:
        name = colormap['Name']
        rgb_points = colormap['RGBPoints']
        colors = []
        for i in range(0, len(rgb_points), 4):
            position = rgb_points[i]
            r, g, b = rgb_points[i + 1:i + 4]
            colors.append({'position': position, 'color': (r, g, b)})

        min_pos = min(color['position'] for color in colors)
        max_pos = max(color['position'] for color in colors)
        if min_pos != 0 or max_pos != 1:
            for color in colors:
                color['position'] = (color['position'] - min_pos) / (max_pos - min_pos)

        colormaps[name] = {
            'colors': colors,
            'nan_color': tuple(colormap.get('NanColor', (1, 1, 1))),
            'color_space': colormap.get('ColorSpace', 'RGB'),
        }
    return colormaps


PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
colors_filepath = os.path.join(PACKAGE_DIR, 'colors.json')
COLORMAPS = load_colormaps_from_json(colors_filepath)


def get_colormap_items(self, context):
    """Return Blender enum items for available colormaps including a custom option if present."""
    items = [(name, name, "") for name in COLORMAPS.keys()]
    if getattr(getattr(context, 'scene', None), 'custom_colorramp', None):
        items.append(("CUSTOM", "Custom", "Use custom ColorRamp"))
    return items


def interpolate_colormap(colors, num_points=32):
    """Resample a color map to an even grid of stops using linear interpolation.

    Parameters
    ----------
    colors : list[dict]
        Items with keys 'position' in [0, 1] and 'color' as an RGB tuple.
    num_points : int
        Number of evenly spaced samples to generate in [0, 1].

    Returns
    -------
    list[dict]
        Resampled colors with positions in [0, 1] and RGB tuples.
    """
    positions = [color['position'] for color in colors]
    rgb_colors = [color['color'] for color in colors]

    if positions[0] != 0:
        positions.insert(0, 0)
        rgb_colors.insert(0, rgb_colors[0])
    if positions[-1] != 1:
        positions.append(1)
        rgb_colors.append(rgb_colors[-1])

    paired = sorted(zip(positions, rgb_colors), key=lambda x: x[0])
    positions_sorted = [p for p, _ in paired]
    r_values = [c[0] for _, c in paired]
    g_values = [c[1] for _, c in paired]
    b_values = [c[2] for _, c in paired]

    new_positions = np.linspace(0.0, 1.0, num_points)
    r_interp = np.interp(new_positions, positions_sorted, r_values)
    g_interp = np.interp(new_positions, positions_sorted, g_values)
    b_interp = np.interp(new_positions, positions_sorted, b_values)

    new_colors = []
    for idx, pos in enumerate(new_positions):
        new_colors.append({'position': float(pos), 'color': (float(r_interp[idx]), float(g_interp[idx]), float(b_interp[idx]))})

    return new_colors 