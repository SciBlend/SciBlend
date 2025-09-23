import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib import font_manager
from PIL import Image


def create_gradient_bar(width, height, color_nodes, labels, filename, legend_name, interpolation, orientation, font_type, font_path, text_color, text_size_pt, label_padding, label_offset_pct):
    """Create and save a colorbar image.

    Parameters:
    - width, height: Pixel dimensions of the generated image.
    - color_nodes: List of (position, (r,g,b)) tuples in range [0,1].
    - labels: Tick labels to display along the colorbar range.
    - filename: Output PNG path.
    - legend_name: Label text for the colorbar.
    - interpolation: One of LINEAR, STEP, CUBIC, NEAREST.
    - orientation: 'HORIZONTAL' or 'VERTICAL'.
    - font_type: 'SYSTEM' or 'CUSTOM'.
    - font_path: Font family name (SYSTEM) or file path (CUSTOM).
    - text_color: RGBA/ RGB color, values in [0,1].
    - text_size_pt: Label and ticks size in points.
    - label_padding: Space between colorbar and label, in points.
    - label_offset_pct: Position of the label along axis [0..100].
    """
    if orientation == 'HORIZONTAL':
        figsize = (width/100, height/100)
        orientation = 'horizontal'
        aspect = 20
    else:
        figsize = (height/100, width/100)
        orientation = 'vertical'
        aspect = 20 * (width / height)

    original_rc = plt.rcParams.copy()

    font_prop = None
    if font_type == 'CUSTOM' and font_path and os.path.exists(font_path):
        try:
            font_manager.fontManager.addfont(font_path)
            font_prop = font_manager.FontProperties(fname=font_path)
            font_name = font_prop.get_name()
            plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
        except Exception:
            font_prop = None
    elif font_type == 'SYSTEM' and font_path:
        try:
            font_prop = font_manager.FontProperties(family=font_path)
            plt.rcParams['font.family'] = font_path
        except Exception:
            font_prop = None

    fig = None
    try:
        fig, ax = plt.subplots(figsize=figsize, dpi=100)
        ax.axis('off')

        positions = [pos for pos, _ in color_nodes]
        colors = [color for _, color in color_nodes]

        if interpolation == 'LINEAR':
            cmap = mcolors.LinearSegmentedColormap.from_list('custom_cmap', list(zip(positions, colors)), N=256)
        elif interpolation == 'STEP':
            cmap = mcolors.ListedColormap(colors)
            bounds = np.linspace(0, 1, len(colors) + 1)
            norm = mcolors.BoundaryNorm(bounds, cmap.N)
        elif interpolation == 'CUBIC':
            cmap = mcolors.LinearSegmentedColormap.from_list('custom_cmap', list(zip(positions, colors)), N=256)
        elif interpolation == 'NEAREST':
            cmap = mcolors.LinearSegmentedColormap.from_list('custom_cmap', list(zip(positions, colors)), N=256)
        else:
            cmap = mcolors.LinearSegmentedColormap.from_list('custom_cmap', list(zip(positions, colors)), N=256)

        norm = mcolors.Normalize(vmin=0, vmax=100)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, orientation=orientation, pad=0.1, aspect=aspect, fraction=0.05)

        text_color_rgb = text_color[:3]

        if font_prop:
            try:
                font_prop.set_size(text_size_pt)
            except Exception:
                pass
            cbar.set_label(legend_name, color=text_color_rgb, fontproperties=font_prop, labelpad=label_padding)
            ticklabels = cbar.ax.get_xticklabels() if orientation == 'horizontal' else cbar.ax.get_yticklabels()
            for label in ticklabels:
                label.set_fontproperties(font_prop)
                label.set_color(text_color_rgb)
        else:
            cbar.set_label(legend_name, color=text_color_rgb, labelpad=label_padding)
            label_obj = cbar.ax.xaxis.label if orientation == 'horizontal' else cbar.ax.yaxis.label
            try:
                label_obj.set_fontsize(text_size_pt)
            except Exception:
                pass
            ticklabels = cbar.ax.get_xticklabels() if orientation == 'horizontal' else cbar.ax.get_yticklabels()
            for label in ticklabels:
                try:
                    label.set_fontsize(text_size_pt)
                except Exception:
                    pass
                label.set_color(text_color_rgb)

        pos_frac = max(0.0, min(1.0, (label_offset_pct or 0.0) / 100.0))
        if orientation == 'horizontal':
            cbar.ax.xaxis.label.set_ha('center')
            cbar.ax.xaxis.label.set_x(pos_frac)
        else:
            cbar.ax.yaxis.label.set_va('center')
            cbar.ax.yaxis.label.set_y(pos_frac)

        cbar.set_ticks(np.linspace(0, 100, len(labels)))
        cbar.set_ticklabels(labels)
        cbar.ax.tick_params(colors=text_color_rgb)

        plt.savefig(filename, format='png', bbox_inches='tight', transparent=True, dpi=100)
    finally:
        if fig is not None:
            plt.close(fig)
        plt.rcParams.update(original_rc)


def create_multi_legends_png(width, height, legends, filename, orientation):
    """Compose multiple legends into a single PNG using matplotlib subplots.

    Parameters
    ----------
    - width, height: output canvas size in pixels
    - legends: list of dicts, each with keys matching create_gradient_bar parameters except filename
    - filename: output image path
    - orientation: 'HORIZONTAL' or 'VERTICAL' indicating layout direction for stacking
    """
    fig = None
    try:
        rows = len(legends) if orientation == 'VERTICAL' else 1
        cols = 1 if orientation == 'VERTICAL' else len(legends)
        figsize = (width/100, height/100)
        fig, axes = plt.subplots(rows, cols, figsize=figsize, dpi=100)
        if not isinstance(axes, (list, np.ndarray)):
            axes = [axes]
        axes = np.atleast_1d(axes).flatten().tolist()
        for ax in axes:
            ax.axis('off')
        for idx, leg in enumerate(legends):
            tmp = filename + f"._tmp_{idx}.png"
            create_gradient_bar(
                width, height,
                leg['color_nodes'], leg['labels'], tmp, leg['legend_name'],
                leg['interpolation'], leg['orientation'], leg['font_type'], leg['font_path'],
                leg['text_color'], leg['text_size_pt'], leg['label_padding'], leg['label_offset_pct']
            )
            img = Image.open(tmp).convert('RGBA')
            axes[idx].imshow(img)
            try:
                os.remove(tmp)
            except Exception:
                pass
        plt.subplots_adjust(wspace=0.02, hspace=0.02)
        plt.savefig(filename, format='png', bbox_inches='tight', transparent=True, dpi=100)
    finally:
        if fig is not None:
            plt.close(fig)