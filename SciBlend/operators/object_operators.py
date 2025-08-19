import bpy
import math

class CreateNullOperator(bpy.types.Operator):
    bl_idname = "import_x3d.create_null"
    bl_label = "Create Null"

    null_type: bpy.props.EnumProperty(
        name="Null Type",
        description="Type of null object to create",
        items=[
            ('PLAIN_AXES', "Plain Axes", ""),
            ('ARROWS', "Arrows", ""),
            ('SINGLE_ARROW', "Single Arrow", ""),
            ('CIRCLE', "Circle", ""),
            ('CUBE', "Cube", ""),
            ('SPHERE', "Sphere", ""),
            ('CONE', "Cone", ""),
            ('IMAGE', "Image", "")
        ],
        default='PLAIN_AXES'
    )

    def execute(self, context):
        bpy.ops.object.empty_add(type=self.null_type)
        self.report({'INFO'}, f"Null of type {self.null_type} created.")
        return {'FINISHED'}

class ParentNullToGeoOperator(bpy.types.Operator):
    bl_idname = "import_x3d.parent_null_to_geo"
    bl_label = "Parent Null to Geo"

    def execute(self, context):
        null_object = next((obj for obj in bpy.context.scene.objects if obj.type == 'EMPTY'), None)

        if not null_object:
            self.report({'ERROR'}, "No null object found.")
            return {'CANCELLED'}

        original_states = {obj: (obj.hide_viewport, obj.hide_render) for obj in bpy.context.scene.objects}

        for obj in bpy.context.scene.objects:
            obj.hide_viewport = False
            obj.hide_render = False

        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            if obj != null_object:
                obj.select_set(True)

        bpy.context.view_layer.objects.active = null_object
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

        for obj, (hide_viewport, hide_render) in original_states.items():
            obj.hide_viewport = hide_viewport
            obj.hide_render = hide_render

        self.report({'INFO'}, "Null parented to all geometry.")
        return {'FINISHED'}

class NullToOriginOperator(bpy.types.Operator):
    bl_idname = "import_x3d.null_to_origin"
    bl_label = "Null to Origin"

    def execute(self, context):
        null_object = next((obj for obj in bpy.context.scene.objects if obj.type == 'EMPTY'), None)

        if not null_object:
            self.report({'ERROR'}, "No null object found.")
            return {'CANCELLED'}

        null_object.location = (0, 0, 0)
        self.report({'INFO'}, "Null moved to origin.")
        return {'FINISHED'}

class CreateSceneOperator(bpy.types.Operator):
    bl_idname = "object.create_scene"
    bl_label = "Scene 1"

    def execute(self, context):
        bpy.ops.object.light_add(type='SUN')
        sun = bpy.context.object
        sun.data.energy = 2.0
        sun.rotation_euler = (math.radians(180), 0, 0)

        world = bpy.context.scene.world
        if world is None:
            world = bpy.data.worlds.new("World")
            bpy.context.scene.world = world
        world.use_nodes = False
        world.color = (0, 0, 0)

        bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
        bpy.context.scene.use_nodes = True

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'RENDERED'
                        space.shading.use_scene_lights = True
                        space.shading.use_scene_world = True

        self.report({'INFO'}, "Scene created successfully.")
        return {'FINISHED'}

class GroupObjectsOperator(bpy.types.Operator):
    bl_idname = "object.group_objects"
    bl_label = "Group Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        group_type = context.scene.group_type
        objects_to_group = []

        if group_type == 'MESHES':
            objects_to_group = [obj for obj in bpy.data.objects if obj.type == 'MESH']
            collection_name = "Meshes"
        elif group_type == 'CAMERAS':
            objects_to_group = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
            collection_name = "Cameras"
        elif group_type == 'LIGHTS':
            objects_to_group = [obj for obj in bpy.data.objects if obj.type == 'LIGHT']
            collection_name = "Lights"
        elif group_type == 'ALL':
            objects_to_group = list(bpy.data.objects)
            collection_name = "All Objects"
        else:
            # Fallback to all objects if group_type is not one of the expected values
            objects_to_group = list(bpy.data.objects)
            collection_name = "All Objects"

        new_collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(new_collection)

        for obj in objects_to_group:
            if obj.name not in new_collection.objects:
                new_collection.objects.link(obj)

        self.report({'INFO'}, f"{len(objects_to_group)} objects grouped in '{collection_name}' collection.")
        return {'FINISHED'}

class DeleteHierarchyOperator(bpy.types.Operator):
    bl_idname = "object.delete_hierarchy"
    bl_label = "Delete Hierarchy"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        collections_to_remove = []

        for collection in bpy.data.collections:
            if collection.name in ["Meshes", "Cameras", "Lights", "All Objects"]:
                for obj in collection.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
                collections_to_remove.append(collection)

        for collection in collections_to_remove:
            bpy.data.collections.remove(collection)

        self.report({'INFO'}, "Hierarchy and objects deleted.")
        return {'FINISHED'}

class BooleanCutterOperator(bpy.types.Operator):
    bl_idname = "object.boolean_cutter_operator"
    bl_label = "Apply Boolean"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cutter_obj = context.scene.boolean_cutter_object
        if cutter_obj is None:
            self.report({'ERROR'}, "No cutter object selected")
            return {'CANCELLED'}

        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj != cutter_obj:
                bool_mod = obj.modifiers.get("Boolean")
                if not bool_mod:
                    bool_mod = obj.modifiers.new(name="Boolean", type='BOOLEAN')
                bool_mod.operation = 'DIFFERENCE'
                bool_mod.object = cutter_obj

        return {'FINISHED'}

