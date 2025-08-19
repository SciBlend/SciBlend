import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib import font_manager
from PIL import Image

def create_gradient_bar(width, height, color_nodes, labels, filename, legend_name, interpolation, orientation, font_type, font_path, text_color):
    if orientation == 'HORIZONTAL':
        figsize = (width/100, height/100)
        orientation = 'horizontal'
        aspect = 20
    else: 
        figsize = (height/100, width/100)
        orientation = 'vertical'
        aspect = 20 * (width / height)

    font_prop = None
    if font_type == 'CUSTOM' and font_path and os.path.exists(font_path):
        try:
            font_manager.fontManager.addfont(font_path)
            font_prop = font_manager.FontProperties(fname=font_path)
            font_name = font_prop.get_name()
            plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
            print(f"Custom font loaded successfully: {font_path}")
        except Exception as e:
            print(f"Error loading custom font: {font_path}")
            print(f"Error details: {str(e)}")
            print("Using system font.")
    elif font_type == 'SYSTEM' and font_path:
        try:
            font_prop = font_manager.FontProperties(family=font_path)
            plt.rcParams['font.family'] = font_path
            print(f"System font loaded successfully: {font_path}")
        except Exception as e:
            print(f"Error loading system font: {font_path}")
            print(f"Error details: {str(e)}")
            print("Using default font.")
    else:
        print("No valid font provided. Using default font.")

    fig, ax = plt.subplots(figsize=figsize, dpi=100)
    ax.axis('off')

    positions = [pos for pos, _ in color_nodes]
    colors = [color for _, color in color_nodes]

    if interpolation == 'LINEAR':
        cmap = mcolors.LinearSegmentedColormap.from_list(
            'custom_cmap', list(zip(positions, colors)), N=256)
    elif interpolation == 'STEP':
        cmap = mcolors.ListedColormap(colors)
        bounds = np.linspace(0, 1, len(colors) + 1)
        norm = mcolors.BoundaryNorm(bounds, cmap.N)
    elif interpolation == 'CUBIC':
        cmap = mcolors.LinearSegmentedColormap.from_list(
            'custom_cmap', list(zip(positions, colors)), N=256)
    elif interpolation == 'NEAREST':
        cmap = mcolors.LinearSegmentedColormap.from_list(
            'custom_cmap', list(zip(positions, colors)), N=256)
    else:
        cmap = mcolors.LinearSegmentedColormap.from_list(
            'custom_cmap', list(zip(positions, colors)), N=256)

    norm = mcolors.Normalize(vmin=0, vmax=100)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation=orientation,
                        pad=0.1, aspect=aspect, fraction=0.05)
    
    text_color_rgb = text_color[:3]
    
    if font_prop:
        cbar.set_label(legend_name, color=text_color_rgb, fontproperties=font_prop)
        for label in cbar.ax.get_yticklabels():
            label.set_fontproperties(font_prop)
            label.set_color(text_color_rgb)
    else:
        cbar.set_label(legend_name, color=text_color_rgb)
    
    cbar.set_ticks(np.linspace(0, 100, len(labels)))
    cbar.set_ticklabels(labels)
    cbar.ax.tick_params(colors=text_color_rgb)

    plt.savefig(filename, format='png', bbox_inches='tight', transparent=True, dpi=100)
    plt.close(fig)

    print(f"Font used: {plt.rcParams['font.family']}")