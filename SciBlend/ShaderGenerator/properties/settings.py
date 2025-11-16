import bpy
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, EnumProperty, IntProperty, CollectionProperty, BoolProperty
from .collection_shader_item import CollectionShaderItem

_loading_material_settings = False


def _get_active_collection_material(context):
    """Get the material from the currently selected collection.
    
    Parameters
    ----------
    context : bpy.types.Context
        Blender context.
        
    Returns
    -------
    bpy.types.Material or None
        The material if found.
    """
    settings = context.scene.shader_generator_settings
    if not settings or not settings.collection_shaders:
        return None
        
    if settings.active_collection_index < 0 or settings.active_collection_index >= len(settings.collection_shaders):
        return None
        
    item = settings.collection_shaders[settings.active_collection_index]
    if not item.material_name:
        return None
        
    return bpy.data.materials.get(item.material_name)


def _update_map_range_from_min(self, context):
    """Update the 'From Min' input of the Shader Generator Map Range node."""
    global _loading_material_settings
    if _loading_material_settings:
        return
        
    mat = _get_active_collection_material(context)
    if not mat:
        return
        
    from ..utils.nodes import find_shader_map_range_node
    node = find_shader_map_range_node(mat)
    try:
        if node and 'From Min' in node.inputs:
            node.inputs['From Min'].default_value = float(self.from_min)
            if mat.node_tree:
                mat.node_tree.update_tag()
    except Exception:
        pass


def _update_map_range_from_max(self, context):
    """Update the 'From Max' input of the Shader Generator Map Range node."""
    global _loading_material_settings
    if _loading_material_settings:
        return
        
    mat = _get_active_collection_material(context)
    if not mat:
        return
        
    from ..utils.nodes import find_shader_map_range_node
    node = find_shader_map_range_node(mat)
    try:
        if node and 'From Max' in node.inputs:
            node.inputs['From Max'].default_value = float(self.from_max)
            if mat.node_tree:
                mat.node_tree.update_tag()
    except Exception:
        pass


def _update_colormap(self, context):
    """Update the colormap of the active collection's material."""
    global _loading_material_settings
    if _loading_material_settings:
        return
        
    mat = _get_active_collection_material(context)
    if not mat:
        return
        
    from ..utils.material_updater import update_material_colormap
    
    custom_colormap = None
    if self.colormap == "CUSTOM":
        scene = context.scene
        if hasattr(scene, 'custom_colorramp') and scene.custom_colorramp:
            custom_colormap = [
                {"position": color.position, "color": color.color[:3]} 
                for color in scene.custom_colorramp
            ]
    
    try:
        update_material_colormap(mat, self.colormap, custom_colormap)
    except Exception:
        pass


def _update_interpolation(self, context):
    """Update the interpolation of the active collection's material."""
    global _loading_material_settings
    if _loading_material_settings:
        return
        
    mat = _get_active_collection_material(context)
    if not mat:
        return
        
    from ..utils.material_updater import update_material_interpolation
    try:
        update_material_interpolation(mat, self.interpolation)
    except Exception:
        pass


def _update_gamma(self, context):
    """Update the gamma of the active collection's material."""
    global _loading_material_settings
    if _loading_material_settings:
        return
        
    mat = _get_active_collection_material(context)
    if not mat:
        return
        
    from ..utils.material_updater import update_material_gamma
    try:
        update_material_gamma(mat, self.gamma)
    except Exception:
        pass


def _update_attribute_name(self, context):
    """Update the attribute name of the active collection's material."""
    global _loading_material_settings
    if _loading_material_settings:
        return
        
    mat = _get_active_collection_material(context)
    if not mat:
        return
        
    from ..utils.material_updater import update_material_attribute
    try:
        update_material_attribute(mat, self.attribute_name)
    except Exception:
        pass


def _update_normalization(self, context):
    """Update the normalization of the active collection's material."""
    global _loading_material_settings
    if _loading_material_settings:
        return
        
    mat = _get_active_collection_material(context)
    if not mat:
        return
        
    from ..utils.material_updater import update_material_normalization
    from ..utils.attributes import get_color_range
    
    settings = context.scene.shader_generator_settings
    if not settings or not settings.collection_shaders:
        return
        
    if settings.active_collection_index < 0 or settings.active_collection_index >= len(settings.collection_shaders):
        return
        
    item = settings.collection_shaders[settings.active_collection_index]
    coll = bpy.data.collections.get(item.collection_name)
    
    color_range = None
    if coll and coll.objects:
        for obj in coll.objects:
            if obj.type == 'MESH':
                try:
                    color_range = get_color_range(obj, self.attribute_name, self.normalization)
                    break
                except Exception:
                    pass
    
    try:
        update_material_normalization(mat, self.normalization, color_range)
        
        from ..utils.nodes import find_shader_map_range_node
        map_range = find_shader_map_range_node(mat)
        if map_range:
            self.from_min = map_range.inputs['From Min'].default_value
            self.from_max = map_range.inputs['From Max'].default_value
    except Exception:
        pass


