import bpy

class UpdateTextSizeOperator(bpy.types.Operator):
    bl_idname = "object.update_text_size"
    bl_label = "Update Text Size"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        grid_settings = scene.grid_settings
        scale_factor = {
            'nm': 1e-9,
            'µm': 1e-6,
            'mm': 0.001,
            'cm': 0.01,
            'dm': 0.1,
            'm': 1,
            'dam': 10,
            'hm': 100,
            'km': 1000
        }.get(grid_settings.unit_measure, 1)
        adjusted_text_size = grid_settings.base_text_size * scale_factor

        for obj in bpy.context.scene.objects:
            if obj.type == 'FONT':
                obj.scale = (adjusted_text_size,) * 3

        return {'FINISHED'}

class UpdateEdgeSizeOperator(bpy.types.Operator):
    bl_idname = "object.update_edge_size"
    bl_label = "Update Edge Size"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        grid_settings = scene.grid_settings
        scale_factor = {
            'nm': 1e-9,
            'µm': 1e-6,
            'mm': 0.001,
            'cm': 0.01,
            'dm': 0.1,
            'm': 1,
            'dam': 10,
            'hm': 100,
            'km': 1000
        }.get(grid_settings.unit_measure, 1)
        adjusted_edge_size = grid_settings.base_edge_size * scale_factor

        for obj in bpy.context.scene.objects:
            if obj.type == 'CURVE' and obj.name.startswith("EdgeObj_"):
                obj.data.bevel_depth = adjusted_edge_size

        return {'FINISHED'}

class ApplyEmissiveMaterialOperator(bpy.types.Operator):
    bl_idname = "object.apply_emissive_material"
    bl_label = "Apply Emissive Material"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        grid_settings = scene.grid_settings

        # Create a new emissive material
        mat = bpy.data.materials.new(name="Emissive Material")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear existing nodes
        nodes.clear()

        # Create necessary nodes
        node_emission = nodes.new(type='ShaderNodeEmission')
        node_output = nodes.new(type='ShaderNodeOutputMaterial')

        # Configure emission node
        node_emission.inputs['Color'].default_value = grid_settings.emission_color
        node_emission.inputs['Strength'].default_value = grid_settings.emission_strength

        # Connect nodes
        links.new(node_emission.outputs['Emission'], node_output.inputs['Surface'])

        # Apply material to edges and numbers
        for obj in bpy.context.scene.objects:
            if obj.type in ['CURVE', 'FONT']:
                if obj.data.materials:
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)

        return {'FINISHED'}

class ResizeSceneOperator(bpy.types.Operator):
    bl_idname = "object.resize_scene"
    bl_label = "Resize Scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        grid_settings = scene.grid_settings

        scale_factor = {
            'nm': 1e-9,
            'µm': 1e-6,
            'mm': 0.001,
            'cm': 0.01,
            'dm': 0.1,
            'm': 1,
            'dam': 10,
            'hm': 100,
            'km': 1000
        }.get(grid_settings.unit_measure, 1)

        target_scale_factor = {
            'nm': 1e-9,
            'µm': 1e-6,
            'mm': 0.001,
            'cm': 0.01,
            'dm': 0.1,
            'm': 1,
            'dam': 10,
            'hm': 100,
            'km': 1000
        }.get(grid_settings.target_unit_measure, 1)

        # Calculate the scale factor between current and target units
        relative_scale = target_scale_factor / scale_factor

        # Update the scene unit scale
        scene.unit_settings.scale_length = grid_settings.unit_scale * relative_scale

        # Update the scene unit system
        if grid_settings.target_unit_measure in ['mm', 'cm', 'dm', 'm']:
            scene.unit_settings.system = 'METRIC'
            scene.unit_settings.length_unit = grid_settings.target_unit_measure.upper()
        elif grid_settings.target_unit_measure in ['nm', 'µm']:
            scene.unit_settings.system = 'METRIC'
            scene.unit_settings.length_unit = 'MICROMETERS'
        elif grid_settings.target_unit_measure in ['dam', 'hm', 'km']:
            scene.unit_settings.system = 'METRIC'
            scene.unit_settings.length_unit = 'KILOMETERS'

        # Scale all objects in the scene
        for obj in bpy.context.scene.objects:
            obj.scale *= relative_scale

        # Update grid settings
        grid_settings.unit_measure = grid_settings.target_unit_measure
        grid_settings.distance_x *= relative_scale
        grid_settings.distance_y *= relative_scale
        grid_settings.distance_z *= relative_scale
        grid_settings.base_text_size *= relative_scale
        grid_settings.base_edge_size *= relative_scale

        self.report({'INFO'}, f"Scene resized to {grid_settings.target_unit_measure}")
        return {'FINISHED'}