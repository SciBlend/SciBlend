import bpy
import json
import os
import colorsys
from mathutils import Color
from bpy.props import (
    EnumProperty,
    StringProperty,
    BoolProperty,
    FloatVectorProperty,
    FloatProperty,
    CollectionProperty
)
from bpy.types import Operator, Panel, PropertyGroup
import numpy as np
from scipy import interpolate
import logging

# Configurar el logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_colormaps_from_json(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    colormaps = {}
    for colormap in data:
        name = colormap['Name']
        rgb_points = colormap['RGBPoints']
        colors = []
        for i in range(0, len(rgb_points), 4):
            position = rgb_points[i]
            r, g, b = rgb_points[i+1:i+4]
            colors.append({
                'position': position,
                'color': (r, g, b)
            })
        
        min_pos = min(color['position'] for color in colors)
        max_pos = max(color['position'] for color in colors)
        if min_pos != 0 or max_pos != 1:
            for color in colors:
                color['position'] = (color['position'] - min_pos) / (max_pos - min_pos)
        
        colormaps[name] = {
            'colors': colors,
            'nan_color': tuple(colormap.get('NanColor', (1, 1, 1))),
            'color_space': colormap.get('ColorSpace', 'RGB')
        }
    return colormaps

addon_directory = os.path.dirname(os.path.realpath(__file__))
colors_filepath = os.path.join(addon_directory, 'colors.json')
COLORMAPS = load_colormaps_from_json(colors_filepath)

def get_colormap_items(self, context):
    items = [(name, name, "") for name in COLORMAPS.keys()]
    if context.scene.custom_colorramp:
        items.append(("CUSTOM", "Custom", "Use custom ColorRamp"))
    return items

INTERPOLATION_OPTIONS = [
    ('CONSTANT', "Constant", "No interpolation"),
    ('LINEAR', "Linear", "Linear interpolation"),
    ('EASE', "Ease", "Easing interpolation"),
    ('CARDINAL', "Cardinal", "Cardinal interpolation"),
    ('B_SPLINE', "B-Spline", "B-Spline interpolation"),
]

class ColorRampColor(PropertyGroup):
    color: FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color of the ColorRamp stop"
    )
    position: FloatProperty(
        name="Position",
        default=0.5,
        min=0.0,
        max=1.0,
        description="Position of the color stop"
    )

class COLORRAMP_OT_add_color(Operator):
    bl_idname = "colorramp.add_color"
    bl_label = "Add Color"
    bl_description = "Add a new color to the custom ColorRamp"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        custom_ramp = context.scene.custom_colorramp
        new_color = custom_ramp.add()
        new_color.position = len(custom_ramp) / (len(custom_ramp) + 1)
        return {'FINISHED'}

class COLORRAMP_OT_remove_color(Operator):
    bl_idname = "colorramp.remove_color"
    bl_label = "Remove Color"
    bl_description = "Remove the last color from the custom ColorRamp"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        custom_ramp = context.scene.custom_colorramp
        if len(custom_ramp) > 2:
            custom_ramp.remove(len(custom_ramp) - 1)
        return {'FINISHED'}

