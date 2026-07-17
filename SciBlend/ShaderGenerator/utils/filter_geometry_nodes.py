import bpy
import logging

logger = logging.getLogger(__name__)

FILTER_MODIFIER_NAME = "SciBlend_Filter"
FILTER_TREE_PREFIX = "SciBlend_Filter_"
RULE_MAT_PREFIX = "SciBlend_Rule_"


def build_filter_geometry_nodes(collection, colormap_material, filters, enable):
    """Build or update the Geometry Nodes filter setup for a collection.

    Parameters
    ----------
    collection : bpy.types.Collection
        The collection containing mesh objects.
    colormap_material : bpy.types.Material
        The main colormap material applied to the mesh.
    filters : list[dict]
        List of filter rules with keys 'attribute', 'operator', 'value', 'enabled',
        'display_mode', 'display_color', 'display_material'.
    enable : bool
        Whether filtering is enabled.

    Returns
    -------
    bool
        True if successful.
    """
    if not collection:
        return False

    enabled_filters = [f for f in filters if f.get('enabled', True) and f.get('attribute', '')]

    if not enable or not enabled_filters:
        _remove_filter_setup(collection)
        return True

    rule_materials = []
    for idx, f in enumerate(enabled_filters):
        mat = _get_or_create_rule_material(
            collection.name,
            idx,
            f.get('display_mode', 'SOLID_COLOR'),
            f.get('display_color', (0.8, 0.2, 0.2)),
            f.get('display_material', ''),
        )
        rule_materials.append(mat)

    tree_name = f"{FILTER_TREE_PREFIX}{collection.name}"
    node_tree = _build_filter_node_tree(tree_name, enabled_filters, rule_materials)

    mesh_objects = [obj for obj in collection.objects if obj.type == 'MESH']
    _apply_filter_modifier(mesh_objects, node_tree, rule_materials)

    logger.info("Built filter geometry nodes for collection %s", collection.name)
    return True


def _get_or_create_rule_material(collection_name, rule_index, display_mode, display_color, display_material_name):
    """Create or update the material for a specific filter rule.

    Parameters
    ----------
    collection_name : str
        Name of the collection (used for material naming).
    rule_index : int
        Index of the rule in the filter list.
    display_mode : str
        'SOLID_COLOR', 'TRANSPARENT', or 'MATERIAL'.
    display_color : tuple
        RGB color for SOLID_COLOR mode.
    display_material_name : str
        Name of existing material for MATERIAL mode.

    Returns
    -------
    bpy.types.Material
        The material for this rule.
    """
    if display_mode == 'MATERIAL' and display_material_name:
        existing_mat = bpy.data.materials.get(display_material_name)
        if existing_mat:
            return existing_mat

    mat_name = f"{RULE_MAT_PREFIX}{collection_name}_{rule_index}"
    mat = bpy.data.materials.get(mat_name)

    if not mat:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    bsdf = None
    output = None
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            bsdf = node
        elif node.type == 'OUTPUT_MATERIAL':
            output = node

    if not bsdf:
        nodes.clear()
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (300, 0)
        links.new(bsdf.outputs[0], output.inputs[0])

    if display_mode == 'TRANSPARENT':
        bsdf.inputs['Base Color'].default_value = (0.0, 0.0, 0.0, 1.0)
        bsdf.inputs['Alpha'].default_value = 0.0
        mat.blend_method = 'BLEND'
        if hasattr(mat, 'shadow_method'):
            mat.shadow_method = 'CLIP'
    else:
        bsdf.inputs['Base Color'].default_value = (
            display_color[0], display_color[1], display_color[2], 1.0
        )
        bsdf.inputs['Alpha'].default_value = 1.0
        mat.blend_method = 'OPAQUE'

    mat['sciblend_rule_material'] = True
    mat['sciblend_rule_index'] = rule_index
    return mat


