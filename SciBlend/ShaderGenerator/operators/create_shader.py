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


class MATERIAL_OT_create_shader(Operator):
    """Create a colormap-based material and apply it to selected or all mesh objects."""
    bl_idname = "material.create_shader"
    bl_label = "Create and Apply Shader"
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
        """Create the material, assign to objects, and trigger legend updates if enabled."""
        active_obj = context.active_object
        try:
            selected_attr = getattr(self, 'attribute_name', None)
        except Exception:
            selected_attr = None
        if not selected_attr:
            items = get_attribute_items(self, context)
            selected_attr = items[0][0] if items else "Col"
        if active_obj and getattr(active_obj, 'type', None) == 'MESH':
            color_range = get_color_range(active_obj, selected_attr, self.normalization)
        else:
            color_range = None

        custom_colormap = None
        if self.colormap == "CUSTOM" and getattr(getattr(context, 'scene', None), 'custom_colorramp', None):
            custom_colormap = [{"position": color.position, "color": color.color[:3]} for color in context.scene.custom_colorramp]

        mat = create_colormap_material(
            self.colormap,
            self.interpolation,
            self.gamma,
            custom_colormap,
            color_range=color_range,
            normalization=self.normalization,
            attribute_name=selected_attr,
        )

        mat.name = self.material_name

        if self.apply_to_all:
            for obj in bpy.data.objects:
                if getattr(obj, 'type', None) == 'MESH':
                    if getattr(getattr(obj, 'data', None), 'materials', None):
                        obj.data.materials[0] = mat
                    else:
                        obj.data.materials.append(mat)

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
        else:
            for obj in context.selected_objects:
                if getattr(obj, 'type', None) == 'MESH':
                    if getattr(getattr(obj, 'data', None), 'materials', None):
                        obj.data.materials[0] = mat
                    else:
                        obj.data.materials.append(mat)

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

        try:
            scene = context.scene
            try:
                from ..properties.settings import ShaderGeneratorSettings
                if not hasattr(bpy.types.Scene, 'shader_generator_settings'):
                    bpy.types.Scene.shader_generator_settings = bpy.props.PointerProperty(type=ShaderGeneratorSettings)
                settings = context.scene.shader_generator_settings
                map_range = None
                try:
                    from ..utils.nodes import find_shader_map_range_node
                    map_range = find_shader_map_range_node(mat)
                except Exception:
                    map_range = None
                if map_range and 'From Min' in map_range.inputs and 'From Max' in map_range.inputs:
                    settings.from_min = float(map_range.inputs['From Min'].default_value)
                    settings.from_max = float(map_range.inputs['From Max'].default_value)
            except Exception:
                pass

            settings = getattr(scene, 'legend_settings', None)
            if settings and getattr(settings, 'auto_from_shader', False):
                try:
                    from ...LegendGenerator.operators.choose_shader import update_legend_from_shader
                    obj = context.active_object
                    update_legend_from_shader(scene, obj)
                except Exception:
                    pass
                try:
                    if getattr(settings, 'legend_enabled', True):
                        bpy.ops.compositor.png_overlay()
                except Exception:
                    pass
        except Exception:
            pass

        self.report({'INFO'}, f"Applied shader with {self.colormap} colormap, {self.interpolation} interpolation, and gamma {self.gamma} to {'all mesh objects' if self.apply_to_all else 'selected objects'}")
        logger.info("Shader applied successfully")
        return {'FINISHED'} 