import bpy
import logging
from .colormaps import COLORMAPS, interpolate_colormap
from .nodes import find_shader_map_range_node

logger = logging.getLogger(__name__)


def load_settings_from_material(material):
    """Read current shader settings from a material's custom properties and nodes.
    
    Parameters
    ----------
    material : bpy.types.Material
        The material to read settings from.
        
    Returns
    -------
    dict
        Dictionary with shader settings including transparency options.
    """
    if not material:
        return None
        
    settings = {}
    
    settings['colormap'] = material.get('sciblend_colormap', 'viridis')
    settings['attribute'] = material.get('sciblend_attribute', 'Col')
    settings['normalization'] = material.get('sciblend_normalization', 'AUTO')
    settings['enable_transparency'] = material.get('sciblend_enable_transparency', False)
    settings['transparency_mode'] = material.get('sciblend_transparency_mode', 'RANGE')
    settings['transparency_min'] = material.get('sciblend_transparency_min', 0.0)
    settings['transparency_max'] = material.get('sciblend_transparency_max', 0.1)
    settings['invert_transparency'] = material.get('sciblend_invert_transparency', False)
    
    if material.use_nodes and material.node_tree:
        nodes = material.node_tree.nodes
        
        for node in nodes:
            if node.type == 'VALTORGB':
                settings['interpolation'] = node.color_ramp.interpolation
                break
        else:
            settings['interpolation'] = 'CONSTANT'
            
        for node in nodes:
            if node.type == 'GAMMA':
                settings['gamma'] = node.inputs[1].default_value
                break
        else:
            settings['gamma'] = 2.2
            
        map_range = find_shader_map_range_node(material)
        if map_range:
            settings['from_min'] = map_range.inputs['From Min'].default_value
            settings['from_max'] = map_range.inputs['From Max'].default_value
        else:
            settings['from_min'] = 0.0
            settings['from_max'] = 1.0
    else:
        settings['interpolation'] = 'CONSTANT'
        settings['gamma'] = 2.2
        settings['from_min'] = 0.0
        settings['from_max'] = 1.0
        
    return settings


def find_colorramp_node(material):
    """Find the ColorRamp node in a Shader Generator material.
    
    Parameters
    ----------
    material : bpy.types.Material
        The material to search.
        
    Returns
    -------
    bpy.types.ShaderNode or None
        The ColorRamp node if found.
    """
    if not material or not material.use_nodes or not material.node_tree:
        return None
        
    for node in material.node_tree.nodes:
        if node.type == 'VALTORGB':
            return node
    return None


def find_gamma_node(material):
    """Find the Gamma node in a Shader Generator material.
    
    Parameters
    ----------
    material : bpy.types.Material
        The material to search.
        
    Returns
    -------
    bpy.types.ShaderNode or None
        The Gamma node if found.
    """
    if not material or not material.use_nodes or not material.node_tree:
        return None
        
    for node in material.node_tree.nodes:
        if node.type == 'GAMMA':
            return node
    return None


def find_attribute_node(material):
    """Find the Attribute node in a Shader Generator material.
    
    Parameters
    ----------
    material : bpy.types.Material
        The material to search.
        
    Returns
    -------
    bpy.types.ShaderNode or None
        The Attribute node if found.
    """
    if not material or not material.use_nodes or not material.node_tree:
        return None
        
    for node in material.node_tree.nodes:
        if node.type == 'ATTRIBUTE':
            return node
    return None


def update_material_colormap(material, colormap_name, custom_colormap=None):
    """Update the ColorRamp node with a new colormap.
    
    Parameters
    ----------
    material : bpy.types.Material
        The material to update.
    colormap_name : str
        Name of the colormap or 'CUSTOM'.
    custom_colormap : list[dict] or None
        Custom colormap data if colormap_name is 'CUSTOM'.
        
    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    if not material:
        return False
        
    node_colorramp = find_colorramp_node(material)
    if not node_colorramp:
        logger.warning("No ColorRamp node found in material %s", material.name)
        return False
        
    try:
        if colormap_name == "CUSTOM":
            colors = custom_colormap
        else:
            colors = COLORMAPS[colormap_name]['colors']
            
        if len(colors) != 32:
            colors = interpolate_colormap(colors, 32)
            
        for i in range(len(node_colorramp.color_ramp.elements) - 1, 0, -1):
            node_colorramp.color_ramp.elements.remove(node_colorramp.color_ramp.elements[i])
            
        for i, color_data in enumerate(colors):
            if i == 0:
                elem = node_colorramp.color_ramp.elements[0]
            else:
                elem = node_colorramp.color_ramp.elements.new(color_data['position'])
            elem.color = color_data['color'] + (1.0,)
            
        node_colorramp.label = str(colormap_name)
        material['sciblend_colormap'] = colormap_name
        material.node_tree.update_tag()
        
        logger.info("Updated colormap for material %s to %s", material.name, colormap_name)
        return True
        
    except Exception as e:
        logger.error("Failed to update colormap: %s", e)
        return False


def update_material_interpolation(material, interpolation):
    """Update the ColorRamp interpolation type.
    
    Parameters
    ----------
    material : bpy.types.Material
        The material to update.
    interpolation : str
        Interpolation type ('CONSTANT', 'LINEAR', 'EASE', 'CARDINAL', 'B_SPLINE').
        
    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    if not material:
        return False
        
    node_colorramp = find_colorramp_node(material)
    if not node_colorramp:
        return False
        
    try:
        node_colorramp.color_ramp.interpolation = interpolation
        material.node_tree.update_tag()
        logger.info("Updated interpolation for material %s to %s", material.name, interpolation)
        return True
    except Exception as e:
        logger.error("Failed to update interpolation: %s", e)
        return False


