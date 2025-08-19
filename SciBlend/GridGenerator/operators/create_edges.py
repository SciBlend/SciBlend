import bpy
import mathutils

class CreateEdgesOperator(bpy.types.Operator):
    bl_idname = "object.create_edges"
    bl_label = "Create Edges"
    bl_options = {'REGISTER', 'UNDO'}

    def create_edge(self, start_obj, end_obj, grid_settings, scale_factor):
        if start_obj is None or end_obj is None:
            print(f"Error: Cannot create edge. Start object: {start_obj}, End object: {end_obj}")
            return

        curve = bpy.data.curves.new(type="CURVE", name="Edge")
        curve.dimensions = '3D'
        curve.resolution_u = 2
        spline = curve.splines.new('POLY')
        spline.points.add(1)
        spline.points[0].co = (start_obj.location.x, start_obj.location.y, start_obj.location.z, 1)
        spline.points[1].co = (end_obj.location.x, end_obj.location.y, end_obj.location.z, 1)
        edge_obj = bpy.data.objects.new(f"EdgeObj_{start_obj.name}_{end_obj.name}", curve)
        edge_obj.data.bevel_depth = grid_settings.base_edge_size * scale_factor
        bpy.context.collection.objects.link(edge_obj)

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

        if grid_settings.grid_type == 'CUBIC_INTERNAL_EDGES':
            for x in range(grid_settings.subdivisions + 1):
                for y in range(grid_settings.subdivisions + 1):
                    for z in range(grid_settings.subdivisions + 1):
                        current_node = bpy.data.objects.get(f"GridNode_{x}_{y}_{z}")
                        if current_node:
                            if x < grid_settings.subdivisions:
                                next_node_x = bpy.data.objects.get(f"GridNode_{x+1}_{y}_{z}")
                                if next_node_x:
                                    self.create_edge(current_node, next_node_x, grid_settings, scale_factor)
                            if y < grid_settings.subdivisions:
                                next_node_y = bpy.data.objects.get(f"GridNode_{x}_{y+1}_{z}")
                                if next_node_y:
                                    self.create_edge(current_node, next_node_y, grid_settings, scale_factor)
                            if z < grid_settings.subdivisions:
                                next_node_z = bpy.data.objects.get(f"GridNode_{x}_{y}_{z+1}")
                                if next_node_z:
                                    self.create_edge(current_node, next_node_z, grid_settings, scale_factor)
        elif grid_settings.grid_type == 'CUBIC_EXTERIOR':
            # Aristas horizontales (X) en los planos Z = 0 y Z = subdivisions
            for z in [0, grid_settings.subdivisions]:
                for y in range(grid_settings.subdivisions + 1):
                    for x in range(grid_settings.subdivisions):
                        self.create_edge_by_coords(x, y, z, x+1, y, z, grid_settings, scale_factor)

            # Aristas horizontales (X) en los planos Y = 0 y Y = subdivisions
            for y in [0, grid_settings.subdivisions]:
                for z in range(grid_settings.subdivisions + 1):
                    for x in range(grid_settings.subdivisions):
                        self.create_edge_by_coords(x, y, z, x+1, y, z, grid_settings, scale_factor)

            # Aristas verticales (Y) en los planos X = 0 y X = subdivisions
            for x in [0, grid_settings.subdivisions]:
                for z in range(grid_settings.subdivisions + 1):
                    for y in range(grid_settings.subdivisions):
                        self.create_edge_by_coords(x, y, z, x, y+1, z, grid_settings, scale_factor)

            # Aristas verticales (Z) en los planos X = 0 y X = subdivisions
            for x in [0, grid_settings.subdivisions]:
                for y in range(grid_settings.subdivisions + 1):
                    for z in range(grid_settings.subdivisions):
                        self.create_edge_by_coords(x, y, z, x, y, z+1, grid_settings, scale_factor)

            # Aristas verticales (Z) en los planos Y = 0 y Y = subdivisions
            for y in [0, grid_settings.subdivisions]:
                for x in range(grid_settings.subdivisions + 1):
                    for z in range(grid_settings.subdivisions):
                        self.create_edge_by_coords(x, y, z, x, y, z+1, grid_settings, scale_factor)

            # Aristas horizontales (Y) en los planos Z = 0 y Z = subdivisions
            for z in [0, grid_settings.subdivisions]:
                for x in range(grid_settings.subdivisions + 1):
                    for y in range(grid_settings.subdivisions):
                        self.create_edge_by_coords(x, y, z, x, y+1, z, grid_settings, scale_factor)
        elif grid_settings.grid_type in ['EXTERIOR_EDGES_1', 'EXTERIOR_EDGES_2']:
            corners = [
                (0, 0, 0),
                (grid_settings.subdivisions, 0, 0),
                (0, grid_settings.subdivisions, 0),
                (grid_settings.subdivisions, 0, grid_settings.subdivisions) if grid_settings.grid_type == 'EXTERIOR_EDGES_2' else (0, 0, grid_settings.subdivisions)
            ]
            
            edges = [
                (0, 1),  # X-axis
                (0, 2),  # Y-axis
                (0, 3) if grid_settings.grid_type == 'EXTERIOR_EDGES_1' else (1, 3)  # Z-axis
            ]
            
            for edge in edges:
                start = corners[edge[0]]
                end = corners[edge[1]]
                start_obj = bpy.data.objects.get(f"GridNode_{edge[0]}")
                end_obj = bpy.data.objects.get(f"GridNode_{edge[1]}")
                
                if start_obj and end_obj:
                    self.create_edge(start_obj, end_obj, grid_settings, scale_factor)
                else:
                    print(f"Error: Cannot find start or end object for edge {edge}. Start: {start_obj}, End: {end_obj}")
                
                prev_node = start_obj
                for i in range(1, grid_settings.subdivisions):
                    t = i / grid_settings.subdivisions
                    location = mathutils.Vector(start).lerp(mathutils.Vector(end), t)
                    sub_node = bpy.data.objects.get(f"GridNode_sub_{edge[0]}_{edge[1]}_{i}")
                    if sub_node:
                        if prev_node:
                            self.create_edge(prev_node, sub_node, grid_settings, scale_factor)
                        else:
                            print(f"Error: Previous node not found for subdivision {i}")
                        prev_node = sub_node
                    else:
                        print(f"Error: Subdivision node not found for edge {edge}, subdivision {i}")
                
                if prev_node and end_obj:
                    self.create_edge(prev_node, end_obj, grid_settings, scale_factor)
                else:
                    print(f"Error: Cannot create last edge segment. Prev node: {prev_node}, End: {end_obj}")
        elif grid_settings.grid_type == '2D_GRID':
            # Crear aristas horizontales
            for y in [0, grid_settings.subdivisions]:
                for x in range(grid_settings.subdivisions):
                    self.create_edge_by_coords(x, y, 0, x+1, y, 0, grid_settings, scale_factor)

            # Crear aristas verticales
            for x in [0, grid_settings.subdivisions]:
                for y in range(grid_settings.subdivisions):
                    self.create_edge_by_coords(x, y, 0, x, y+1, 0, grid_settings, scale_factor)

        return {'FINISHED'}

    def create_edge_by_coords(self, x1, y1, z1, x2, y2, z2, grid_settings, scale_factor):
        start_obj = bpy.data.objects.get(f"GridNode_{x1}_{y1}_{z1}")
        end_obj = bpy.data.objects.get(f"GridNode_{x2}_{y2}_{z2}")
        if start_obj and end_obj:
            self.create_edge(start_obj, end_obj, grid_settings, scale_factor)
        else:
            print(f"Error: Cannot find objects for edge ({x1},{y1},{z1}) to ({x2},{y2},{z2})")