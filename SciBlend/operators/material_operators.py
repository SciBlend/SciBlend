import bpy

class CreateSharedMaterialOperator(bpy.types.Operator):
    bl_idname = "import_x3d.create_shared_material"
    bl_label = "New Global Material"

    def execute(self, context):
        material = bpy.data.materials.new(name="SharedMaterial")
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        for node in nodes:
            nodes.remove(node)

        attribute_node = nodes.new(type='ShaderNodeAttribute')
        attribute_node.attribute_name = 'Col'

        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')

        material_output = nodes.new(type='ShaderNodeOutputMaterial')

        links.new(attribute_node.outputs['Color'], bsdf.inputs['Base Color'])
        links.new(bsdf.outputs['BSDF'], material_output.inputs['Surface'])

        context.scene.x3d_import_settings.shared_material = material

        self.report({'INFO'}, "Shared material created and assigned.")
        return {'FINISHED'}


class ApplySharedMaterialOperator(bpy.types.Operator):
    bl_idname = "import_x3d.apply_shared_material"
    bl_label = "Apply Shared Material"

    def execute(self, context):
        material = context.scene.x3d_import_settings.shared_material
        if material is None:
            self.report({'ERROR'}, "No material selected.")
            return {'CANCELLED'}

        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.data.materials.clear()
                obj.data.materials.append(material)

        self.report({'INFO'}, "Material applied to all meshes.")
        return {'FINISHED'}


class RemoveAllShadersOperator(bpy.types.Operator):
    bl_idname = "import_x3d.remove_all_shaders"
    bl_label = "Remove All Shaders"

    def execute(self, context):
        for material in bpy.data.materials:
            bpy.data.materials.remove(material)

        self.report({'INFO'}, "All shaders removed.")
        return {'FINISHED'}