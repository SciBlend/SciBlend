import bpy


def update_legend_position_in_compositor(context):
    scene = context.scene
    settings = scene.legend_settings
    tree = scene.node_tree
    
    if tree is None:
        return

    translate_node = None
    for node in tree.nodes:
        if node.type == 'TRANSLATE':
            translate_node = node
            break

    if translate_node is None:
        return

    render_size_x = scene.render.resolution_x
    render_size_y = scene.render.resolution_y
    
    translate_node.inputs[1].default_value = settings.legend_position_x * render_size_x / 100
    translate_node.inputs[2].default_value = settings.legend_position_y * render_size_y / 100


def update_legend_scale_in_compositor(context):
    scene = context.scene
    settings = scene.legend_settings
    tree = scene.node_tree
    
    if tree is None:
        return

    scale_size_node = None
    scale_legend_node = None
    for node in tree.nodes:
        if node.type == 'SCALE':
            if node.space == 'RELATIVE':
                scale_legend_node = node
            else:
                scale_size_node = node

    if scale_size_node is None or scale_legend_node is None:
        return

    if scale_size_node.space != 'RENDER_SIZE':
        scale_size_node.space = 'RENDER_SIZE'
    scale_size_node.frame_method = 'FIT'

    scale_x = settings.legend_scale_x
    scale_y = settings.legend_scale_y if not settings.legend_scale_linked else settings.legend_scale_x
    scale_legend_node.inputs[1].default_value = scale_x
    scale_legend_node.inputs[2].default_value = scale_y

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
    tree = scene.node_tree

    if not tree:
        if visible:
            try:
                bpy.ops.compositor.png_overlay()
            except Exception:
                return
        return

    image_node = None
    alpha_over_node = None
    for node in tree.nodes:
        if node.type == 'IMAGE':
            image_node = node
        elif node.type == 'ALPHAOVER':
            alpha_over_node = node

    if visible and (not image_node or not alpha_over_node):
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