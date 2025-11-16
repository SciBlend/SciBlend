import bpy
import logging
from bpy.types import Operator
from bpy.props import EnumProperty, StringProperty, BoolProperty, FloatProperty
from ..utils.colormaps import COLORMAPS, interpolate_colormap, get_colormap_items
from ..utils.attributes import get_color_range, get_attribute_items

logger = logging.getLogger(__name__)


def create_colormap_material(colormap_name, interpolation, gamma, custom_colormap=None, color_range=None, normalization='AUTO', attribute_name="Col"):
    """Create a Blender material that maps a mesh attribute through a ColorRamp to Base Color.

    Parameters
    ----------
    colormap_name : str
        Name of the colormap or 'CUSTOM'.
    interpolation : str
        Interpolation type for the ColorRamp.
    gamma : float
        Gamma value to apply after the ColorRamp.
    custom_colormap : list[dict] | None
        When colormap_name is 'CUSTOM', the list of color stops.
    color_range : tuple[float, float] | None
        Explicit value range for Map Range. Ignored if normalization is 'NONE'.
    normalization : str
        One of 'AUTO', 'GLOBAL', 'NONE'.
    attribute_name : str
        Name of the mesh attribute to map from.

    Returns
    -------
    bpy.types.Material
        The created material with the node tree configured.
    """
    logger.info("Creating material with colormap: %s", colormap_name)

    mat = bpy.data.materials.new(name=f"Shader_Generator_{colormap_name}")
    mat.use_nodes = True
    try:
        mat["sciblend_colormap"] = colormap_name
        mat["sciblend_attribute"] = attribute_name
        mat["sciblend_normalization"] = normalization
    except Exception:
        pass

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    node_attrib = nodes.new(type='ShaderNodeAttribute')
    node_attrib.attribute_name = attribute_name
    node_attrib.location = (-600, 0)

    map_range = nodes.new(type='ShaderNodeMapRange')
    map_range.location = (-400, 0)
    try:
        map_range.label = 'SCIBLEND_MAP_RANGE'
        map_range["sciblend_map_range"] = True
    except Exception:
        pass

    if color_range and normalization != 'NONE':
        min_value, max_value = color_range
        if normalization in {'AUTO', 'GLOBAL'}:
            map_range.inputs['From Min'].default_value = min_value
            map_range.inputs['From Max'].default_value = max_value
    else:
        map_range.inputs['From Min'].default_value = 0.0
        map_range.inputs['From Max'].default_value = 1.0

    map_range.inputs['To Min'].default_value = 0.0
    map_range.inputs['To Max'].default_value = 1.0
    map_range.clamp = True

    node_colorramp = nodes.new(type='ShaderNodeValToRGB')
    node_colorramp.location = (-200, 0)
    node_colorramp.color_ramp.interpolation = interpolation
    try:
        node_colorramp.label = str(colormap_name)
    except Exception:
        pass

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

    node_gamma = nodes.new(type='ShaderNodeGamma')
    node_gamma.inputs[1].default_value = gamma
    node_gamma.location = (0, 0)

    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_bsdf.location = (200, 0)

    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_output.location = (400, 0)

    links.new(node_attrib.outputs[0], map_range.inputs[0])
    links.new(map_range.outputs[0], node_colorramp.inputs[0])
    links.new(node_colorramp.outputs[0], node_gamma.inputs[0])
    links.new(node_gamma.outputs[0], node_bsdf.inputs['Base Color'])
    links.new(node_bsdf.outputs[0], node_output.inputs[0])

    logger.info("Material created and nodes connected")
    return mat


def _get_collection_items(self, context):
    """Return available collections as EnumProperty items for the operator UI."""
    items = [("", "None", "No collection override")]
    try:
        for coll in bpy.data.collections:
            items.append((coll.name, coll.name, coll.name))
    except Exception:
        pass
    return items


