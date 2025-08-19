import bpy

def update_legend_position_in_compositor(context):
    scene = context.scene
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
    
    translate_node.inputs["X"].default_value = scene.legend_position_x * render_size_x / 10
    translate_node.inputs["Y"].default_value = scene.legend_position_y * render_size_y / 10

def update_legend_scale_in_compositor(context):
    scene = context.scene
    tree = scene.node_tree
    
    if tree is None:
        return

    scale_node = None
    for node in tree.nodes:
        if node.type == 'SCALE':
            scale_node = node
            break

    if scale_node is None:
        return

    scale_node.space = 'RELATIVE' if scene.legend_scale_mode == 'SCENE' else 'RENDER_SIZE'

    if scene.legend_scale_linked:
        scale_value = scene.legend_scale_x
        scale_node.inputs['X'].default_value = scale_value
        scale_node.inputs['Y'].default_value = scale_value
    else:
        scale_node.inputs['X'].default_value = scene.legend_scale_x
        scale_node.inputs['Y'].default_value = scene.legend_scale_y

    bpy.context.view_layer.update()

    for node in tree.nodes:
        if hasattr(node, 'update'):
            node.update()

    for area in bpy.context.screen.areas:
        if area.type == 'NODE_EDITOR':
            area.tag_redraw()