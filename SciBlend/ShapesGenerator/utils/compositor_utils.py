import bpy

from ...compat import get_scene_compositor_tree, set_compositor_scale


def update_legend_position_in_compositor(context):
    scene = context.scene
    settings = scene.legend_settings
    tree = get_scene_compositor_tree(scene)
    
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
    
    translate_node.inputs["X"].default_value = settings.legend_position_x * render_size_x / 10
    translate_node.inputs["Y"].default_value = settings.legend_position_y * render_size_y / 10


def update_legend_scale_in_compositor(context):
    scene = context.scene
    settings = scene.legend_settings
    tree = get_scene_compositor_tree(scene)
    
    if tree is None:
        return

    scale_node = None
    for node in tree.nodes:
        if node.type == 'SCALE':
            scale_node = node
            break

    if scale_node is None:
        return

    mode = 'Relative' if settings.legend_scale_mode == 'SCENE' else 'Render Size'
    if settings.legend_scale_linked:
        scale_value = settings.legend_scale_x
        set_compositor_scale(scale_node, mode=mode, x=scale_value, y=scale_value)
    else:
        set_compositor_scale(scale_node, mode=mode, x=settings.legend_scale_x, y=settings.legend_scale_y)

    bpy.context.view_layer.update()

    for node in tree.nodes:
        if hasattr(node, 'update'):
            node.update()

    for area in bpy.context.screen.areas:
        if area.type == 'NODE_EDITOR':
            area.tag_redraw()