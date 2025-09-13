import numpy as np
from io import BytesIO
import os


def generate_shape(shape_type, **kwargs):
    """Generate a shape image using matplotlib and PIL.

    Imports heavy dependencies lazily to avoid failing at add-on load if they
    are missing. The caller should handle None if generation fails.
    """
    try:
        from PIL import Image
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyArrowPatch, Ellipse, RegularPolygon, Rectangle
        from matplotlib.transforms import Affine2D
        import matplotlib.font_manager as fm
    except Exception as e:
        print(f"Error: Required dependencies for shape generation are missing: {e}")
        return None

    dimension_x = int(kwargs.get('dimension_x', 100))
    dimension_y = int(kwargs.get('dimension_y', 100))
    
    fig, ax = plt.subplots(figsize=(dimension_x/100, dimension_y/100), dpi=100)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    fill_color = tuple(c for c in kwargs.get('fill_color', (1, 1, 1, 1)))
    line_color = tuple(c for c in kwargs.get('line_color', (0, 0, 0, 1)))
    font_color = tuple(c for c in kwargs.get('font_color', (0, 0, 0, 1)))
    line_size = kwargs.get('line_size', 1)
    rotation = kwargs.get('rotation', 0)

    scale = min(dimension_x, dimension_y) / 100

    if shape_type == 'TEXT':
        text = kwargs.get('text_content', 'Sample Text')
        font_size = kwargs.get('font_size', 12) * scale
        font_path = kwargs.get('font_path', '')
        
        if font_path and os.path.exists(font_path):
            font_prop = fm.FontProperties(fname=font_path)
        else:
            font_prop = fm.FontProperties()
        
        ax.text(50, 50, text, fontproperties=font_prop, fontsize=font_size, 
                color=font_color, ha='center', va='center')

    elif shape_type == 'LATEX':
        latex = kwargs.get('latex_formula', r'$E = mc^2$')
        font_size = kwargs.get('font_size', 12) * scale
        # Use Matplotlib mathtext to avoid external LaTeX dependency
        if not (isinstance(latex, str) and latex.startswith('$') and latex.endswith('$')):
            latex = f'${latex}$'
        plt.rcParams['text.usetex'] = False
        ax.text(50, 50, latex, color=font_color, ha='center', va='center', fontsize=font_size)

    elif shape_type == 'CUSTOM':
        custom_shape_path = kwargs.get('custom_shape_path', '')
        if custom_shape_path and os.path.exists(custom_shape_path):
            try:
                from PIL import Image
            except Exception:
                print("Error: PIL is required for custom shape images.")
                return None
            custom_image = Image.open(custom_shape_path).convert("RGBA")
            custom_image = custom_image.resize((dimension_x, dimension_y))
            
            fill_color = kwargs.get('fill_color', (1, 1, 1, 1))
            fill_color = tuple(int(c * 255) for c in fill_color) 
            if custom_image and custom_image.size:
                from PIL import Image as _PILImage
                fill_image = _PILImage.new('RGBA', custom_image.size, fill_color)
                
                r, g, b, a = custom_image.split()
                filled_rgb = _PILImage.composite(custom_image, fill_image, a)
                
                custom_image = _PILImage.merge('RGBA', (*filled_rgb.split()[:3], a))
            else:
                print("Error: Custom image did not load correctly")
                return None
            
            fig, ax = plt.subplots(figsize=(dimension_x/100, dimension_y/100), dpi=100)
            ax.imshow(custom_image)
            ax.axis('off')
            fig.patch.set_alpha(0)
            
            fig.canvas.draw()
            w, h = fig.canvas.get_width_height()
            buf = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
            buf.shape = (w, h, 4)
            buf = np.roll(buf, 3, axis=2)
            image = Image.frombytes("RGBA", (w, h), buf.tobytes())
            plt.close(fig)
            return image
        else:
            print(f"Error: Could not find or open custom shape file: {custom_shape_path}")
            return None

    else:
        if shape_type == 'ARROW':
            arrow = plt.Arrow(0, 50, kwargs['arrow_length'] * scale, 0,
                              width=kwargs['arrow_width'] * scale,
                              facecolor=fill_color, edgecolor=line_color, linewidth=line_size)
            ax.add_patch(arrow)
        elif shape_type == 'CIRCLE':
            circle = plt.Circle((50, 50), kwargs['circle_radius'] * scale,
                                facecolor=fill_color, edgecolor=line_color, linewidth=line_size)
            ax.add_patch(circle)
        elif shape_type == 'RECTANGLE':
            width = kwargs['rectangle_width'] * scale
            height = kwargs['rectangle_height'] * scale
            rectangle = Rectangle((50 - width/2, 50 - height/2), width, height,
                                  facecolor=fill_color, edgecolor=line_color, linewidth=line_size)
            ax.add_patch(rectangle)
        elif shape_type == 'FANCY_ARROW':
            arrow = FancyArrowPatch((0, 50), (kwargs['arrow_length'] * scale, 50),
                                    arrowstyle='fancy', mutation_scale=kwargs['arrow_width'] * scale,
                                    facecolor=fill_color, edgecolor=line_color, linewidth=line_size)
            ax.add_patch(arrow)
        elif shape_type == 'ELLIPSE':
            ellipse = Ellipse((50, 50), kwargs['ellipse_width'] * scale, kwargs['ellipse_height'] * scale,
                              facecolor=fill_color, edgecolor=line_color, linewidth=line_size)
            ax.add_patch(ellipse)
        elif shape_type == 'STAR':
            star = RegularPolygon((50, 50), kwargs['star_points'], kwargs['star_outer_radius'] * scale,
                                  facecolor=fill_color, edgecolor=line_color, linewidth=line_size)
            ax.add_patch(star)
            inner_star = RegularPolygon((50, 50), kwargs['star_points'], kwargs['star_inner_radius'] * scale,
                                        facecolor='white', edgecolor=None)
            inner_star.set_transform(inner_star.get_transform() + Affine2D().rotate_deg(180/kwargs['star_points']))
            ax.add_patch(inner_star)

    for artist in ax.get_children():
        if isinstance(artist, (plt.Text, plt.Line2D, plt.Polygon)):
            artist.set_transform(artist.get_transform() + Affine2D().rotate_deg_around(50, 50, rotation))

    fig.canvas.draw()
    
    w, h = fig.canvas.get_width_height()
    buf = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
    buf.shape = (w, h, 4)
    
    buf = np.roll(buf, 3, axis=2)
    
    image = Image.frombytes("RGBA", (w, h), buf.tobytes())
    plt.close(fig)

    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    return image