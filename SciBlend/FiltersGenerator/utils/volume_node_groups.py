import bpy


def _create_socket(interface, name, io_type, sock_type, defaults=None):
    """Helper to create and configure a socket with common attributes."""
    sock = interface.new_socket(name, in_out=io_type, socket_type=sock_type)
    sock.attribute_domain = 'POINT'
    if defaults:
        for key, val in defaults.items():
            setattr(sock, key, val)
    return sock


def _build_threshold_masking_graph():
    """Construct node group that masks values at 0 and 1 extremes based on flags."""
    group_name = "SciBlend_Threshold_Mask"
    existing = bpy.data.node_groups.get(group_name)
    if existing:
        return existing
    
    ng = bpy.data.node_groups.new(type='ShaderNodeTree', name=group_name)
    iface = ng.interface
    
    _create_socket(iface, "Normalized", "INPUT", 'NodeSocketFloat')
    _create_socket(iface, "Mask Lower Bound", "INPUT", 'NodeSocketBool', {'default_value': True})
    _create_socket(iface, "Mask Upper Bound", "INPUT", 'NodeSocketBool', {'default_value': False})
    _create_socket(iface, "Result", "OUTPUT", 'NodeSocketFloat')
    
    nodes = ng.nodes
    links = ng.links
    
    input_node = nodes.new("NodeGroupInput")
    output_node = nodes.new("NodeGroupOutput")
    input_node.location = (-400, 0)
    output_node.location = (800, 0)

    negate_lower = nodes.new("ShaderNodeMath")
    negate_lower.operation = "SUBTRACT"
    negate_lower.inputs[0].default_value = 1.0
    negate_lower.location = (-200, 120)
    links.new(input_node.outputs["Mask Lower Bound"], negate_lower.inputs[1])
    
    compare_lower = nodes.new("ShaderNodeMath")
    compare_lower.operation = "GREATER_THAN"
    compare_lower.location = (0, 120)
    links.new(input_node.outputs["Normalized"], compare_lower.inputs[0])
    links.new(negate_lower.outputs[0], compare_lower.inputs[1])
    

    invert_upper_flag = nodes.new("ShaderNodeMath")
    invert_upper_flag.operation = "LESS_THAN"
    invert_upper_flag.inputs[1].default_value = 1.0
    invert_upper_flag.location = (-200, -120)
    links.new(input_node.outputs["Mask Upper Bound"], invert_upper_flag.inputs[0])
    
    compute_upper_threshold = nodes.new("ShaderNodeMath")
    compute_upper_threshold.operation = "ADD"
    compute_upper_threshold.inputs[1].default_value = 1.0
    compute_upper_threshold.location = (0, -200)
    links.new(invert_upper_flag.outputs[0], compute_upper_threshold.inputs[0])
    
    compare_upper = nodes.new("ShaderNodeMath")
    compare_upper.operation = "LESS_THAN"
    compare_upper.location = (200, -120)
    links.new(input_node.outputs["Normalized"], compare_upper.inputs[0])
    links.new(compute_upper_threshold.outputs[0], compare_upper.inputs[1])
    
    combine_masks = nodes.new("ShaderNodeMath")
    combine_masks.operation = "MULTIPLY"
    combine_masks.location = (500, 0)
    links.new(compare_lower.outputs[0], combine_masks.inputs[0])
    links.new(compare_upper.outputs[0], combine_masks.inputs[1])
    
    links.new(combine_masks.outputs[0], output_node.inputs["Result"])
    return ng


def _build_density_controller_graph():
    """Construct the main density/alpha controller with baseline, multiplier and masking."""
    group_name = "SciBlend_Volume_Density"
    existing = bpy.data.node_groups.get(group_name)
    if existing:
        required_inputs = ['Opacity Unit Distance', 'Step Size']
        has_new_inputs = all(inp in existing.interface.items_tree for inp in required_inputs)
        if has_new_inputs:
            return existing
        else:
            bpy.data.node_groups.remove(existing)
    
    ng = bpy.data.node_groups.new(type='ShaderNodeTree', name=group_name)
    iface = ng.interface
    
    _create_socket(iface, "Normalized Value", "INPUT", 'NodeSocketFloat')
    _create_socket(iface, "Enable Lower Clip", "INPUT", 'NodeSocketBool', {'default_value': True})
    _create_socket(iface, "Enable Upper Clip", "INPUT", 'NodeSocketBool', {'default_value': True})
    _create_socket(iface, "Base Density", "INPUT", 'NodeSocketFloat', 
                   {'default_value': 0.0, 'min_value': 0.0, 'max_value': 100.0})
    _create_socket(iface, "Scale Factor", "INPUT", 'NodeSocketFloat',
                   {'default_value': 0.15, 'min_value': 0.0, 'max_value': 100.0})
    _create_socket(iface, "Opacity Unit Distance", "INPUT", 'NodeSocketFloat',
                   {'default_value': 1.0, 'min_value': 0.0, 'max_value': 100.0})
    _create_socket(iface, "Step Size", "INPUT", 'NodeSocketFloat',
                   {'default_value': 0.05, 'min_value': 0.001, 'max_value': 1000.0})
    
    _create_socket(iface, "Density", "OUTPUT", 'NodeSocketFloat')
    
    nodes = ng.nodes
    links = ng.links
    
    input_node = nodes.new("NodeGroupInput")
    output_node = nodes.new("NodeGroupOutput")
    input_node.location = (-800, 0)
    output_node.location = (1000, 0)
    
    density_compute = nodes.new("ShaderNodeMath")
    density_compute.operation = "MULTIPLY_ADD"
    density_compute.location = (-400, 100)
    links.new(input_node.outputs["Normalized Value"], density_compute.inputs[0])
    links.new(input_node.outputs["Scale Factor"], density_compute.inputs[1])
    links.new(input_node.outputs["Base Density"], density_compute.inputs[2])
    
    opacity_correction = nodes.new("ShaderNodeMath")
    opacity_correction.operation = "DIVIDE"
    opacity_correction.location = (0, -150)
    links.new(input_node.outputs["Step Size"], opacity_correction.inputs[0])
    links.new(input_node.outputs["Opacity Unit Distance"], opacity_correction.inputs[1])
    
    apply_opacity_correction = nodes.new("ShaderNodeMath")
    apply_opacity_correction.operation = "MULTIPLY"
    apply_opacity_correction.location = (200, 0)
    links.new(density_compute.outputs[0], apply_opacity_correction.inputs[0])
    links.new(opacity_correction.outputs[0], apply_opacity_correction.inputs[1])
    
    mask_group = nodes.new('ShaderNodeGroup')
    mask_group.node_tree = _build_threshold_masking_graph()
    mask_group.location = (-200, -300)
    mask_group.hide = True
    links.new(input_node.outputs["Normalized Value"], mask_group.inputs["Normalized"])
    links.new(input_node.outputs["Enable Lower Clip"], mask_group.inputs["Mask Lower Bound"])
    links.new(input_node.outputs["Enable Upper Clip"], mask_group.inputs["Mask Upper Bound"])
    
    final_multiply = nodes.new("ShaderNodeMath")
    final_multiply.operation = "MULTIPLY"
    final_multiply.location = (600, 0)
    links.new(apply_opacity_correction.outputs[0], final_multiply.inputs[0])
    links.new(mask_group.outputs["Result"], final_multiply.inputs[1])
    
    links.new(final_multiply.outputs[0], output_node.inputs["Density"])
    return ng


def get_volume_density_node_group():
    """Get or create the volume density controller node group."""
    return _build_density_controller_graph() 