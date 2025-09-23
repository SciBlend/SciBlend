import bpy
import tempfile
import os
import numpy as np  
from bpy.props import IntProperty
from bpy.types import Operator
# from ..utils.gradient_bar import create_gradient_bar
from ..utils.compositor_utils import update_legend_position_in_compositor, update_legend_scale_in_compositor
from ..utils.color_utils import load_colormaps, interpolate_color
from ..utils.group_utils import create_or_update_legend_group

_running_overlay = False


def _build_unique_png_path(name: str, context: bpy.types.Context) -> str:
    """Resolve a unique PNG path using add-on preferences if available, else tempdir."""
    try:
        from importlib import import_module
        for mod in (
            "..ui.pref",
            "...ui.pref",
            "....ui.pref",
        ):
            try:
                pref = import_module(mod, package=__package__)
                if hasattr(pref, "build_unique_png_path"):
                    return pref.build_unique_png_path(name, context)
            except Exception:
                continue
    except Exception:
        pass
    directory = getattr(bpy.app, "tempdir", None) or tempfile.gettempdir()
    safe = "".join(c if c.isalnum() or c in ".-_" else "_" for c in str(name) or "legend")
    import uuid
    return os.path.join(directory, f"{safe}_{uuid.uuid4().hex}.png")


def _format_number(value: float, decimals: int, mode: str) -> str:
    """Format a numeric value according to decimals and format mode."""
    try:
        if mode == 'FIXED':
            return f"{value:.{decimals}f}"
        if mode == 'SCIENTIFIC_E':
            return f"{value:.{decimals}e}"
        if mode == 'GENERAL':
            return f"{value:.{decimals}g}"
        if mode == 'SCIENTIFIC_TEX':
            s = f"{value:.{decimals}e}"
            mantissa, exp = s.split('e')
            exp_i = int(exp)
            return rf"${mantissa}\times10^{{{exp_i}}}$"
        return f"{value:.{decimals}f}"
    except Exception:
        return str(value)


