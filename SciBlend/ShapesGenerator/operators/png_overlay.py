import bpy
import numpy as np
from bpy.types import Operator
from ..utils.shape_generator import generate_shape
import os
import tempfile
import uuid
import re
from ..utils.group_utils import create_or_update_shape_group


def _build_unique_png_path(base_name: str, context: bpy.types.Context | None = None) -> str:
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
                    return pref.build_unique_png_path(base_name, context)
            except Exception:
                continue
    except Exception:
        pass
    directory = getattr(bpy.app, "tempdir", None) or tempfile.gettempdir()
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", str(base_name) or "shape")
    unique = uuid.uuid4().hex
    return os.path.join(directory, f"sciblend_{safe}_{unique}.png")


def _sanitize_filename_component(name):
    """Return a filesystem-safe component derived from name."""
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", str(name))
    return safe or "shape"


def _get_unique_temp_png_path(base_name):
    """Build a unique, writable temporary PNG file path for the given base name."""
    return _build_unique_png_path(base_name)


def _remove_blender_image_and_file(image):
    """Remove the Blender image datablock and delete its underlying file if present."""
    if not image:
        return
    path = None
    try:
        path = bpy.path.abspath(getattr(image, "filepath", ""))
    except Exception:
        path = None
    try:
        bpy.data.images.remove(image)
    except Exception:
        pass
    if path and os.path.isfile(path):
        try:
            os.remove(path)
        except Exception:
            pass