class COLORRAMP_OT_save_custom(Operator):
    bl_idname = "colorramp.save_custom"
    bl_label = "Save Custom ColorRamp"
    bl_description = "Save the current custom ColorRamp"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        custom_ramp = context.scene.custom_colorramp
        data = [{"color": list(c.color) + [1.0], "position": c.position}
                for c in custom_ramp]
        with open(self.filepath, 'w') as f:
            json.dump(data, f)
        self.report({'INFO'}, f"ColorRamp saved to {self.filepath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = "custom_colorramp.json"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class COLORRAMP_OT_load_custom(Operator):
    bl_idname = "colorramp.load_custom"
    bl_label = "Load Custom ColorRamp"
    bl_description = "Load a custom ColorRamp"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        with open(self.filepath, 'r') as f:
            data = json.load(f)

        custom_ramp = context.scene.custom_colorramp
        custom_ramp.clear()
        for item in data:
            new_color = custom_ramp.add()
            new_color.color = item['color'][:3]
            new_color.position = item['position']

        self.report({'INFO'}, f"ColorRamp loaded from {self.filepath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class COLORRAMP_OT_import_json(Operator):
    bl_idname = "colorramp.import_json"
    bl_label = "Import JSON Colormaps"
    bl_description = "Import colormaps from a Paraview JSON file"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        description="Path to the JSON file",
        default="",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}

        try:
            new_colormaps = load_colormaps_from_json(self.filepath)
            COLORMAPS.update(new_colormaps)
            self.report({'INFO'}, f"Successfully imported {len(new_colormaps)} colormaps")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error importing colormaps: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def interpolate_colormap(colors, num_points=32):
    positions = [color['position'] for color in colors]
    rgb_colors = [color['color'] for color in colors]
    
    if positions[0] != 0:
        positions.insert(0, 0)
        rgb_colors.insert(0, rgb_colors[0])
    if positions[-1] != 1:
        positions.append(1)
        rgb_colors.append(rgb_colors[-1])
    
    r_interp = interpolate.interp1d(positions, [c[0] for c in rgb_colors], bounds_error=False, fill_value="extrapolate")
    g_interp = interpolate.interp1d(positions, [c[1] for c in rgb_colors], bounds_error=False, fill_value="extrapolate")
    b_interp = interpolate.interp1d(positions, [c[2] for c in rgb_colors], bounds_error=False, fill_value="extrapolate")
    
    new_positions = np.linspace(0, 1, num_points)
    
    new_colors = []
    for pos in new_positions:
        new_colors.append({
            'position': pos,
            'color': (float(r_interp(pos)), float(g_interp(pos)), float(b_interp(pos)))
        })
    
    return new_colors

def get_color_range(obj, attribute_name, normalization='AUTO'):
    if normalization == 'GLOBAL':
        # Buscar el atributo en todos los objetos de la escena
        all_values = []
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and attribute_name in obj.data.attributes:
                attribute = obj.data.attributes[attribute_name]
                if attribute.data_type == 'FLOAT':
                    values = [data.value for data in attribute.data]
                    all_values.extend(values)
                elif attribute.data_type == 'FLOAT_VECTOR':
                    values = [data.vector.length for data in attribute.data]
                    all_values.extend(values)
        
        if all_values:
            return (min(all_values), max(all_values))
        return (0, 1)
    
    # Comportamiento original para AUTO y NONE
    if obj.type != 'MESH' or attribute_name not in obj.data.attributes:
        return (0, 1)
    
    attribute = obj.data.attributes[attribute_name]
    if attribute.data_type == 'FLOAT':
        values = [data.value for data in attribute.data]
    elif attribute.data_type == 'FLOAT_VECTOR':
        values = [data.vector.length for data in attribute.data]
    else:
        return (0, 1)
    
    return (min(values), max(values))

def create_colormap_material(colormap_name, interpolation, gamma, custom_colormap=None, color_range=None, normalization='AUTO', attribute_name="Col"):
    logger.info("Creando material con colormap: %s", colormap_name)
    
    mat = bpy.data.materials.new(name=f"Shader_Generator_{colormap_name}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    node_attrib = nodes.new(type='ShaderNodeAttribute')
    node_attrib.attribute_name = attribute_name
    node_attrib.location = (-600, 0)

    map_range = nodes.new(type='ShaderNodeMapRange')
    map_range.location = (-400, 0)

    if color_range and normalization != 'NONE':
        min_value, max_value = color_range
        if normalization == 'AUTO' or normalization == 'GLOBAL':
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
        elem.color = color_data['color'] + (1.0,)  # Añadir alpha = 1.0


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

    logger.info("Material creado y nodos conectados")
    return mat

class MATERIAL_OT_create_shader(Operator):
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
        items=INTERPOLATION_OPTIONS,
        default='CONSTANT'
    )

    gamma: FloatProperty(
        name="Gamma",
        description="Adjust the gamma value",
        default=2.2,
        min=0.1,
        max=5.0
    )

    material_name: StringProperty(
        name="Material Name",
        description="Name of the new material",
        default="New Shader"
    )

    apply_to_all: BoolProperty(
        name="Apply to All",
        description="Apply the shader to all mesh objects in the scene",
        default=False
    )

    normalization: EnumProperty(
        name="Normalization",
        description="Choose the normalization method",
        items=[
            ('AUTO', "Auto Per Channel", "Normalize each color channel separately"),
            ('GLOBAL', "Global", "Use global min and max for all channels"),
            ('NONE', "None", "Don't normalize"),
        ],
        default='AUTO'
    )

    attribute_name: StringProperty(
        name="Attribute Name",
        description="Name of the attribute to map",
        default="Col"
    )

    def execute(self, context):
        active_obj = context.active_object
        if active_obj and active_obj.type == 'MESH':
            color_range = get_color_range(active_obj, self.attribute_name, self.normalization)
        else:
            color_range = None

        custom_colormap = None
        if self.colormap == "CUSTOM" and context.scene.custom_colorramp:
            custom_colormap = [{"position": color.position, "color": color.color[:3]} for color in context.scene.custom_colorramp]

        mat = create_colormap_material(
            self.colormap,
            self.interpolation,
            self.gamma,
            custom_colormap,
            color_range=color_range,
            normalization=self.normalization,
            attribute_name=self.attribute_name
        )

        mat.name = self.material_name

        if self.apply_to_all:
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    if obj.data.materials:
                        obj.data.materials[0] = mat
                    else:
                        obj.data.materials.append(mat)
                    
                    if obj.modifiers:
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
                if obj.type == 'MESH':
                    if obj.data.materials:
                        obj.data.materials[0] = mat
                    else:
                        obj.data.materials.append(mat)
                    
                    if obj.modifiers:
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

        self.report({'INFO'}, f"Applied shader with {self.colormap} colormap, {self.interpolation} interpolation, and gamma {self.gamma} to {'all mesh objects' if self.apply_to_all else 'selected objects'}")
        logger.info("Shader aplicado exitosamente")
        return {'FINISHED'}

class MATERIAL_PT_shader_generator(Panel):
    bl_label = "Shader Generator"
    bl_idname = "MATERIAL_PT_shader_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Shader Generator'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Import Colormaps", icon='IMPORT')
        layout.operator(COLORRAMP_OT_import_json.bl_idname, text="Import Scientific Colormaps", icon='FILE_NEW')

        layout.separator()

        layout.label(text="Create Shader", icon='NODE_MATERIAL')
        box = layout.box()
        col = box.column(align=True)

        op = col.operator(MATERIAL_OT_create_shader.bl_idname,
                          text="Generate Shader", icon='MATERIAL')
        col.prop(op, "colormap", text="Colormap")
        col.prop(op, "interpolation", text="Interpolation")
        col.prop(op, "gamma", text="Gamma")
        col.prop(op, "material_name", text="Material Name")
        col.prop(op, "apply_to_all", text="Apply to All")
        col.prop(op, "normalization", text="Normalization")
        col.prop(op, "attribute_name", text="Attribute Name")

        layout.separator()

        layout.label(text="Custom ColorRamp", icon='COLOR')
        box = layout.box()
        row = box.row(align=True)
        row.operator(COLORRAMP_OT_add_color.bl_idname,
                     text="Add Color", icon='ADD')
        row.operator(COLORRAMP_OT_remove_color.bl_idname,
                     text="Remove Color", icon='REMOVE')

        for i, color in enumerate(scene.custom_colorramp):
            row = box.row(align=True)
            row.prop(color, "color", text=f"Color {i+1}")
            row.prop(color, "position", text="Pos")

        layout.separator()

        layout.label(text="Save/Load ColorRamp", icon='FILE_FOLDER')
        box = layout.box()
        box.operator(COLORRAMP_OT_save_custom.bl_idname,
                     text="Save ColorRamp", icon='FILE_TICK')
        box.operator(COLORRAMP_OT_load_custom.bl_idname,
                     text="Load ColorRamp", icon='IMPORT')