class MATERIAL_OT_create_shader(Operator):
    """Create or update a colormap-based material for the selected collection."""
    bl_idname = "material.create_shader"
    bl_label = "Create/Update Shader"
    bl_options = {'REGISTER', 'UNDO'}

    colormap: EnumProperty(
        name="Colormap",
        description="Choose the colormap or use custom",
        items=get_colormap_items,
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
    )

    gamma: FloatProperty(
        name="Gamma",
        description="Adjust the gamma value",
        default=2.2,
        min=0.1,
        max=5.0,
    )

    material_name: StringProperty(
        name="Material Name",
        description="Name of the new material",
        default="New Shader",
    )

    apply_to_all: BoolProperty(
        name="Apply to All",
        description="Apply the shader to all mesh objects in the scene",
        default=False,
    )

    target_collection: EnumProperty(
        name="Target Collection",
        description="Apply the shader to all mesh objects in the chosen collection",
        items=_get_collection_items,
        options={'SKIP_SAVE'},
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
    )

    attribute_name: EnumProperty(
        name="Attribute Name",
        description="Choose the attribute to map",
        items=get_attribute_items,
    )

    def execute(self, context):
        """Create or update the material for the selected collection."""
        settings = context.scene.shader_generator_settings
        if not settings:
            self.report({'ERROR'}, "Shader Generator settings not found")
            return {'CANCELLED'}
            
        if settings.active_collection_index < 0 or settings.active_collection_index >= len(settings.collection_shaders):
            self.report({'ERROR'}, "No collection selected")
            return {'CANCELLED'}
            
        item = settings.collection_shaders[settings.active_collection_index]
        coll = bpy.data.collections.get(item.collection_name)
        
        if not coll:
            self.report({'ERROR'}, f"Collection '{item.collection_name}' not found")
            return {'CANCELLED'}
            
        try:
            selected_attr = settings.attribute_name
        except Exception:
            items = get_attribute_items(self, context)
            selected_attr = items[0][0] if items else "Col"
            
        color_range = None
        for obj in coll.objects:
            if obj.type == 'MESH':
                try:
                    color_range = get_color_range(obj, selected_attr, settings.normalization)
                    break
                except Exception:
                    pass

        custom_colormap = None
        if settings.colormap == "CUSTOM":
            scene = context.scene
            if hasattr(scene, 'custom_colorramp') and scene.custom_colorramp:
                custom_colormap = [
                    {"position": color.position, "color": color.color[:3]} 
                    for color in scene.custom_colorramp
                ]

        existing_mat = None
        if item.material_name:
            existing_mat = bpy.data.materials.get(item.material_name)
            
        if existing_mat and existing_mat.get('sciblend_colormap') is not None:
            mat = existing_mat
            logger.info("Updating existing material: %s", mat.name)
            
            from ..utils.material_updater import (
                update_material_colormap,
                update_material_interpolation,
                update_material_gamma,
                update_material_attribute,
                update_material_normalization,
                update_material_transparency,
            )
            
            update_material_colormap(mat, settings.colormap, custom_colormap)
            update_material_interpolation(mat, settings.interpolation)
            update_material_gamma(mat, settings.gamma)
            update_material_attribute(mat, selected_attr)
            update_material_normalization(mat, settings.normalization, color_range)
            update_material_transparency(
                mat,
                settings.enable_transparency,
                settings.transparency_mode,
                settings.transparency_min,
                settings.transparency_max,
                settings.invert_transparency
            )
            
            action = "Updated"
        else:
            mat = create_colormap_material(
                settings.colormap,
                settings.interpolation,
                settings.gamma,
                custom_colormap,
                color_range=color_range,
                normalization=settings.normalization,
                attribute_name=selected_attr,
            )
            
            mat.name = f"Shader_{item.collection_name}"
            
            from ..utils.material_updater import update_material_transparency
            update_material_transparency(
                mat,
                settings.enable_transparency,
                settings.transparency_mode,
                settings.transparency_min,
                settings.transparency_max,
                settings.invert_transparency
            )
            
            item.material_name = mat.name
            item.is_shader_generator = True
            
            action = "Created"
            logger.info("Created new material: %s", mat.name)

        def _apply_to_objects(objects):
            """Assign the material and update any Set Material nodes for each mesh object in 'objects'."""
            for obj in objects:
                if getattr(obj, 'type', None) != 'MESH':
                    continue
                if getattr(getattr(obj, 'data', None), 'materials', None):
                    if len(obj.data.materials) > 0:
                        obj.data.materials[0] = mat
                    else:
                        obj.data.materials.append(mat)
                else:
                    try:
                        obj.data.materials.append(mat)
                    except Exception:
                        continue
                if getattr(obj, 'modifiers', None):
                    for modifier in obj.modifiers:
                        if modifier.type == 'NODES' and modifier.node_group:
                            def update_set_material_nodes(node_group):
                                for node in node_group.nodes:
                                    if node.type == 'SET_MATERIAL':
                                        if mat not in obj.data.materials[:]:
                                            obj.data.materials.append(mat)
                                        if hasattr(node, 'inputs') and 'Material' in node.inputs:
                                            node.inputs['Material'].default_value = mat
                                        elif hasattr(node, 'material_index'):
                                            node.material_index = obj.data.materials.find(mat.name)
                                    elif node.type == 'GROUP' and node.node_tree:
                                        update_set_material_nodes(node.node_tree)
                            update_set_material_nodes(modifier.node_group)

        _apply_to_objects(list(coll.objects))

        try:
            from ..utils.nodes import find_shader_map_range_node
            map_range = find_shader_map_range_node(mat)
            if map_range and 'From Min' in map_range.inputs and 'From Max' in map_range.inputs:
                settings.from_min = float(map_range.inputs['From Min'].default_value)
                settings.from_max = float(map_range.inputs['From Max'].default_value)
        except Exception:
            pass

        try:
            legend_settings = getattr(context.scene, 'legend_settings', None)
            if legend_settings and getattr(legend_settings, 'auto_from_shader', False):
                try:
                    from ...LegendGenerator.operators.choose_shader import update_legend_from_shader
                    obj = context.active_object
                    update_legend_from_shader(context.scene, obj)
                except Exception:
                    pass
                try:
                    if getattr(legend_settings, 'legend_enabled', True):
                        bpy.ops.compositor.png_overlay()
                except Exception:
                    pass
        except Exception:
            pass

        self.report({'INFO'}, f"{action} shader for collection '{item.collection_name}'")
        logger.info("%s shader for collection %s", action, item.collection_name)
        return {'FINISHED'} 