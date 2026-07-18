import bpy

from ...compat import (
    get_scene_compositor_tree,
    set_compositor_scale,
    get_compositor_scale_mode,
    set_translate_node,
)


def update_legend_position_in_compositor(context):
    scene = context.scene
    settings = scene.legend_settings
    tree = get_scene_compositor_tree(scene)
    
    if tree is None:
        return

    group_node = None
    for node in tree.nodes:
        if node.type == 'GROUP' and getattr(node, 'node_tree', None) and getattr(node.node_tree, 'name', '') == 'SciBlend_LegendGroup':
            group_node = node
            break

    render_size_x = scene.render.resolution_x
    render_size_y = scene.render.resolution_y
    tx = settings.legend_position_x * render_size_x / 100
    ty = settings.legend_position_y * render_size_y / 100

    if group_node:
        if "Translate X" in group_node.inputs:
            group_node.inputs["Translate X"].default_value = tx
        if "Translate Y" in group_node.inputs:
            group_node.inputs["Translate Y"].default_value = ty
        return

    translate_node = None
    for node in tree.nodes:
        if node.type == 'TRANSLATE':
            translate_node = node
            break

    if translate_node is None:
        return

    set_translate_node(translate_node, x=tx, y=ty)


def update_legend_scale_in_compositor(context):
    scene = context.scene
    settings = scene.legend_settings
    tree = get_scene_compositor_tree(scene)
    
    if tree is None:
        return

    group_node = None
    for node in tree.nodes:
        if node.type == 'GROUP' and getattr(node, 'node_tree', None) and getattr(node.node_tree, 'name', '') == 'SciBlend_LegendGroup':
            group_node = node
            break

    scale_x = settings.legend_scale_x
    scale_y = settings.legend_scale_y if not settings.legend_scale_linked else settings.legend_scale_x

    if group_node:
        if "Scale X" in group_node.inputs:
            group_node.inputs["Scale X"].default_value = scale_x
        if "Scale Y" in group_node.inputs:
            group_node.inputs["Scale Y"].default_value = scale_y
        bpy.context.view_layer.update()
        for node in tree.nodes:
            if hasattr(node, 'update'):
                node.update()
        for area in bpy.context.screen.areas:
            area.tag_redraw()
        return

    scale_size_node = None
    scale_legend_node = None
    for node in tree.nodes:
        if node.type == 'SCALE':
            if get_compositor_scale_mode(node) == 'Relative':
                scale_legend_node = node
            else:
                scale_size_node = node

    if scale_size_node is None or scale_legend_node is None:
        return

    set_compositor_scale(scale_size_node, mode='Render Size', frame_method='Fit')
    set_compositor_scale(scale_legend_node, x=scale_x, y=scale_y)

    bpy.context.view_layer.update()

    for node in tree.nodes:
        if hasattr(node, 'update'):
            node.update()

    for area in bpy.context.screen.areas:
        area.tag_redraw()


def update_legend_scale_mode(context):
    update_legend_scale_in_compositor(context)


def set_legend_visibility(context, visible: bool):
    """Show or hide the legend overlay in the compositor.

    - If enabling and the overlay nodes are missing, generate the overlay first.
    - If nodes exist, toggle the Alpha Over node mute state to hide/show the overlay.
    """
    scene = context.scene
    tree = get_scene_compositor_tree(scene)

    if not tree:
        if visible:
            try:
                bpy.ops.compositor.png_overlay()
            except Exception:
                return
        return

    image_output_present = False
    alpha_over_node = None
    for node in tree.nodes:
        if node.type == 'GROUP' and getattr(node, 'node_tree', None) and getattr(node.node_tree, 'name', '') == 'SciBlend_LegendGroup':
            image_output_present = True
        elif node.type == 'IMAGE':
            image_output_present = True
        elif node.type == 'ALPHAOVER':
            alpha_over_node = node

    if visible and (not image_output_present or not alpha_over_node):
        try:
            bpy.ops.compositor.png_overlay()
        except Exception:
            return
        return

    if not alpha_over_node:
        return

    try:
        alpha_over_node.mute = not visible
    except Exception:
        pass

    for area in bpy.context.screen.areas:
        area.tag_redraw()