class BooleanCutterHideOperator(bpy.types.Operator):
    bl_idname = "object.boolean_cutter_hide_operator"
    bl_label = "Hide Boolean Cutter"

    def execute(self, context):
        cutter_obj = context.scene.boolean_cutter_object
        if cutter_obj is None:
            self.report({'ERROR'}, "No cutter object selected.")
            return {'CANCELLED'}

        cutter_obj.hide_viewport = True
        cutter_obj.hide_render = True

        self.report({'INFO'}, "Boolean cutter hidden.")
        return {'FINISHED'}

class AddMeshCutterOperator(bpy.types.Operator):
    bl_idname = "object.add_mesh_cutter_operator"
    bl_label = "Add Mesh Cutter"
    
    mesh_type: bpy.props.EnumProperty(
        name="Mesh Type",
        description="Select a mesh to use as cutter",
        items=[
            ("CUBE", "Cube", "Add a cube"),
            ("SPHERE", "Sphere", "Add a sphere"),
            ("CYLINDER", "Cylinder", "Add a cylinder"),
            ("CONE", "Cone", "Add a cone"),
            ("TORUS", "Torus", "Add a torus")
        ])

    def execute(self, context):
        mesh_type = self.mesh_type

        if mesh_type == 'CUBE':
            bpy.ops.mesh.primitive_cube_add()
        elif mesh_type == 'SPHERE':
            bpy.ops.mesh.primitive_uv_sphere_add()
        elif mesh_type == 'CYLINDER':
            bpy.ops.mesh.primitive_cylinder_add()
        elif mesh_type == 'CONE':
            bpy.ops.mesh.primitive_cone_add()
        elif mesh_type == 'TORUS':
            bpy.ops.mesh.primitive_torus_add()

        cutter = context.active_object
        context.scene.boolean_cutter_object = cutter

        return {'FINISHED'}

class OrganizeGeometryInCollectionsOperator(bpy.types.Operator):
    bl_idname = "object.organize_geometry_in_collections"
    bl_label = "Organize Geometry in Collections"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        
        collections = []
        empties = []
        for i in range(scene.frame_start, scene.frame_end + 1):
            collection_name = f"Frame_{i}"
            if collection_name not in bpy.data.collections:
                new_collection = bpy.data.collections.new(collection_name)
                scene.collection.children.link(new_collection)
            else:
                new_collection = bpy.data.collections[collection_name]
            collections.append(new_collection)
            
            empty_name = f"Visibility_Control_{i}"
            if empty_name not in bpy.data.objects:
                empty = bpy.data.objects.new(empty_name, None)
                scene.collection.objects.link(empty)
            else:
                empty = bpy.data.objects[empty_name]
            empties.append(empty)

        for frame, (collection, empty) in enumerate(zip(collections, empties), start=scene.frame_start):
            visible_objects = [obj for obj in scene.objects if obj.type == 'MESH' and not obj.hide_viewport]
            for obj in visible_objects:
                if obj.name not in collection.objects:
                    collection.objects.link(obj)
                if obj.name in scene.collection.objects:
                    scene.collection.objects.unlink(obj)

            empty.hide_viewport = False
            empty.hide_render = False
            empty.keyframe_insert(data_path="hide_viewport", frame=frame)
            empty.keyframe_insert(data_path="hide_render", frame=frame)
            
            empty.hide_viewport = True
            empty.hide_render = True
            if frame > scene.frame_start:
                empty.keyframe_insert(data_path="hide_viewport", frame=frame-1)
                empty.keyframe_insert(data_path="hide_render", frame=frame-1)
            if frame < scene.frame_end:
                empty.keyframe_insert(data_path="hide_viewport", frame=frame+1)
                empty.keyframe_insert(data_path="hide_render", frame=frame+1)

        for collection, empty in zip(collections, empties):
            for prop in ["hide_viewport", "hide_render"]:
                driver = collection.driver_add(prop)
                driver.driver.type = 'AVERAGE'
                var = driver.driver.variables.new()
                var.name = 'visibility'
                var.type = 'SINGLE_PROP'
                var.targets[0].id = empty
                var.targets[0].data_path = prop
                driver.driver.expression = 'visibility'

        for empty in empties:
            if empty.animation_data and empty.animation_data.action:
                for fcurve in empty.animation_data.action.fcurves:
                    for kf in fcurve.keyframe_points:
                        kf.interpolation = 'CONSTANT'

        self.report({'INFO'}, "Geometry organized in collections and animation updated.")
        return {'FINISHED'}

class CenterNullToOriginOperator(bpy.types.Operator):
    bl_idname = "object.center_null_to_origin"
    bl_label = "Center Null to Origin"

    def execute(self, context):
        null_object = next((obj for obj in bpy.context.scene.objects if obj.type == 'EMPTY'), None)

        if not null_object:
            self.report({'ERROR'}, "No null object found.")
            return {'CANCELLED'}

        null_object.location = (0, 0, 0)
        
        for child in null_object.children:
            child.select_set(True)
        
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
        
        for child in null_object.children:
            child.select_set(False)

        self.report({'INFO'}, "Null centered to origin and children's origin set to geometry.")
        return {'FINISHED'}