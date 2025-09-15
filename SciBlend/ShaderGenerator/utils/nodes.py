import bpy


def find_shader_map_range_node(material: bpy.types.Material):
    """Return the Map Range node used by Shader Generator, preferring the labeled one.

    The function first searches for a node with the custom label 'SCIBLEND_MAP_RANGE' or
    custom property 'sciblend_map_range'. If not found, it returns the first Map Range node.
    """
    if not material or not getattr(material, 'use_nodes', False) or not getattr(material, 'node_tree', None):
        return None
    nodes = material.node_tree.nodes
    for node in nodes:
        if getattr(node, 'type', None) == 'MAP_RANGE':
            label = getattr(node, 'label', '') or ''
            if label == 'SCIBLEND_MAP_RANGE' or bool(getattr(node, 'get', lambda k, d=None: None)('sciblend_map_range', None)):
                return node
    for node in nodes:
        if getattr(node, 'type', None) == 'MAP_RANGE':
            return node
    return None 