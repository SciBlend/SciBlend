import bpy
import tempfile
import os
import numpy as np  
from bpy.props import IntProperty
from bpy.types import Operator
from ..utils.gradient_bar import create_gradient_bar
from ..utils.compositor_utils import update_legend_position_in_compositor, update_legend_scale_in_compositor
from ..utils.color_utils import load_colormaps, interpolate_color

class PNGOverlayOperator(Operator):
    bl_idname = "compositor.png_overlay"
    bl_label = "PNG Overlay Compositor"

    resolution: IntProperty(name="Resolution", default=1920)

    def execute(self, context):
        scene = context.scene
        settings = scene.legend_settings
        
        if settings.colormap == 'CUSTOM':
            colors_values = settings.colors_values
            if not colors_values:
                color_nodes = [
                    (0.0, (0, 0, 0)),  
                    (1.0, (1, 1, 1)) 
                ]
                labels = ["0.00", "1.00"]
            else:
                color_nodes = []
                labels = []
                for i, item in enumerate(colors_values):
                    color_nodes.append((i / (len(colors_values) - 1), item.color[:3]))
                    labels.append(item.value)
        else:
            colormaps = load_colormaps()
            selected_colormap = colormaps.get(settings.colormap, [])
            
            start = settings.colormap_start
            end = settings.colormap_end
            subdivisions = settings.colormap_subdivisions
            
            positions = np.linspace(0, 1, subdivisions)
            values = np.linspace(start, end, subdivisions)
            
            color_nodes = []
            labels = []
            for pos, value in zip(positions, values):
                color = interpolate_color(selected_colormap, pos)
                color_nodes.append((pos, color))
                labels.append(f"{value:.2f}")

        if not color_nodes:
            self.report({'ERROR'}, "No color nodes available")
            return {'CANCELLED'}

        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                tmpname = tmpfile.name
                font_type = settings.legend_font_type
                font_path = settings.legend_system_font if font_type == 'SYSTEM' else settings.legend_font
                create_gradient_bar(settings.legend_width, settings.legend_height, color_nodes,
                                    labels, tmpname, settings.legend_name, 
                                    settings.interpolation, settings.legend_orientation,
                                    font_type, font_path,
                                    settings.legend_text_color,
                                    settings.legend_text_size_pt)  
            scene.use_nodes = True
            tree = scene.node_tree

            tree.nodes.clear()

            render_layers = tree.nodes.new('CompositorNodeRLayers')
            composite = tree.nodes.new('CompositorNodeComposite')
            alpha_over = tree.nodes.new('CompositorNodeAlphaOver')
            image_node = tree.nodes.new('CompositorNodeImage')
            scale_size_node = tree.nodes.new('CompositorNodeScale')
            scale_legend_node = tree.nodes.new('CompositorNodeScale')
            translate_node = tree.nodes.new('CompositorNodeTranslate')

            try:
                image_node.image = bpy.data.images.load(tmpname)
            except Exception:
                self.report({'ERROR'}, "Cannot load image")
                return {'CANCELLED'}

            scale_size_node.space = 'RENDER_SIZE'
            scale_size_node.inputs[1].default_value = 1.0
            scale_size_node.inputs[2].default_value = 1.0

            scale_legend_node.space = 'RELATIVE'
            scale_legend_node.inputs[1].default_value = settings.legend_scale_x
            scale_legend_node.inputs[2].default_value = settings.legend_scale_y

            render_layers.location = (0, 0)
            image_node.location = (0, 200)
            translate_node.location = (100, 200)
            scale_size_node.location = (300, 200)
            scale_legend_node.location = (500, 200)
            alpha_over.location = (800, 0)
            composite.location = (1000, 0)

            tree.links.new(render_layers.outputs["Image"], alpha_over.inputs[1])
            tree.links.new(image_node.outputs["Image"], translate_node.inputs["Image"])
            tree.links.new(translate_node.outputs["Image"], scale_size_node.inputs["Image"])
            tree.links.new(scale_size_node.outputs["Image"], scale_legend_node.inputs["Image"])
            tree.links.new(scale_legend_node.outputs["Image"], alpha_over.inputs[2])
            tree.links.new(alpha_over.outputs["Image"], composite.inputs["Image"])

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

            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error generating the legend: {str(e)}")
            return {'CANCELLED'}