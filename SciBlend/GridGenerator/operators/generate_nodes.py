import bpy
import mathutils
import math

class GenerateNodesOperator(bpy.types.Operator):
    bl_idname = "object.generate_nodes"
    bl_label = "Generate Nodes"
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

        dist_x = grid_settings.distance_x * scale_factor
        dist_y = grid_settings.distance_y * scale_factor
        dist_z = grid_settings.distance_z * scale_factor

        # Ajustar el tamaño del texto basado en la unidad de medida
        adjusted_text_size = grid_settings.base_text_size * scale_factor

        # Use existing camera or create a new one
        camera = next(
            (obj for obj in bpy.context.scene.objects if obj.type == 'CAMERA'), None)
        if not camera:
            bpy.ops.object.camera_add(
                align='VIEW', location=(0, -10, 5), rotation=(0, 0, 0))
            camera = bpy.context.object

        # Remove only objects related to the previous grid, but keep edges for EXTERIOR_EDGES_1 and EXTERIOR_EDGES_2
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            if obj.name.startswith("GridNode_") or obj.name.startswith("GridNode_text_"):
                obj.select_set(True)
            elif obj.name.startswith("EdgeObj_") and grid_settings.grid_type == 'CUBIC_INTERNAL_EDGES':
                obj.select_set(True)
        bpy.ops.object.delete()

        text_objects = []

        def create_node(location, name):
            empty = bpy.data.objects.new(name, None)
            empty.location = location
            bpy.context.collection.objects.link(empty)
            return empty

        def create_text(location, name, text, axis):
            if grid_settings.show_numbers:
                bpy.ops.object.text_add(location=location)
                text_obj = bpy.context.object
                text_obj.name = name
                text_obj.data.body = text
                text_obj.data.align_x = 'CENTER'
                text_obj.data.align_y = 'CENTER'
                text_obj.scale = (adjusted_text_size,) * 3
                if grid_settings.use_custom_font and grid_settings.custom_font:
                    try:
                        font = bpy.data.fonts.load(grid_settings.custom_font)
                        text_obj.data.font = font
                    except:
                        self.report({'WARNING'}, "Failed to load custom font. Using default.")
                
                # Aplicar tracking a la cámara solo si no es un grid 2D
                if grid_settings.grid_type != '2D_GRID':
                    constraint = text_obj.constraints.new(type='TRACK_TO')
                    constraint.target = camera
                    constraint.track_axis = 'TRACK_Z'
                    constraint.up_axis = 'UP_Y'
                
                apply_text_offset(location, text_obj, axis)
                text_objects.append(text_obj)
                
                print(f"Created text '{text}' for axis {axis} at location {location}")
                print(f"Final text location: {text_obj.location}")
            return text_obj if grid_settings.show_numbers else None

        def apply_text_offset(node_location, text_obj, axis):
            offset = getattr(grid_settings, f"text_offset_{axis.lower()}")
            direction = getattr(grid_settings, f"text_direction_{axis.lower()}")
            
            offset_vector = mathutils.Vector((0, 0, 0))
            if direction == 'X':
                offset_vector.x = offset
            elif direction == '-X':
                offset_vector.x = -offset
            elif direction == 'Y':
                offset_vector.y = offset
            elif direction == '-Y':
                offset_vector.y = -offset
            elif direction == 'Z':
                offset_vector.z = offset
            elif direction == '-Z':
                offset_vector.z = -offset
            
            text_obj.location = node_location + offset_vector
            
            print(f"Applying offset for axis {axis}: direction {direction}, offset {offset}")
            print(f"Offset vector: {offset_vector}")
            print(f"Final text location: {text_obj.location}")

        if grid_settings.grid_type == 'CUBIC_INTERNAL_EDGES':
            for z in range(grid_settings.subdivisions + 1):
                for y in range(grid_settings.subdivisions + 1):
                    for x in range(grid_settings.subdivisions + 1):
                        location = mathutils.Vector((
                            x * dist_x / grid_settings.subdivisions,
                            y * dist_y / grid_settings.subdivisions,
                            z * dist_z / grid_settings.subdivisions
                        ))
                        
                        node_name = f"GridNode_{x}_{y}_{z}"
                        create_node(location, node_name)
                        
                        if grid_settings.show_numbers:
                            text = f"{location.x:.2f},{location.y:.2f},{location.z:.2f}"
                            if x == grid_settings.subdivisions:
                                axis = 'X'
                            elif y == grid_settings.subdivisions:
                                axis = 'Y'
                            elif z == grid_settings.subdivisions:
                                axis = 'Z'
                            else:
                                axis = 'X'  # Default for internal nodes
                            create_text(location, node_name + "_text", text, axis)

        elif grid_settings.grid_type == 'CUBIC_EXTERIOR':
            for z in [0, grid_settings.subdivisions]:
                for y in range(grid_settings.subdivisions + 1):
                    for x in range(grid_settings.subdivisions + 1):
                        location = mathutils.Vector((
                            x * dist_x / grid_settings.subdivisions,
                            y * dist_y / grid_settings.subdivisions,
                            z * dist_z / grid_settings.subdivisions
                        ))
                        
                        node_name = f"GridNode_{x}_{y}_{z}"
                        create_node(location, node_name)
                        
                        if grid_settings.show_numbers:
                            text = f"{location.x:.2f},{location.y:.2f},{location.z:.2f}"
                            if x == grid_settings.subdivisions:
                                axis = 'X'
                            elif y == grid_settings.subdivisions:
                                axis = 'Y'
                            else:
                                axis = 'Z'
                            create_text(location, node_name + "_text", text, axis)

            for y in [0, grid_settings.subdivisions]:
                for z in range(1, grid_settings.subdivisions):
                    for x in range(grid_settings.subdivisions + 1):
                        location = mathutils.Vector((
                            x * dist_x / grid_settings.subdivisions,
                            y * dist_y / grid_settings.subdivisions,
                            z * dist_z / grid_settings.subdivisions
                        ))
                        
                        node_name = f"GridNode_{x}_{y}_{z}"
                        create_node(location, node_name)
                        
                        if grid_settings.show_numbers:
                            text = f"{location.x:.2f},{location.y:.2f},{location.z:.2f}"
                            if x == grid_settings.subdivisions:
                                axis = 'X'
                            else:
                                axis = 'Y'
                            create_text(location, node_name + "_text", text, axis)

            for x in [0, grid_settings.subdivisions]:
                for z in range(1, grid_settings.subdivisions):
                    for y in range(1, grid_settings.subdivisions):
                        location = mathutils.Vector((
                            x * dist_x / grid_settings.subdivisions,
                            y * dist_y / grid_settings.subdivisions,
                            z * dist_z / grid_settings.subdivisions
                        ))
                        
                        node_name = f"GridNode_{x}_{y}_{z}"
                        create_node(location, node_name)
                        
                        if grid_settings.show_numbers:
                            text = f"{location.x:.2f},{location.y:.2f},{location.z:.2f}"
                            axis = 'X'
                            create_text(location, node_name + "_text", text, axis)

        elif grid_settings.grid_type in ['EXTERIOR_EDGES_1', 'EXTERIOR_EDGES_2']:
            corners = [
                (0, 0, 0),
                (grid_settings.subdivisions, 0, 0),
                (0, grid_settings.subdivisions, 0),
                (grid_settings.subdivisions, 0, grid_settings.subdivisions) if grid_settings.grid_type == 'EXTERIOR_EDGES_2' else (0, 0, grid_settings.subdivisions)
            ]
            
            for i, (x, y, z) in enumerate(corners):
                location = mathutils.Vector((
                    x * dist_x / grid_settings.subdivisions,
                    y * dist_y / grid_settings.subdivisions,
                    z * dist_z / grid_settings.subdivisions
                ))
                node_name = f"GridNode_{i}"
                create_node(location, node_name)
                
                if grid_settings.show_numbers:
                    coord_x = x * grid_settings.distance_x / grid_settings.subdivisions
                    coord_y = y * grid_settings.distance_y / grid_settings.subdivisions
                    coord_z = z * grid_settings.distance_z / grid_settings.subdivisions
                    
                    if x == grid_settings.subdivisions and z == 0:
                        text = f"{coord_x:.2f}"
                        axis = 'X'
                    elif y == grid_settings.subdivisions:
                        text = f"{coord_y:.2f}"
                        axis = 'Y'
                    elif z == grid_settings.subdivisions:
                        text = f"{coord_z:.2f}"
                        axis = 'Z'
                    else:
                        text = "0.00"
                        axis = 'X'  # Valor predeterminado para el origen
                    
                    create_text(location, node_name + "_text", text, axis)
            
            # Generate subdivision nodes
            edges = [
                (0, 1),  # X-axis
                (0, 2),  # Y-axis
                (0, 3) if grid_settings.grid_type == 'EXTERIOR_EDGES_1' else (1, 3)  # Z-axis
            ]
            for edge in edges:
                start = corners[edge[0]]
                end = corners[edge[1]]
                for i in range(1, grid_settings.subdivisions):
                    t = i / grid_settings.subdivisions
                    x = int(start[0] + t * (end[0] - start[0]))
                    y = int(start[1] + t * (end[1] - start[1]))
                    z = int(start[2] + t * (end[2] - start[2]))
                    location = mathutils.Vector((
                        x * dist_x / grid_settings.subdivisions,
                        y * dist_y / grid_settings.subdivisions,
                        z * dist_z / grid_settings.subdivisions
                    ))
                    
                    node_name = f"GridNode_sub_{edge[0]}_{edge[1]}_{i}"
                    create_node(location, node_name)
                    
                    if grid_settings.show_numbers:
                        if end[0] > start[0]:  # X-axis
                            coord = x * grid_settings.distance_x / grid_settings.subdivisions
                            axis = 'X'
                        elif end[1] > start[1]:  # Y-axis
                            coord = y * grid_settings.distance_y / grid_settings.subdivisions
                            axis = 'Y'
                        else:  # Z-axis
                            coord = z * grid_settings.distance_z / grid_settings.subdivisions
                            axis = 'Z'
                        text = f"{coord:.2f}"
                        create_text(location, node_name + "_text", text, axis)

        elif grid_settings.grid_type == '2D_GRID':
            orientation = grid_settings.grid_2d_orientation
            rotation_matrix = mathutils.Matrix.Identity(3)
            if orientation == 'XZ':
                rotation_matrix = mathutils.Matrix.Rotation(math.radians(90), 3, 'X')
            elif orientation == 'YZ':
                rotation_matrix = mathutils.Matrix.Rotation(math.radians(90), 3, 'Y')
            elif orientation == '-XY':
                rotation_matrix = mathutils.Matrix.Rotation(math.radians(180), 3, 'X')
            elif orientation == '-XZ':
                rotation_matrix = mathutils.Matrix.Rotation(math.radians(-90), 3, 'X')
            elif orientation == '-YZ':
                rotation_matrix = mathutils.Matrix.Rotation(math.radians(-90), 3, 'Y')

            for y in range(grid_settings.subdivisions + 1):
                for x in range(grid_settings.subdivisions + 1):
                    original_location = mathutils.Vector((
                        x * dist_x / grid_settings.subdivisions,
                        y * dist_y / grid_settings.subdivisions,
                        0
                    ))
                    location = rotation_matrix @ original_location
                    
                    node_name = f"GridNode_{x}_{y}_0"
                    node = create_node(location, node_name)
                    node.rotation_euler = rotation_matrix.to_euler()
                    
                    if grid_settings.show_numbers:
                        show_x = grid_settings.length_axis_2d in ['X', 'BOTH']
                        show_y = grid_settings.length_axis_2d in ['Y', 'BOTH']
                        
                        if (x == 0 and show_y) or (y == 0 and show_x):
                            coord_x = x * grid_settings.distance_x / grid_settings.subdivisions
                            coord_y = y * grid_settings.distance_y / grid_settings.subdivisions
                            
                            if x == 0 and y == 0:
                                text = "0.00, 0.00" if grid_settings.length_axis_2d == 'BOTH' else "0.00"
                                axis = 'X'
                            elif x == 0 and show_y:
                                text = f"{coord_y:.2f}"
                                axis = 'Y'
                            elif y == 0 and show_x:
                                text = f"{coord_x:.2f}"
                                axis = 'X'
                            
                            text_obj = create_text(location, node_name + "_text", text, axis)
                            if text_obj:
                                text_obj.rotation_euler = rotation_matrix.to_euler()

        return {'FINISHED'}