def register():
    bpy.utils.register_class(ColorRampColor)
    bpy.types.Scene.custom_colorramp = CollectionProperty(type=ColorRampColor)
    bpy.utils.register_class(COLORRAMP_OT_add_color)
    bpy.utils.register_class(COLORRAMP_OT_remove_color)
    bpy.utils.register_class(COLORRAMP_OT_save_custom)
    bpy.utils.register_class(COLORRAMP_OT_load_custom)
    bpy.utils.register_class(COLORRAMP_OT_import_json)
    bpy.utils.register_class(MATERIAL_OT_create_shader)
    bpy.utils.register_class(MATERIAL_PT_shader_generator)

def unregister():
    del bpy.types.Scene.custom_colorramp
    bpy.utils.unregister_class(ColorRampColor)
    bpy.utils.unregister_class(COLORRAMP_OT_add_color)
    bpy.utils.unregister_class(COLORRAMP_OT_remove_color)
    bpy.utils.unregister_class(COLORRAMP_OT_save_custom)
    bpy.utils.unregister_class(COLORRAMP_OT_load_custom)
    bpy.utils.unregister_class(COLORRAMP_OT_import_json)
    bpy.utils.unregister_class(MATERIAL_OT_create_shader)
    bpy.utils.unregister_class(MATERIAL_PT_shader_generator)

if __name__ == "__main__":
    register()
