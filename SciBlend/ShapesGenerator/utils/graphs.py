import numpy as np
from typing import Optional, Sequence, Tuple


def _prepare_figure(width_px: int, height_px: int):
    """Create a transparent Matplotlib figure sized in pixels and return (fig, ax)."""
    try:
        from PIL import Image
        import matplotlib.pyplot as plt
    except Exception as e:
        return None, None, f"Missing dependencies: {e}"
    width_px = max(1, int(width_px))
    height_px = max(1, int(height_px))
    dpi = 100
    fig, ax = plt.subplots(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)
    ax.set_facecolor((0, 0, 0, 0))
    fig.patch.set_alpha(0)
    return fig, ax, None


def _finalize_to_image(fig) -> Optional["Image.Image"]:
    """Render the current figure into a PIL RGBA image and close the figure."""
    try:
        from PIL import Image
        import numpy as np
    except Exception:
        return None
    try:
        fig.canvas.draw()
        w, h = fig.canvas.get_width_height()
        buf = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
        buf.shape = (w, h, 4)
        buf = np.roll(buf, 3, axis=2)
        image = Image.frombytes("RGBA", (w, h), buf.tobytes())
        return image
    finally:
        import matplotlib.pyplot as plt
        plt.close(fig)


def render_histogram(values: np.ndarray,
                     width_px: int,
                     height_px: int,
                     bins: int = 30,
                     color: Tuple[float, float, float, float] = (0.2, 0.4, 0.8, 0.8),
                     edgecolor: Tuple[float, float, float, float] = (0, 0, 0, 1),
                     title: str = "",
                     xlabel: str = "",
                     ylabel: str = "Count",
                     grid: bool = True,
                     font_size: int = 12,
                     font_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)) -> Optional["Image.Image"]:
    """Render a histogram and return it as a PIL RGBA image."""
    fig, ax, err = _prepare_figure(width_px, height_px)
    if err or fig is None:
        return None
    clean = values[np.isfinite(values)] if isinstance(values, np.ndarray) else np.asarray(values, dtype=float)
    if clean.size == 0:
        clean = np.asarray([0.0], dtype=float)
    ax.hist(clean, bins=max(1, int(bins)), color=color, edgecolor=edgecolor)
    if title:
        ax.set_title(title, fontsize=font_size, color=font_color)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=font_size, color=font_color)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=font_size, color=font_color)
    ax.tick_params(axis='both', labelsize=font_size, labelcolor=font_color)
    if grid:
        ax.grid(True, alpha=0.3)
    return _finalize_to_image(fig)


def render_boxplot(values_list: Sequence[np.ndarray],
                   width_px: int,
                   height_px: int,
                   labels: Optional[Sequence[str]] = None,
                   facecolor: Tuple[float, float, float, float] = (0.6, 0.6, 0.9, 0.7),
                   edgecolor: Tuple[float, float, float, float] = (0, 0, 0, 1),
                   title: str = "",
                   ylabel: str = "Value",
                   grid: bool = True,
                   font_size: int = 12,
                   font_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)) -> Optional["Image.Image"]:
    """Render a boxplot comparing one or more arrays and return a PIL RGBA image."""
    fig, ax, err = _prepare_figure(width_px, height_px)
    if err or fig is None:
        return None
    prepared = []
    for arr in values_list:
        a = np.asarray(arr, dtype=float)
        a = a[np.isfinite(a)]
        if a.size == 0:
            a = np.asarray([0.0], dtype=float)
        prepared.append(a)
    bp = ax.boxplot(prepared, patch_artist=True, labels=labels)
    for patch in bp['boxes']:
        patch.set(facecolor=facecolor, edgecolor=edgecolor)
    for whisker in bp['whiskers']:
        whisker.set(color=edgecolor)
    for cap in bp['caps']:
        cap.set(color=edgecolor)
    for median in bp['medians']:
        median.set(color=edgecolor)
    if title:
        ax.set_title(title, fontsize=font_size, color=font_color)
    ax.tick_params(axis='both', labelsize=font_size, labelcolor=font_color)
    if labels:
        for label in ax.get_xticklabels():
            label.set_color(font_color)
    for label in ax.get_yticklabels():
        label.set_color(font_color)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=font_size, color=font_color)
    if grid:
        ax.grid(True, alpha=0.3)
    return _finalize_to_image(fig) 