class SHAPESGENERATOR_OT_UpdateShapes(Operator):
    bl_idname = "shapesgenerator.update_shapes"
    bl_label = "Update Shapes"

    def execute(self, context):
        scene = context.scene
        print("Starting SHAPESGENERATOR_OT_UpdateShapes")
        
        if not scene.use_nodes:
            scene.use_nodes = True
        tree = scene.node_tree
        print(f"Node tree obtained: {tree}")

        composite = tree.nodes.get("Composite")
        if not composite:
            composite = tree.nodes.new(type='CompositorNodeComposite')
        print(f"Composite Node: {composite}")

        legend_alpha_over = tree.nodes.get("Alpha Over")

        render_layers = tree.nodes.get("Render Layers")
        if not render_layers:
            render_layers = tree.nodes.new(type='CompositorNodeRLayers')
        
        spacing_x = 250
        base_x = composite.location.x - 3 * spacing_x
        row_y = composite.location.y

        render_layers.location = (base_x, row_y)

        if legend_alpha_over:
            target_socket = legend_alpha_over.inputs[1]
            if target_socket.links:
                tree.links.remove(target_socket.links[0])
        else:
            target_socket = composite.inputs['Image']
            if target_socket.links:
                tree.links.remove(target_socket.links[0])

        for node in [n for n in tree.nodes if n.name.startswith("ShapesGenerator_AlphaOver_") or n.name.startswith("ShapesGenerator_Group_")]:
            tree.nodes.remove(node)

        for node in [n for n in tree.nodes if n.type == 'REROUTE']:
            for out in node.outputs:
                for link in list(out.links):
                    if link.to_socket == target_socket:
                        tree.links.remove(link)
                        try:
                            tree.nodes.remove(node)
                        except Exception:
                            pass

        shapes = scene.shapesgenerator_shapes
        group_nodes = []

        for i, shape in enumerate(shapes):
            print(f"Processing shape {i+1}: {shape.name}, Type: {shape.shape_type}")

            extra_kwargs = {}
            if shape.shape_type == 'GRAPH':
                try:
                    from ..utils.mesh_attributes import read_float_attribute
                except Exception as e:
                    print(f"Error importing mesh attribute utils: {e}")
                    extra_kwargs = {}
                else:
                    source_obj = shape.graph_object or context.active_object
                    arr_a = read_float_attribute(source_obj, shape.graph_attribute) if source_obj and shape.graph_attribute else np.asarray([], dtype=float)
                    arr_b = read_float_attribute(source_obj, shape.graph_attribute_b) if source_obj and shape.graph_attribute_b else np.asarray([], dtype=float)
                    labels = None
                    if arr_b.size > 0:
                        labels = [shape.graph_attribute or "A", shape.graph_attribute_b or "B"]
                    extra_kwargs = {
                        'graph_type': shape.graph_type,
                        'graph_values_a': arr_a,
                        'graph_values_b': arr_b,
                        'graph_labels': labels,
                        'graph_bins': shape.graph_bins,
                        'graph_title': shape.graph_title,
                        'graph_xlabel': shape.graph_xlabel,
                        'graph_ylabel': shape.graph_ylabel,
                        'graph_color': tuple(shape.graph_color),
                        'graph_edgecolor': tuple(shape.graph_edgecolor),
                        'graph_grid': bool(shape.graph_grid),
                        'graph_font_size': int(shape.graph_font_size),
                        'graph_font_color': tuple(shape.graph_font_color),
                    }

            image = generate_shape(shape.shape_type, **{
                'dimension_x': shape.dimension_x,
                'dimension_y': shape.dimension_y,
                'arrow_length': shape.arrow_length,
                'arrow_width': shape.arrow_width,
                'circle_radius': shape.circle_radius,
                'rectangle_width': shape.rectangle_width,
                'rectangle_height': shape.rectangle_height,
                'ellipse_width': shape.ellipse_width,
                'ellipse_height': shape.ellipse_height,
                'star_outer_radius': shape.star_outer_radius,
                'star_inner_radius': shape.star_inner_radius,
                'star_points': shape.star_points,
                'fill_color': (*shape.fill_color[:3], shape.fill_alpha),
                'line_color': (*shape.line_color[:3], shape.line_alpha),
                'line_width': shape.line_width,
                'rotation': shape.rotation,
                'text_content': shape.text_content,
                'font_size': shape.font_size,
                'font_path': shape.font_path,
                'latex_formula': shape.latex_formula,
                'font_color': (*shape.font_color[:3], shape.font_color[3]),
                'line_size': shape.line_size,
                'custom_shape_path': shape.custom_shape_path,
                'scale_x': shape.scale_x,
                'scale_y': shape.scale_y,
                **extra_kwargs,
            })
            if image is None:
                print(f"Error: No image generated for shape {shape.name}")
                continue

            temp_path = _get_unique_temp_png_path(shape.name)
            image.save(temp_path, format='PNG')

            group_name = f"ShapesGroup_{i}"
            nodegroup = create_or_update_shape_group(group_name, temp_path)

            group_node = tree.nodes.new('CompositorNodeGroup')
            group_node.name = f"ShapesGenerator_Group_{i}"
            group_node.node_tree = nodegroup

            group_node.inputs["Translate X"].default_value = shape.position_x * 1000
            group_node.inputs["Translate Y"].default_value = shape.position_y * 1000
            group_node.inputs["Angle"].default_value = shape.rotation
            group_node.inputs["Scale Size X"].default_value = shape.dimension_x / scene.render.resolution_x
            group_node.inputs["Scale Size Y"].default_value = shape.dimension_y / scene.render.resolution_y
            group_node.inputs["Scale X"].default_value = shape.scale_x
            group_node.inputs["Scale Y"].default_value = shape.scale_y

            group_node.location = (base_x + (i + 1) * spacing_x, row_y)
            group_nodes.append(group_node)

        if len(group_nodes) == 0:
            pass
        else:
            base_socket = render_layers.outputs['Image']
            ao_nodes = []
            for i, g in enumerate(group_nodes):
                ao = tree.nodes.new(type='CompositorNodeAlphaOver')
                ao.name = f"ShapesGenerator_AlphaOver_{i}"
                ao.inputs[0].default_value = 1.0
                ao.location = (base_x + (i + 1.5) * spacing_x, row_y)
                tree.links.new(base_socket, ao.inputs[1])
                tree.links.new(g.outputs['Image'], ao.inputs[2])
                base_socket = ao.outputs[0]
                ao_nodes.append(ao)

            tree.links.new(base_socket, target_socket)

        self.force_update(context)

        print("SHAPESGENERATOR_OT_UpdateShapes completed")
        return {'FINISHED'}

    def force_update(self, context):
        context.view_layer.update()

        for area in context.screen.areas:
            area.tag_redraw()

        context.scene.update_tag()

        if context.scene.node_tree:
            context.scene.node_tree.update_tag()

        current_frame = context.scene.frame_current
        context.scene.frame_set(current_frame)

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces[0]
                current_shading = space.shading.type
                
                space.shading.type = 'SOLID'
                context.view_layer.update()
                
                space.shading.type = current_shading
                context.view_layer.update()

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()

        depsgraph = context.evaluated_depsgraph_get()
        depsgraph.update()

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            context.view_layer.update()
                            region.tag_redraw()

        for node in context.scene.node_tree.nodes:
            node.update()

class SHAPESGENERATOR_OT_NewShape(Operator):
    bl_idname = "shapesgenerator.new_shape"
    bl_label = "New Shape"

    def execute(self, context):
        new_shape = context.scene.shapesgenerator_shapes.add()
        new_shape.name = f"Shape {len(context.scene.shapesgenerator_shapes)}"
        new_shape.position_x = 0  
        new_shape.position_y = 0  
        context.scene.shapesgenerator_active_shape_index = len(context.scene.shapesgenerator_shapes) - 1
        return {'FINISHED'}

class SHAPESGENERATOR_OT_DeleteShape(Operator):
    bl_idname = "shapesgenerator.delete_shape"
    bl_label = "Delete Shape"

    def execute(self, context):
        shapes = context.scene.shapesgenerator_shapes
        index = context.scene.shapesgenerator_active_shape_index

        if index >= 0 and index < len(shapes):
            shapes.remove(index)
            context.scene.shapesgenerator_active_shape_index = min(max(0, index - 1), len(shapes) - 1)

        return {'FINISHED'}