def update_material_gamma(material, gamma):
    """Update the Gamma node value.
    
    Parameters
    ----------
    material : bpy.types.Material
        The material to update.
    gamma : float
        The gamma value.
        
    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    if not material:
        return False
        
    node_gamma = find_gamma_node(material)
    if not node_gamma:
        return False
        
    try:
        node_gamma.inputs[1].default_value = gamma
        material.node_tree.update_tag()
        logger.info("Updated gamma for material %s to %s", material.name, gamma)
        return True
    except Exception as e:
        logger.error("Failed to update gamma: %s", e)
        return False


def update_material_attribute(material, attribute_name):
    """Update the Attribute node to use a different attribute.
    
    Parameters
    ----------
    material : bpy.types.Material
        The material to update.
    attribute_name : str
        Name of the attribute.
        
    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    if not material:
        return False
        
    node_attrib = find_attribute_node(material)
    if not node_attrib:
        return False
        
    try:
        node_attrib.attribute_name = attribute_name
        material['sciblend_attribute'] = attribute_name
        material.node_tree.update_tag()
        logger.info("Updated attribute for material %s to %s", material.name, attribute_name)
        return True
    except Exception as e:
        logger.error("Failed to update attribute: %s", e)
        return False


def update_material_normalization(material, normalization, color_range=None):
    """Update the Map Range node based on normalization setting.
    
    Parameters
    ----------
    material : bpy.types.Material
        The material to update.
    normalization : str
        One of 'AUTO', 'GLOBAL', 'NONE'.
    color_range : tuple[float, float] or None
        Min and max values for the range.
        
    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    if not material:
        return False
        
    map_range = find_shader_map_range_node(material)
    if not map_range:
        return False
        
    try:
        material['sciblend_normalization'] = normalization
        
        if color_range and normalization != 'NONE':
            min_value, max_value = color_range
            if normalization in {'AUTO', 'GLOBAL'}:
                map_range.inputs['From Min'].default_value = min_value
                map_range.inputs['From Max'].default_value = max_value
        else:
            map_range.inputs['From Min'].default_value = 0.0
            map_range.inputs['From Max'].default_value = 1.0
            
        material.node_tree.update_tag()
        logger.info("Updated normalization for material %s to %s", material.name, normalization)
        return True
    except Exception as e:
        logger.error("Failed to update normalization: %s", e)
        return False


def get_material_from_collection(collection):
    """Get the first material found in objects of a collection.
    
    Parameters
    ----------
    collection : bpy.types.Collection
        The collection to search.
        
    Returns
    -------
    bpy.types.Material or None
        The first material found, or None.
    """
    if not collection:
        return None
        
    for obj in collection.objects:
        if obj.type == 'MESH' and obj.data.materials:
            if len(obj.data.materials) > 0 and obj.data.materials[0]:
                return obj.data.materials[0]
    return None


def update_material_transparency(material, enable, mode, min_val, max_val, invert):
    """Update or create transparency nodes in the material.
    
    Parameters
    ----------
    material : bpy.types.Material
        The material to update.
    enable : bool
        Whether transparency is enabled.
    mode : str
        Transparency mode: 'RANGE', 'NAN', or 'BOTH'.
    min_val : float
        Minimum value for range mode.
    max_val : float
        Maximum value for range mode.
    invert : bool
        Whether to invert the transparency mask.
        
    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    print(f"[TRANSPARENCY] Called with enable={enable}, mode={mode}, min={min_val}, max={max_val}, invert={invert}")
    
    if not material or not material.use_nodes or not material.node_tree:
        print(f"[TRANSPARENCY] Early return: material checks failed")
        return False
    
    print(f"[TRANSPARENCY] Material: {material.name}")
    
    try:
        material['sciblend_enable_transparency'] = enable
        material['sciblend_transparency_mode'] = mode
        material['sciblend_transparency_min'] = min_val
        material['sciblend_transparency_max'] = max_val
        material['sciblend_invert_transparency'] = invert
        
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        
        attrib_node = find_attribute_node(material)
        print(f"[TRANSPARENCY] Attribute node found: {attrib_node}")
        
        bsdf_node = None
        output_node = None
        
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                bsdf_node = node
            elif node.type == 'OUTPUT_MATERIAL':
                output_node = node
        
        print(f"[TRANSPARENCY] BSDF node: {bsdf_node}, Output node: {output_node}")
        
        if not attrib_node or not bsdf_node or not output_node:
            print(f"[TRANSPARENCY] Missing required nodes!")
            return False
        
        transparency_nodes = [n for n in nodes if hasattr(n, 'label') and 'SCIBLEND_TRANSPARENCY' in str(n.label)]
        print(f"[TRANSPARENCY] Removing {len(transparency_nodes)} old transparency nodes")
        for node in transparency_nodes:
            nodes.remove(node)
        
        if not enable:
            print(f"[TRANSPARENCY] Transparency disabled, setting material to OPAQUE")
            material.blend_method = 'OPAQUE'
            material.node_tree.update_tag()
            return True
        
        print(f"[TRANSPARENCY] Enabling transparency with mode: {mode}")
        material.blend_method = 'BLEND'
        if hasattr(material, 'shadow_method'):
            material.shadow_method = 'CLIP'
        
        base_x = attrib_node.location.x
        base_y = attrib_node.location.y - 300
        print(f"[TRANSPARENCY] Base position: ({base_x}, {base_y})")
        
        if mode == 'NAN':
            print(f"[TRANSPARENCY] Creating NAN detection nodes")
            # NaN detection: NaN != NaN, so we compare value with itself
            # If EQUAL returns 1, it's NOT NaN. If it returns 0, it IS NaN.
            is_nan_node = nodes.new(type='ShaderNodeMath')
            is_nan_node.operation = 'COMPARE'
            is_nan_node.location = (base_x + 200, base_y)
            is_nan_node.label = 'SCIBLEND_TRANSPARENCY_NAN_CHECK'
            is_nan_node.inputs[2].default_value = 0.0001  # epsilon for comparison
            
            # Connect the same value to both inputs to compare with itself
            links.new(attrib_node.outputs[2], is_nan_node.inputs[0])
            links.new(attrib_node.outputs[2], is_nan_node.inputs[1])
            
            # Now invert: if EQUAL=1 (not NaN), we want alpha=1 (opaque)
            #             if EQUAL=0 (is NaN), we want alpha=0 (transparent)
            # So the EQUAL result is already what we want for alpha!
            alpha_socket = is_nan_node.outputs[0]
            print(f"[TRANSPARENCY] NAN node created: {is_nan_node}")
            
        elif mode == 'RANGE':
            print(f"[TRANSPARENCY] Creating RANGE detection nodes")
            in_range_low = nodes.new(type='ShaderNodeMath')
            in_range_low.operation = 'GREATER_THAN'
            in_range_low.location = (base_x + 200, base_y)
            in_range_low.label = 'SCIBLEND_TRANSPARENCY_LOW'
            in_range_low.inputs[1].default_value = min_val
            
            in_range_high = nodes.new(type='ShaderNodeMath')
            in_range_high.operation = 'LESS_THAN'
            in_range_high.location = (base_x + 200, base_y - 100)
            in_range_high.label = 'SCIBLEND_TRANSPARENCY_HIGH'
            in_range_high.inputs[1].default_value = max_val
            
            combine_range = nodes.new(type='ShaderNodeMath')
            combine_range.operation = 'MULTIPLY'
            combine_range.location = (base_x + 400, base_y - 50)
            combine_range.label = 'SCIBLEND_TRANSPARENCY_COMBINE'
            
            # Invert: if in range (combine=1), we want transparent (alpha=0)
            invert_range = nodes.new(type='ShaderNodeMath')
            invert_range.operation = 'SUBTRACT'
            invert_range.location = (base_x + 600, base_y - 50)
            invert_range.label = 'SCIBLEND_TRANSPARENCY_INVERT_RANGE'
            invert_range.inputs[0].default_value = 1.0
            
            links.new(attrib_node.outputs[2], in_range_low.inputs[0])
            links.new(attrib_node.outputs[2], in_range_high.inputs[0])
            links.new(in_range_low.outputs[0], combine_range.inputs[0])
            links.new(in_range_high.outputs[0], combine_range.inputs[1])
            links.new(combine_range.outputs[0], invert_range.inputs[1])
            
            alpha_socket = invert_range.outputs[0]
            print(f"[TRANSPARENCY] RANGE nodes created: low={in_range_low}, high={in_range_high}, combine={combine_range}, invert={invert_range}")
            
        else:
            print(f"[TRANSPARENCY] Creating BOTH (RANGE + NAN) detection nodes")
            # NaN detection: compare value with itself
            is_nan_node = nodes.new(type='ShaderNodeMath')
            is_nan_node.operation = 'COMPARE'
            is_nan_node.location = (base_x + 200, base_y)
            is_nan_node.label = 'SCIBLEND_TRANSPARENCY_NAN_CHECK'
            is_nan_node.inputs[2].default_value = 0.0001  # epsilon for comparison
            
            in_range_low = nodes.new(type='ShaderNodeMath')
            in_range_low.operation = 'GREATER_THAN'
            in_range_low.location = (base_x + 200, base_y - 150)
            in_range_low.label = 'SCIBLEND_TRANSPARENCY_LOW'
            in_range_low.inputs[1].default_value = min_val
            
            in_range_high = nodes.new(type='ShaderNodeMath')
            in_range_high.operation = 'LESS_THAN'
            in_range_high.location = (base_x + 200, base_y - 250)
            in_range_high.label = 'SCIBLEND_TRANSPARENCY_HIGH'
            in_range_high.inputs[1].default_value = max_val
            
            combine_range = nodes.new(type='ShaderNodeMath')
            combine_range.operation = 'MULTIPLY'
            combine_range.location = (base_x + 400, base_y - 200)
            combine_range.label = 'SCIBLEND_TRANSPARENCY_COMBINE'
            
            combine_all = nodes.new(type='ShaderNodeMath')
            combine_all.operation = 'MULTIPLY'
            combine_all.location = (base_x + 600, base_y - 100)
            combine_all.label = 'SCIBLEND_TRANSPARENCY_FINAL'
            
            # Connect NaN check (value compared with itself)
            links.new(attrib_node.outputs[2], is_nan_node.inputs[0])
            links.new(attrib_node.outputs[2], is_nan_node.inputs[1])
            
            # Connect range check
            links.new(attrib_node.outputs[2], in_range_low.inputs[0])
            links.new(attrib_node.outputs[2], in_range_high.inputs[0])
            links.new(in_range_low.outputs[0], combine_range.inputs[0])
            links.new(in_range_high.outputs[0], combine_range.inputs[1])
            

            # Invert range result
            invert_range = nodes.new(type='ShaderNodeMath')
            invert_range.operation = 'SUBTRACT'
            invert_range.location = (base_x + 600, base_y - 200)
            invert_range.label = 'SCIBLEND_TRANSPARENCY_INVERT_RANGE'
            invert_range.inputs[0].default_value = 1.0
            links.new(combine_range.outputs[0], invert_range.inputs[1])
            
            # Multiply: opaque only if NOT NaN AND NOT in range
            links.new(is_nan_node.outputs[0], combine_all.inputs[0])
            links.new(invert_range.outputs[0], combine_all.inputs[1])
            
            alpha_socket = combine_all.outputs[0]
            print(f"[TRANSPARENCY] BOTH nodes created: nan={is_nan_node}, low={in_range_low}, high={in_range_high}, combine_range={combine_range}, invert_range={invert_range}, combine_all={combine_all}")
        
        if invert:
            print(f"[TRANSPARENCY] Creating invert node")
            invert_node = nodes.new(type='ShaderNodeMath')
            invert_node.operation = 'SUBTRACT'
            invert_node.location = (alpha_socket.node.location.x + 200, alpha_socket.node.location.y)
            invert_node.label = 'SCIBLEND_TRANSPARENCY_INVERT'
            invert_node.inputs[0].default_value = 1.0
            
            links.new(alpha_socket, invert_node.inputs[1])
            alpha_socket = invert_node.outputs[0]
        
        print(f"[TRANSPARENCY] Connecting alpha to BSDF")
        links.new(alpha_socket, bsdf_node.inputs['Alpha'])
        
        print(f"[TRANSPARENCY] Updating material node tree")
        material.node_tree.update_tag()
        
        print(f"[TRANSPARENCY] Success!")
        logger.info("Updated transparency for material %s", material.name)
        return True
        
    except Exception as e:
        print(f"[TRANSPARENCY] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        logger.error("Failed to update transparency: %s", e)
        return False