def _on_collection_index_changed(self, context):
    """Called when the active collection changes. Selects first object and loads shader settings."""
    global _loading_material_settings
    
    settings = context.scene.shader_generator_settings
    if not settings or not settings.collection_shaders:
        return
        
    if settings.active_collection_index < 0 or settings.active_collection_index >= len(settings.collection_shaders):
        return
        
    item = settings.collection_shaders[settings.active_collection_index]
    coll = bpy.data.collections.get(item.collection_name)
    
    if not coll:
        return
    
    if coll.objects:
        first_obj = None
        for obj in coll.objects:
            if obj.type == 'MESH':
                first_obj = obj
                break
        
        if first_obj:
            try:
                bpy.ops.object.select_all(action='DESELECT')
                first_obj.select_set(True)
                context.view_layer.objects.active = first_obj
            except Exception:
                pass
    
    if not item.material_name:
        return
        
    mat = bpy.data.materials.get(item.material_name)
    if not mat or mat.get('sciblend_colormap') is None:
        return
    
    from ..utils.material_updater import load_settings_from_material
    mat_settings = load_settings_from_material(mat)
    
    if mat_settings:
        _loading_material_settings = True
        try:
            settings.colormap = mat_settings.get('colormap', 'viridis')
        except Exception:
            pass
        try:
            settings.interpolation = mat_settings.get('interpolation', 'CONSTANT')
        except Exception:
            pass
        try:
            settings.gamma = mat_settings.get('gamma', 2.2)
        except Exception:
            pass
        try:
            settings.attribute_name = mat_settings.get('attribute', 'Col')
        except Exception:
            pass
        try:
            settings.normalization = mat_settings.get('normalization', 'AUTO')
        except Exception:
            pass
        try:
            settings.from_min = mat_settings.get('from_min', 0.0)
            settings.from_max = mat_settings.get('from_max', 1.0)
        except Exception:
            pass
        finally:
            _loading_material_settings = False


class ShaderGeneratorSettings(PropertyGroup):
    """Settings for Shader Generator with real-time update callbacks."""
    
    active_collection_index: IntProperty(
        name="Active Collection",
        description="Index of the active collection in the list",
        default=-1,
        update=_on_collection_index_changed,
    )
    
    from_min: FloatProperty(
        name="From Min",
        description="Input range minimum for Map Range",
        default=0.0,
        update=_update_map_range_from_min,
    )
    
    from_max: FloatProperty(
        name="From Max",
        description="Input range maximum for Map Range",
        default=1.0,
        update=_update_map_range_from_max,
    )
    
    colormap: EnumProperty(
        name="Colormap",
        description="Choose the colormap",
        items=lambda self, context: _get_colormap_items_callback(self, context),
        update=_update_colormap,
    )
    
    interpolation: EnumProperty(
        name="Interpolation",
        description="Choose the interpolation method",
        items=[
            ('CONSTANT', "Constant", "No interpolation"),
            ('LINEAR', "Linear", "Linear interpolation"),
            ('EASE', "Ease", "Easing interpolation"),
            ('CARDINAL', "Cardinal", "Cardinal interpolation"),
            ('B_SPLINE', "B-Spline", "B-Spline interpolation"),
        ],
        default='CONSTANT',
        update=_update_interpolation,
    )
    
    gamma: FloatProperty(
        name="Gamma",
        description="Adjust the gamma value",
        default=2.2,
        min=0.1,
        max=5.0,
        update=_update_gamma,
    )
    
    attribute_name: EnumProperty(
        name="Attribute Name",
        description="Choose the attribute to map",
        items=lambda self, context: _get_attribute_items_callback(self, context),
        update=_update_attribute_name,
    )
    
    normalization: EnumProperty(
        name="Normalization",
        description="Choose the normalization method",
        items=[
            ('AUTO', "Auto Per Channel", "Normalize each color channel separately"),
            ('GLOBAL', "Global", "Use global min and max for all channels"),
            ('NONE', "None", "Don't normalize"),
        ],
        default='AUTO',
        update=_update_normalization,
    )


def _get_colormap_items_callback(self, context):
    """Get colormap items for the enum property.
    
    Parameters
    ----------
    self : ShaderGeneratorSettings
        The settings object.
    context : bpy.types.Context
        Blender context.
        
    Returns
    -------
    list
        List of enum items.
    """
    from ..utils.colormaps import get_colormap_items
    return get_colormap_items(self, context)


def _get_attribute_items_callback(self, context):
    """Get attribute items for the enum property.
    
    Parameters
    ----------
    self : ShaderGeneratorSettings
        The settings object.
    context : bpy.types.Context
        Blender context.
        
    Returns
    -------
    list
        List of enum items.
    """
    from ..utils.attributes import get_attribute_items
    return get_attribute_items(self, context) 