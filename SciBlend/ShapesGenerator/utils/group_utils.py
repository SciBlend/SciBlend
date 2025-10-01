import bpy


def create_or_update_shape_group(group_name: str, image_filepath: str, as_sequence: bool = False, sequence_duration: int | None = None) -> bpy.types.NodeTree:
    """Create or update a compositor node group for a shape overlay.

    The group contains Image -> Transform -> Scale(RENDER_SIZE) -> Scale(RELATIVE) -> Output.
    Interface inputs: Translate X, Translate Y, Angle, Scale Size X, Scale Size Y, Scale X, Scale Y. Output: Image.
    """
    nodegroup = bpy.data.node_groups.get(group_name)
    if not nodegroup:
        nodegroup = bpy.data.node_groups.new(type='CompositorNodeTree', name=group_name)
    while nodegroup.nodes:
        nodegroup.nodes.remove(nodegroup.nodes[0])
    for item in list(nodegroup.interface.items_tree):
        try:
            nodegroup.interface.remove(item)
        except Exception:
            pass

    out_image = nodegroup.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    in_tx = nodegroup.interface.new_socket(name="Translate X", in_out='INPUT', socket_type='NodeSocketFloat')
    in_ty = nodegroup.interface.new_socket(name="Translate Y", in_out='INPUT', socket_type='NodeSocketFloat')
    in_ang = nodegroup.interface.new_socket(name="Angle", in_out='INPUT', socket_type='NodeSocketFloat')
    in_ssx = nodegroup.interface.new_socket(name="Scale Size X", in_out='INPUT', socket_type='NodeSocketFloat')
    in_ssy = nodegroup.interface.new_socket(name="Scale Size Y", in_out='INPUT', socket_type='NodeSocketFloat')
    in_sx = nodegroup.interface.new_socket(name="Scale X", in_out='INPUT', socket_type='NodeSocketFloat')
    in_sy = nodegroup.interface.new_socket(name="Scale Y", in_out='INPUT', socket_type='NodeSocketFloat')

    group_in = nodegroup.nodes.new("NodeGroupInput")
    group_out = nodegroup.nodes.new("NodeGroupOutput")

    n_image = nodegroup.nodes.new("CompositorNodeImage")
    n_transform = nodegroup.nodes.new("CompositorNodeTransform")
    n_scale_render = nodegroup.nodes.new("CompositorNodeScale")
    n_scale_rel = nodegroup.nodes.new("CompositorNodeScale")

    try:
        n_image.image = bpy.data.images.load(image_filepath)
        n_image.name = f"{group_name}_Image"
        try:
            if n_image.image:
                n_image.image.source = 'SEQUENCE' if as_sequence else 'FILE'
        except Exception:
            pass
        try:
            n_image.use_auto_refresh = bool(as_sequence)
            n_image.use_cyclic = False
            n_image.frame_start = 1
            if as_sequence and isinstance(sequence_duration, int) and sequence_duration > 0:
                n_image.frame_duration = sequence_duration
        except Exception:
            pass
    except Exception:
        pass

    n_scale_render.space = 'RENDER_SIZE'
    n_scale_render.frame_method = 'CROP'

    n_scale_rel.space = 'RELATIVE'

    nodegroup.links.new(n_image.outputs.get('Image'), n_transform.inputs.get('Image'))
    nodegroup.links.new(n_transform.outputs.get('Image'), n_scale_render.inputs.get('Image'))
    nodegroup.links.new(n_scale_render.outputs.get('Image'), n_scale_rel.inputs.get('Image'))
    nodegroup.links.new(n_scale_rel.outputs.get('Image'), group_out.inputs.get('Image'))

    nodegroup.links.new(group_in.outputs.get("Translate X"), n_transform.inputs[1])
    nodegroup.links.new(group_in.outputs.get("Translate Y"), n_transform.inputs[2])
    nodegroup.links.new(group_in.outputs.get("Angle"), n_transform.inputs[3])
    if 'X' in n_scale_render.inputs and 'Y' in n_scale_render.inputs:
        nodegroup.links.new(group_in.outputs.get("Scale Size X"), n_scale_render.inputs['X'])
        nodegroup.links.new(group_in.outputs.get("Scale Size Y"), n_scale_render.inputs['Y'])
    elif 'Scale' in n_scale_render.inputs:
        nodegroup.links.new(group_in.outputs.get("Scale Size X"), n_scale_render.inputs['Scale'])
    if 'X' in n_scale_rel.inputs and 'Y' in n_scale_rel.inputs:
        nodegroup.links.new(group_in.outputs.get("Scale X"), n_scale_rel.inputs['X'])
        nodegroup.links.new(group_in.outputs.get("Scale Y"), n_scale_rel.inputs['Y'])
    elif 'Scale' in n_scale_rel.inputs:
        nodegroup.links.new(group_in.outputs.get("Scale X"), n_scale_rel.inputs['Scale'])

    group_in.location = (-600, 0)
    n_image.location = (-400, 0)
    n_transform.location = (-200, 0)
    n_scale_render.location = (0, 0)
    n_scale_rel.location = (200, 0)
    group_out.location = (400, 0)

    return nodegroup 