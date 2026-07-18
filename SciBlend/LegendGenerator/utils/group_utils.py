import bpy
from typing import Optional

from ...compat import set_compositor_scale


GROUP_NAME = "SciBlend_LegendGroup"


def _ensure_interface_socket(nodegroup: bpy.types.NodeTree, name: str, in_out: str, socket_type: str) -> bpy.types.NodeTreeInterfaceSocket:
    """Return an existing interface socket by name or create it."""
    for s in nodegroup.interface.items_tree:
        if getattr(s, 'name', '') == name and getattr(s, 'in_out', '') == in_out:
            return s
    return nodegroup.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)


def create_or_update_legend_group(image_filepath: str) -> bpy.types.NodeTree:
    """Create or update the compositor node group used for the legend overlay.

    The group includes:
    - CompositorNodeImage (loads provided image)
    - CompositorNodeTranslate (position)
    - CompositorNodeScale (RENDER_SIZE, FIT)
    - CompositorNodeScale (RELATIVE)

    Interface:
    - Inputs: Translate X (FLOAT), Translate Y (FLOAT), Scale X (FLOAT), Scale Y (FLOAT)
    - Outputs: Image (COLOR)
    """
    nodegroup = bpy.data.node_groups.get(GROUP_NAME)
    if not nodegroup:
        nodegroup = bpy.data.node_groups.new(type='CompositorNodeTree', name=GROUP_NAME)
    while nodegroup.nodes:
        nodegroup.nodes.remove(nodegroup.nodes[0])
    for item in list(nodegroup.interface.items_tree):
        try:
            nodegroup.interface.remove(item)
        except Exception:
            pass

    out_image = _ensure_interface_socket(nodegroup, "Image", 'OUTPUT', 'NodeSocketColor')
    in_tx = _ensure_interface_socket(nodegroup, "Translate X", 'INPUT', 'NodeSocketFloat')
    in_ty = _ensure_interface_socket(nodegroup, "Translate Y", 'INPUT', 'NodeSocketFloat')
    in_sx = _ensure_interface_socket(nodegroup, "Scale X", 'INPUT', 'NodeSocketFloat')
    in_sy = _ensure_interface_socket(nodegroup, "Scale Y", 'INPUT', 'NodeSocketFloat')

    group_in = nodegroup.nodes.new("NodeGroupInput")
    group_out = nodegroup.nodes.new("NodeGroupOutput")

    n_image = nodegroup.nodes.new("CompositorNodeImage")
    n_translate = nodegroup.nodes.new("CompositorNodeTranslate")
    n_scale_render = nodegroup.nodes.new("CompositorNodeScale")
    n_scale_rel = nodegroup.nodes.new("CompositorNodeScale")

    try:
        n_image.image = bpy.data.images.load(image_filepath)
        n_image.name = "SciBlendLegendImage"
    except Exception:
        pass

    set_compositor_scale(n_scale_render, mode='Render Size', frame_method='Fit')
    set_compositor_scale(n_scale_rel, mode='Relative')

    nodegroup.links.new(n_image.outputs.get('Image'), n_translate.inputs.get('Image'))
    nodegroup.links.new(n_translate.outputs.get('Image'), n_scale_render.inputs.get('Image'))
    nodegroup.links.new(n_scale_render.outputs.get('Image'), n_scale_rel.inputs.get('Image'))
    nodegroup.links.new(n_scale_rel.outputs.get('Image'), group_out.inputs.get('Image'))

    tx_out = group_in.outputs.get("Translate X")
    ty_out = group_in.outputs.get("Translate Y")
    nodegroup.links.new(tx_out, n_translate.inputs.get('X') or n_translate.inputs[1])
    nodegroup.links.new(ty_out, n_translate.inputs.get('Y') or n_translate.inputs[2])
    sx_in = n_scale_rel.inputs.get('X')
    sy_in = n_scale_rel.inputs.get('Y')
    if sx_in is not None:
        nodegroup.links.new(group_in.outputs.get("Scale X"), sx_in)
    if sy_in is not None:
        nodegroup.links.new(group_in.outputs.get("Scale Y"), sy_in)

    group_in.location = (-600, 0)
    n_image.location = (-400, 0)
    n_translate.location = (-200, 0)
    n_scale_render.location = (0, 0)
    n_scale_rel.location = (200, 0)
    group_out.location = (400, 0)

    return nodegroup 