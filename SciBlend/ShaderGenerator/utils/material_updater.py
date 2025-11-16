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
        Dictionary with keys: colormap, attribute, normalization, interpolation, gamma, from_min, from_max.
    """
    if not material:
        return None
        
    settings = {}
    
    settings['colormap'] = material.get('sciblend_colormap', 'viridis')
    settings['attribute'] = material.get('sciblend_attribute', 'Col')
    settings['normalization'] = material.get('sciblend_normalization', 'AUTO')
    
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