def _build_filter_node_tree(tree_name, filters, rule_materials):
    """Create or rebuild the Geometry Nodes tree for filtering with per-rule materials.

    Parameters
    ----------
    tree_name : str
        Name of the node tree.
    filters : list[dict]
        List of enabled filter rules.
    rule_materials : list[bpy.types.Material]
        Materials corresponding to each filter rule.

    Returns
    -------
    bpy.types.NodeTree
        The Geometry Nodes tree.
    """
    ng = bpy.data.node_groups.get(tree_name)
    if ng:
        ng.nodes.clear()
        ng.interface.clear()
    else:
        ng = bpy.data.node_groups.new(tree_name, 'GeometryNodeTree')

    nodes = ng.nodes
    links = ng.links

    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    group_input = nodes.new('NodeGroupInput')
    group_input.location = (-800, 0)

    group_output = nodes.new('NodeGroupOutput')
    group_output.location = (1200, 0)

    condition_outputs = []
    base_x = -600
    base_y = 300

    for idx, f in enumerate(filters):
        attr_name = f.get('attribute', '')
        operator = f.get('operator', 'EQUAL')
        value = float(f.get('value', 0.0))
        y_offset = idx * -250

        named_attr = nodes.new('GeometryNodeInputNamedAttribute')
        named_attr.data_type = 'FLOAT'
        named_attr.inputs['Name'].default_value = attr_name
        named_attr.location = (base_x, base_y + y_offset)

        if operator in ('IS_NAN', 'IS_NOT_NAN'):
            compare = nodes.new('FunctionNodeCompare')
            compare.data_type = 'FLOAT'
            compare.operation = 'EQUAL'
            compare.location = (base_x + 200, base_y + y_offset)
            if 'Epsilon' in compare.inputs:
                compare.inputs['Epsilon'].default_value = 0.0001

            links.new(named_attr.outputs['Attribute'], compare.inputs['A'])
            links.new(named_attr.outputs['Attribute'], compare.inputs['B'])

            if operator == 'IS_NAN':
                bool_not = nodes.new('FunctionNodeBooleanMath')
                bool_not.operation = 'NOT'
                bool_not.location = (base_x + 400, base_y + y_offset)
                links.new(compare.outputs['Result'], bool_not.inputs[0])
                condition_outputs.append(bool_not.outputs[0])
            else:
                condition_outputs.append(compare.outputs['Result'])
        else:
            compare = nodes.new('FunctionNodeCompare')
            compare.data_type = 'FLOAT'
            compare.location = (base_x + 200, base_y + y_offset)

            op_map = {
                'EQUAL': 'EQUAL',
                'NOT_EQUAL': 'NOT_EQUAL',
                'GREATER_THAN': 'GREATER_THAN',
                'LESS_THAN': 'LESS_THAN',
                'GREATER_EQUAL': 'GREATER_EQUAL',
                'LESS_EQUAL': 'LESS_EQUAL',
            }
            compare.operation = op_map.get(operator, 'EQUAL')

            if operator in ('EQUAL', 'NOT_EQUAL') and 'Epsilon' in compare.inputs:
                compare.inputs['Epsilon'].default_value = 0.5

            links.new(named_attr.outputs['Attribute'], compare.inputs['A'])
            compare.inputs['B'].default_value = value

            condition_outputs.append(compare.outputs['Result'])

    set_mat_x = 400
    set_mat_y = 0
    current_geometry = group_input.outputs['Geometry']
    already_matched_output = None

    for idx, (cond_output, mat) in enumerate(zip(condition_outputs, rule_materials)):
        y_offset = idx * -150

        if already_matched_output is not None:
            exclude_node = nodes.new('FunctionNodeBooleanMath')
            exclude_node.operation = 'NIMPLY'
            exclude_node.location = (set_mat_x - 200, set_mat_y + y_offset)
            links.new(cond_output, exclude_node.inputs[0])
            links.new(already_matched_output, exclude_node.inputs[1])
            selection_output = exclude_node.outputs[0]
        else:
            selection_output = cond_output

        set_material = nodes.new('GeometryNodeSetMaterial')
        set_material.location = (set_mat_x, set_mat_y + y_offset)
        set_material.inputs['Material'].default_value = mat

        links.new(current_geometry, set_material.inputs['Geometry'])
        links.new(selection_output, set_material.inputs['Selection'])

        current_geometry = set_material.outputs['Geometry']

        if already_matched_output is None:
            already_matched_output = cond_output
        else:
            combine_matched = nodes.new('FunctionNodeBooleanMath')
            combine_matched.operation = 'OR'
            combine_matched.location = (set_mat_x + 100, set_mat_y + y_offset - 50)
            links.new(already_matched_output, combine_matched.inputs[0])
            links.new(cond_output, combine_matched.inputs[1])
            already_matched_output = combine_matched.outputs[0]

    links.new(current_geometry, group_output.inputs['Geometry'])

    return ng


def _apply_filter_modifier(objects, node_tree, rule_materials):
    """Apply or update the filter modifier on mesh objects.

    Parameters
    ----------
    objects : list[bpy.types.Object]
        List of mesh objects.
    node_tree : bpy.types.NodeTree
        The Geometry Nodes tree.
    rule_materials : list[bpy.types.Material]
        Materials used by filter rules.
    """
    for obj in objects:
        if obj.type != 'MESH':
            continue

        existing_mat_names = [m.name for m in obj.data.materials if m]
        for mat in rule_materials:
            if mat.name not in existing_mat_names:
                obj.data.materials.append(mat)

        modifier = obj.modifiers.get(FILTER_MODIFIER_NAME)
        if not modifier:
            modifier = obj.modifiers.new(name=FILTER_MODIFIER_NAME, type='NODES')

        modifier.node_group = node_tree


def _remove_filter_setup(collection):
    """Remove the filter modifier and rule materials from all objects.

    Parameters
    ----------
    collection : bpy.types.Collection
        The collection to clean up.
    """
    if not collection:
        return

    tree_name = f"{FILTER_TREE_PREFIX}{collection.name}"
    rule_mat_prefix = f"{RULE_MAT_PREFIX}{collection.name}_"

    for obj in collection.objects:
        if obj.type != 'MESH':
            continue

        modifier = obj.modifiers.get(FILTER_MODIFIER_NAME)
        if modifier:
            obj.modifiers.remove(modifier)

        indices_to_remove = []
        for i, mat in enumerate(obj.data.materials):
            if mat and mat.name.startswith(rule_mat_prefix):
                indices_to_remove.append(i)

        for i in reversed(indices_to_remove):
            if len(obj.data.materials) > 1:
                obj.data.materials.pop(index=i)

    ng = bpy.data.node_groups.get(tree_name)
    if ng and ng.users == 0:
        bpy.data.node_groups.remove(ng)

    for mat in list(bpy.data.materials):
        if mat.name.startswith(rule_mat_prefix) and mat.users == 0:
            bpy.data.materials.remove(mat)

    logger.info("Removed filter setup for collection %s", collection.name)