class PNGOverlayOperator(Operator):
    bl_idname = "compositor.png_overlay"
    bl_label = "PNG Overlay Compositor"

    resolution: IntProperty(name="Resolution", default=1920)

    def execute(self, context):
        from ..utils.gradient_bar import create_gradient_bar, create_multi_legends_png
        global _running_overlay
        if _running_overlay:
            return {'CANCELLED'}
        _running_overlay = True
        scene = context.scene
        settings = scene.legend_settings

        if not getattr(settings, 'legend_enabled', True):
            _running_overlay = False
            return {'CANCELLED'}
        
        def build_color_nodes_and_labels():
            """Build color nodes and labels based on current legend settings."""
            if settings.colormap == 'CUSTOM':
                colors_values = settings.colors_values
                if not colors_values:
                    cn = [
                        (0.0, (0, 0, 0)),  
                        (1.0, (1, 1, 1)) 
                    ]
                    labels = ["0.00", "1.00"]
                else:
                    cn = []
                    labels = []
                    for i, item in enumerate(colors_values):
                        cn.append((i / (len(colors_values) - 1), item.color[:3]))
                        labels.append(item.value)
            else:
                colormaps = load_colormaps()
                selected_colormap = colormaps.get(settings.colormap, [])
                start = settings.colormap_start
                end = settings.colormap_end
                subdivisions = settings.colormap_subdivisions
                positions = np.linspace(0, 1, subdivisions)
                values = np.linspace(start, end, subdivisions)
                cn = []
                labels = []
                for pos, value in zip(positions, values):
                    color = interpolate_color(selected_colormap, pos)
                    cn.append((pos, color))
                    labels.append(_format_number(float(value), int(getattr(settings, 'legend_decimal_places', 2)), getattr(settings, 'legend_number_format', 'FIXED')))
            return cn, labels

        def get_collection_attribute_name(coll: bpy.types.Collection) -> str:
            """Return the attribute name used by the collection's shader if detectable; fallback to collection name.

            The function inspects the first mesh object with a node-based material in the collection,
            preferring the material's 'sciblend_attribute' property, then falling back to an Attribute node.
            """
            try:
                for obj in coll.objects:
                    if getattr(obj, 'type', None) != 'MESH':
                        continue
                    mat = getattr(obj, 'active_material', None) or (obj.data.materials[0] if getattr(obj.data, 'materials', None) else None)
                    if not mat or not getattr(mat, 'use_nodes', False) or not getattr(mat, 'node_tree', None):
                        continue
                    try:
                        attr = mat.get("sciblend_attribute", None)
                        if isinstance(attr, str) and attr.strip():
                            return attr.strip()
                    except Exception:
                        pass
                    try:
                        for node in mat.node_tree.nodes:
                            if node.type == 'ATTRIBUTE' and getattr(node, 'attribute_name', None):
                                return node.attribute_name
                    except Exception:
                        pass
            except Exception:
                pass
            return coll.name

        def get_collection_shader_legend(coll: bpy.types.Collection):
            """Extract per-collection legend data: color nodes and min/max range from the collection's shader.

            Returns a tuple (legend_name, color_nodes, start, end). If not found, returns fallbacks.
            """
            legend_name = get_collection_attribute_name(coll)
            color_nodes = None
            start = None
            end = None
            try:
                for obj in coll.objects:
                    if getattr(obj, 'type', None) != 'MESH':
                        continue
                    mat = getattr(obj, 'active_material', None) or (obj.data.materials[0] if getattr(obj.data, 'materials', None) else None)
                    if not mat or not getattr(mat, 'use_nodes', False) or not getattr(mat, 'node_tree', None):
                        continue
                    # Range from Map Range node if flagged
                    try:
                        node_map = None
                        for n in mat.node_tree.nodes:
                            if n.type == 'MAP_RANGE' and (getattr(n, 'label', '') == 'SCIBLEND_MAP_RANGE' or bool(n.get('sciblend_map_range', False))):
                                node_map = n
                                break
                        if node_map and 'From Min' in node_map.inputs and 'From Max' in node_map.inputs:
                            start = float(node_map.inputs['From Min'].default_value)
                            end = float(node_map.inputs['From Max'].default_value)
                    except Exception:
                        pass
                    # Color ramp or colormap
                    try:
                        cmap_prop = mat.get('sciblend_colormap', None)
                    except Exception:
                        cmap_prop = None
                    if isinstance(cmap_prop, str) and cmap_prop.strip().upper() != 'CUSTOM':
                        try:
                            colormaps = load_colormaps()
                            cmap_key = cmap_prop.strip().upper()
                            selected_colormap = colormaps.get(cmap_key, None)
                            if selected_colormap is not None:
                                subs = max(2, int(getattr(settings, 'colormap_subdivisions', 10)))
                                positions = np.linspace(0, 1, subs)
                                sampled = []
                                for p in positions:
                                    col = interpolate_color(selected_colormap, float(p))
                                    sampled.append((float(p), tuple(col)))
                                color_nodes = sampled
                        except Exception:
                            color_nodes = None
                    if color_nodes is None:
                        # Fallback: inspect VALTORGB node elements
                        try:
                            for n in mat.node_tree.nodes:
                                if n.type == 'VALTORGB' and hasattr(n, 'color_ramp'):
                                    elems = list(n.color_ramp.elements)
                                    if len(elems) >= 2:
                                        color_nodes = []
                                        for e in elems:
                                            col = tuple(e.color[:3])
                                            pos = float(getattr(e, 'position', 0.0))
                                            color_nodes.append((pos, col))
                                        color_nodes.sort(key=lambda x: x[0])
                                        break
                        except Exception:
                            color_nodes = None
                    if color_nodes is not None or (start is not None and end is not None):
                        break
            except Exception:
                pass
            if color_nodes is None:
                cn, _ = build_color_nodes_and_labels()
                color_nodes = cn
            if start is None or end is None:
                start = settings.colormap_start
                end = settings.colormap_end
            return legend_name, color_nodes, start, end

        try:
            multi_count = max(1, int(getattr(settings, 'multi_legend_count', 1)))
            tmpname = _build_unique_png_path(getattr(settings, 'legend_name', 'legend'), context)
            font_type = settings.legend_font_type
            font_path = settings.legend_system_font if font_type == 'SYSTEM' else settings.legend_font

            if multi_count > 1:
                legends = []
                collections = [c for c in bpy.data.collections if len(c.objects) > 0]
                for idx, coll in enumerate(collections[:multi_count]):
                    legend_name, cn, start, end = get_collection_shader_legend(coll)
                    subdivisions = settings.colormap_subdivisions
                    positions = np.linspace(0, 1, subdivisions)
                    values = np.linspace(start, end, subdivisions)
                    labels = [_format_number(float(v), int(getattr(settings, 'legend_decimal_places', 2)), getattr(settings, 'legend_number_format', 'FIXED')) for v in values]
                    legends.append({
                        'color_nodes': cn,
                        'labels': labels,
                        'legend_name': legend_name,
                        'interpolation': settings.interpolation,
                        'orientation': settings.legend_orientation,
                        'font_type': font_type,
                        'font_path': font_path,
                        'text_color': settings.legend_text_color,
                        'text_size_pt': settings.legend_text_size_pt,
                        'label_padding': settings.legend_label_padding,
                        'label_offset_pct': settings.legend_label_offset_pct,
                    })
                if legends:
                    create_multi_legends_png(settings.legend_width, settings.legend_height, legends, tmpname, settings.legend_orientation)
                else:
                    color_nodes, labels = build_color_nodes_and_labels()
                    create_gradient_bar(settings.legend_width, settings.legend_height, color_nodes,
                                        labels, tmpname, settings.legend_name, 
                                        settings.interpolation, settings.legend_orientation,
                                        font_type, font_path,
                                        settings.legend_text_color,
                                        settings.legend_text_size_pt,
                                        settings.legend_label_padding,
                                        settings.legend_label_offset_pct)
            else:
                color_nodes, labels = build_color_nodes_and_labels()
                create_gradient_bar(settings.legend_width, settings.legend_height, color_nodes,
                                    labels, tmpname, settings.legend_name, 
                                    settings.interpolation, settings.legend_orientation,
                                    font_type, font_path,
                                    settings.legend_text_color,
                                    settings.legend_text_size_pt,
                                    settings.legend_label_padding,
                                    settings.legend_label_offset_pct)

            scene.use_nodes = True
            tree = scene.node_tree

            nodegroup = create_or_update_legend_group(tmpname)

            tree.nodes.clear()

            render_layers = tree.nodes.new('CompositorNodeRLayers')
            composite = tree.nodes.new('CompositorNodeComposite')
            alpha_over = tree.nodes.new('CompositorNodeAlphaOver')
            group_node = tree.nodes.new('CompositorNodeGroup')
            group_node.node_tree = nodegroup
            group_node.label = "Legend"

            render_layers.location = (0, 0)
            group_node.location = (300, 0)
            alpha_over.location = (600, 0)
            composite.location = (800, 0)

            tree.links.new(render_layers.outputs["Image"], alpha_over.inputs[1])
            tree.links.new(group_node.outputs["Image"], alpha_over.inputs[2])
            tree.links.new(alpha_over.outputs["Image"], composite.inputs["Image"]) 

            render_size_x = scene.render.resolution_x
            render_size_y = scene.render.resolution_y
            tx = settings.legend_position_x * render_size_x / 100
            ty = settings.legend_position_y * render_size_y / 100
            group_node.inputs["Translate X"].default_value = tx
            group_node.inputs["Translate Y"].default_value = ty
            group_node.inputs["Scale X"].default_value = settings.legend_scale_x
            group_node.inputs["Scale Y"].default_value = settings.legend_scale_y if not settings.legend_scale_linked else settings.legend_scale_x

            update_legend_position_in_compositor(context)
            update_legend_scale_in_compositor(context)

            try:
                scene_shading = getattr(scene, 'display', None)
                if scene_shading and hasattr(scene_shading, 'shading'):
                    ss = scene_shading.shading
                    if hasattr(ss, 'type') and ss.type not in {'MATERIAL', 'RENDERED'}:
                        try:
                            ss.type = 'MATERIAL'
                        except Exception:
                            pass
                    if hasattr(ss, 'compositor_mode'):
                        try:
                            ss.compositor_mode = 'ALWAYS'
                        except Exception:
                            pass
                    elif hasattr(ss, 'compositor'):
                        try:
                            ss.compositor = 'ALWAYS'
                        except Exception:
                            pass
                    elif hasattr(ss, 'use_compositor'):
                        try:
                            ss.use_compositor = 'ALWAYS'
                        except Exception:
                            pass

                wm = bpy.context.window_manager
                for window in wm.windows:
                    screen = window.screen
                    for area in screen.areas:
                        if area.type == 'VIEW_3D':
                            for space in area.spaces:
                                if space.type == 'VIEW_3D':
                                    shading = getattr(space, 'shading', None)
                                    if shading:
                                        if hasattr(shading, 'type') and shading.type not in {'MATERIAL', 'RENDERED'}:
                                            try:
                                                shading.type = 'MATERIAL'
                                            except Exception:
                                                pass
                                        if hasattr(shading, 'compositor_mode'):
                                            try:
                                                shading.compositor_mode = 'ALWAYS'
                                            except Exception:
                                                pass
                                        elif hasattr(shading, 'compositor'):
                                            try:
                                                shading.compositor = 'ALWAYS'
                                            except Exception:
                                                pass
                                        elif hasattr(shading, 'use_compositor'):
                                            try:
                                                shading.use_compositor = 'ALWAYS'
                                            except Exception:
                                                pass
                            area.tag_redraw()
            except Exception:
                pass

            _running_overlay = False
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error generating the legend: {str(e)}")
            _running_overlay = False
            return {'CANCELLED'}