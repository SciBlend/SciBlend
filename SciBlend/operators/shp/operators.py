import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, FloatProperty, BoolProperty
import numpy as np
import os
import geopandas as gpd
from ..utils.scene import clear_scene

class ImportShapefileOperator(bpy.types.Operator, ImportHelper):
    """Import Shapefile (.shp) into Blender."""
    bl_idname = "import_shapefile.static"
    bl_label = "Import Shapefile"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".shp"
    filter_glob: StringProperty(default="*.shp", options={'HIDDEN'})

    scale_factor: FloatProperty(name="Scale Factor", description="Scale factor for imported objects", default=1.0, min=0.0001, max=100.0)
    extrude_height: FloatProperty(name="Extrude Height", description="Height to extrude 2D shapes", default=0.0, min=0.0, max=100.0)
    use_dbf_attributes: BoolProperty(name="Use DBF Attributes", description="Import attributes from DBF file", default=True)

    def execute(self, context):
        try:
            if context.scene.x3d_import_settings.overwrite_scene:
                clear_scene(context)
            gdf = gpd.read_file(self.filepath)
            collection_name = os.path.splitext(os.path.basename(self.filepath))[0]
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
            material = bpy.data.materials.new(name=f"{collection_name}_Material")
            material.use_nodes = True
            nodes = material.node_tree.nodes
            links = material.node_tree.links
            nodes.clear()
            bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
            output = nodes.new(type='ShaderNodeOutputMaterial')
            links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
            for idx, row in gdf.iterrows():
                geom = row.geometry
                if geom is None:
                    continue
                verts = []
                edges = []
                faces = []
                if geom.geom_type == 'Polygon':
                    coords = np.array(geom.exterior.coords)
                    verts = [(x * self.scale_factor, y * self.scale_factor, 0) for x, y in coords[:-1]]
                    verts, edges, faces = self.triangulate_mesh(verts)
                elif geom.geom_type == 'MultiPolygon':
                    all_verts = []
                    all_faces = []
                    vertex_offset = 0
                    for polygon in geom.geoms:
                        coords = np.array(polygon.exterior.coords)
                        poly_verts = [(x * self.scale_factor, y * self.scale_factor, 0) for x, y in coords[:-1]]
                        tri_verts, _, tri_faces = self.triangulate_mesh(poly_verts)
                        adjusted_faces = [[idx + vertex_offset for idx in face] for face in tri_faces]
                        all_verts.extend(tri_verts)
                        all_faces.extend(adjusted_faces)
                        vertex_offset += len(tri_verts)
                    verts = all_verts
                    faces = all_faces
                elif geom.geom_type == 'LineString':
                    coords = np.array(geom.coords)
                    z_height = float(row.get('Elev', 0.0)) * self.extrude_height
                    verts = [(x * self.scale_factor, y * self.scale_factor, z_height) for x, y in coords]
                    edges = [(i, i+1) for i in range(len(verts)-1)]
                elif geom.geom_type == 'MultiLineString':
                    start_idx = 0
                    z_height = float(row.get('Elev', 0.0)) * self.extrude_height
                    for line in geom.geoms:
                        coords = np.array(line.coords)
                        line_verts = [(x * self.scale_factor, y * self.scale_factor, z_height) for x, y in coords]
                        verts.extend(line_verts)
                        edges.extend([(start_idx + i, start_idx + i+1) for i in range(len(line_verts)-1)])
                        start_idx += len(line_verts)
                else:
                    continue
                if not verts:
                    continue
                mesh = bpy.data.meshes.new(f"{collection_name}_{idx}")
                obj = bpy.data.objects.new(f"{collection_name}_{idx}", mesh)
                collection.objects.link(obj)
                mesh.from_pydata(verts, edges, faces)
                mesh.update()
                obj.data.materials.append(material)
                if edges and not faces:
                    self.setup_geometry_nodes(obj)
                if self.extrude_height > 0 and faces:
                    bpy.context.view_layer.objects.active = obj
                    obj.select_set(True)
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate=({"value": (0, 0, self.extrude_height)}))
                    bpy.ops.object.mode_set(mode='OBJECT')
                if self.use_dbf_attributes:
                    for column in gdf.columns:
                        if column != 'geometry':
                            value = row[column]
                            domain = 'FACE' if faces else 'EDGE' if edges else 'POINT'
                            if isinstance(value, (int, float)):
                                attr = mesh.attributes.new(name=column, type='FLOAT', domain=domain)
                                for i in range(len(attr.data)):
                                    attr.data[i].value = float(value)
                            elif isinstance(value, str):
                                try:
                                    float_value = float(value)
                                    attr = mesh.attributes.new(name=column, type='FLOAT', domain=domain)
                                    for i in range(len(attr.data)):
                                        attr.data[i].value = float_value
                                except ValueError:
                                    attr = mesh.attributes.new(name=column, type='BYTE_COLOR', domain=domain)
                                    str_bytes = value.encode('utf-8')[:4]
                                    while len(str_bytes) < 4:
                                        str_bytes += b'\x00'
                                    color_value = tuple(b/255 for b in str_bytes)
                                    for i in range(len(attr.data)):
                                        attr.data[i].color = color_value
            self.report({'INFO'}, f"Imported shapefile: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error importing shapefile: {str(e)}")
            return {'CANCELLED'}

    def setup_geometry_nodes(self, obj):
        """Add a Geometry Nodes setup to render edges as tubes using a circle profile."""
        geo_nodes = obj.modifiers.new(name="Curve Circle", type='NODES')
        if "Curve Circle" not in bpy.data.node_groups:
            node_group = bpy.data.node_groups.new("Curve Circle", 'GeometryNodeTree')
            nodes = node_group.nodes
            links = node_group.links
            nodes.clear()
            group_input = nodes.new('NodeGroupInput')
            group_output = nodes.new('NodeGroupOutput')
            mesh_to_curve = nodes.new('GeometryNodeMeshToCurve')
            curve_circle = nodes.new('GeometryNodeCurvePrimitiveCircle')
            curve_to_mesh = nodes.new('GeometryNodeCurveToMesh')
            set_material = nodes.new('GeometryNodeSetMaterial')
            group_input.location = (-400, 0)
            mesh_to_curve.location = (-200, 0)
            curve_circle.location = (-200, -200)
            curve_to_mesh.location = (0, 0)
            set_material.location = (200, 0)
            group_output.location = (400, 0)
            node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
            node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
            curve_circle.inputs['Radius'].default_value = 0.1
            curve_circle.inputs['Resolution'].default_value = 32
            if len(obj.data.materials) > 0:
                set_material.inputs['Material'].default_value = obj.data.materials[0]
            links.new(group_input.outputs["Geometry"], mesh_to_curve.inputs["Mesh"])
            links.new(mesh_to_curve.outputs["Curve"], curve_to_mesh.inputs["Curve"])
            links.new(curve_circle.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])
            links.new(curve_to_mesh.outputs["Mesh"], set_material.inputs["Geometry"])
            links.new(set_material.outputs["Geometry"], group_output.inputs["Geometry"])
        else:
            node_group = bpy.data.node_groups["Curve Circle"]
        geo_nodes.node_group = node_group

__all__ = ["ImportShapefileOperator"] 