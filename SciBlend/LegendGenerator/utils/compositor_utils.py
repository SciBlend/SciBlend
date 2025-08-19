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
    
    translate_node.inputs[1].default_value = scene.legend_position_x * render_size_x / 100
    translate_node.inputs[2].default_value = scene.legend_position_y * render_size_y / 100

def update_legend_scale_in_compositor(context):
    scene = context.scene
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

    if scene.legend_scale_mode == 'SCENE_SIZE':
        new_space = 'SCENE_SIZE'
    else:
        new_space = 'RENDER_SIZE'
    
    if scale_size_node.space != new_space:
        scale_size_node.space = new_space

    if scene.legend_scale_mode == 'RENDER_SIZE_FIT':
        scale_size_node.frame_method = 'FIT'
    elif scene.legend_scale_mode == 'RENDER_SIZE_CROP':
        scale_size_node.frame_method = 'CROP'
    else:  
        scale_size_node.frame_method = 'STRETCH'

    scale_x = scene.legend_scale_x
    scale_y = scene.legend_scale_y if not scene.legend_scale_linked else scene.legend_scale_x
    scale_legend_node.inputs[1].default_value = scale_x
    scale_legend_node.inputs[2].default_value = scale_y

    # Force a view update
    bpy.context.view_layer.update()

    for node in tree.nodes:
        if hasattr(node, 'update'):
            node.update()

    for area in bpy.context.screen.areas:
        area.tag_redraw()

def update_legend_scale_mode(context):
    update_legend_scale_in_compositor(context)