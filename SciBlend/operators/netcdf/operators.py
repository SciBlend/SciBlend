import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, FloatProperty, EnumProperty, BoolProperty
import numpy as np
import os
import math
import time
from datetime import datetime, timedelta
from ..utils.scene import clear_scene, keyframe_visibility_single_frame, enforce_constant_interpolation

try:
    import netCDF4 as nc
    NETCDF_AVAILABLE = True
except ImportError:
    NETCDF_AVAILABLE = False

class ImportNetCDFOperator(bpy.types.Operator, ImportHelper):
    """Import NetCDF files into Blender."""
    bl_idname = "import_netcdf.animation"
    bl_label = "Import NetCDF Animation"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".nc"
    filter_glob: StringProperty(default="*.nc;*.nc4", options={'HIDDEN'})

    variable_name: StringProperty(name="Variable Name", description="Name of the variable to visualize", default="")
    time_dimension: StringProperty(name="Time Dimension", description="Name of the time dimension", default="time")
    scale_factor: FloatProperty(name="Scale Factor", description="Scale factor for imported objects", default=1.0, min=0.0001, max=100.0)
    axis_forward: EnumProperty(name="Forward", items=[('X','X Forward',''),('Y','Y Forward',''),('Z','Z Forward',''),('-X','-X Forward',''),('-Y','-Y Forward',''),('-Z','-Z Forward','')], default='Y')
    axis_up: EnumProperty(name="Up", items=[('X','X Up',''),('Y','Y Up',''),('Z','Z Up',''),('-X','-X Up',''),('-Y','-Y Up',''),('-Z','-Z Up','')], default='Z')
    use_sphere: BoolProperty(name="Spherical Projection", description="Project data onto a sphere", default=False)
    sphere_radius: FloatProperty(name="Sphere Radius", default=1.0, min=0.01, max=100.0)
    height_scale: FloatProperty(name="Height Scale", default=0.01, min=0.0001, max=1.0, soft_min=0.001, soft_max=0.1)

    def execute(self, context):
        if not NETCDF_AVAILABLE:
            self.report({'ERROR'}, "netCDF4 is not available. Please install netCDF4.")
            return {'CANCELLED'}
        try:
            dataset = nc.Dataset(self.filepath, 'r')
            if not self.variable_name:
                for var_name in dataset.variables:
                    if var_name not in dataset.dimensions:
                        var = dataset.variables[var_name]
                        if len(var.shape) >= 2:
                            self.variable_name = var_name
                            break
            if self.variable_name not in dataset.variables:
                self.report({'ERROR'}, f"Variable '{self.variable_name}' not found")
                return {'CANCELLED'}
            variable = dataset.variables[self.variable_name]
            if len(variable.shape) < 2:
                self.report({'ERROR'}, f"Variable '{self.variable_name}' must have at least 2 dimensions")
                return {'CANCELLED'}
            spatial_dims = [dim for dim in variable.dimensions if dim != self.time_dimension]
            if len(spatial_dims) < 2:
                self.report({'ERROR'}, "Need at least 2 spatial dimensions")
                return {'CANCELLED'}
            coords = {dim_name: dataset.variables[dim_name][:] for dim_name in variable.dimensions if dim_name in dataset.variables}
            has_time = self.time_dimension in dataset.dimensions and len(dataset.dimensions[self.time_dimension]) > 0
            if has_time:
                time_steps = len(dataset.dimensions[self.time_dimension])
                time_axis = variable.dimensions.index(self.time_dimension)
                variable_data = np.moveaxis(variable[:], time_axis, 0) if time_axis != 0 else variable[:]
            else:
                time_steps = 1
                variable_data = np.expand_dims(variable[:], 0)
            loop_count = max(1, getattr(context.scene.x3d_import_settings, "loop_count", 1))
            if has_time:
                context.scene.frame_start = 1
                context.scene.frame_end = time_steps * loop_count
            if context.scene.x3d_import_settings.overwrite_scene:
                clear_scene(context)
            material = self.create_material(variable_data, self.variable_name)
            start_wall = time.time()
            print(f"[NetCDF] Starting import of {time_steps} time step(s) at {datetime.now().strftime('%H:%M:%S')}")
            for frame in range(time_steps):
                per_item_start = time.time()
                data = variable_data[frame]
                vertices = []
                faces = []
                spatial_dims = list(variable.dimensions)
                if has_time:
                    spatial_dims.remove(self.time_dimension)
                dim_y, dim_x = spatial_dims[-2:]
                rows = len(dataset.dimensions[dim_y])
                cols = len(dataset.dimensions[dim_x])
                x_coords = coords.get(dim_x, np.arange(cols))
                y_coords = coords.get(dim_y, np.arange(rows))
                for i in range(rows):
                    for j in range(cols):
                        if self.use_sphere:
                            lon = float(x_coords[j])
                            lat = float(y_coords[i])
                            lon_rad = math.radians(lon)
                            lat_rad = math.radians(lat)
                            radius = self.sphere_radius * self.scale_factor
                            x = radius * math.cos(lat_rad) * math.cos(lon_rad)
                            y = radius * math.cos(lat_rad) * math.sin(lon_rad)
                            z = radius * math.sin(lat_rad)
                        else:
                            x = float(x_coords[j]) * self.scale_factor
                            y = float(y_coords[i]) * self.scale_factor
                            z = 0.0
                        try:
                            value = data[i, j]
                            if np.isscalar(value):
                                height = float(value) if not np.isnan(value) else 0.0
                            else:
                                if isinstance(value, np.ndarray) and value.size > 0 and not np.all(np.isnan(value)):
                                    height = float(np.nanmean(value))
                                else:
                                    height = 0.0
                        except IndexError:
                            height = 0.0
                        if self.use_sphere:
                            factor = 1.0 + (height * self.height_scale)
                            x *= factor
                            y *= factor
                            z *= factor
                        else:
                            z = height
                        vertices.append((x, y, z))
                for i in range(rows - 1):
                    for j in range(cols - 1):
                        v0 = i * cols + j
                        v1 = v0 + 1
                        v2 = (i + 1) * cols + j + 1
                        v3 = (i + 1) * cols + j
                        faces.append([v0, v1, v2, v3])
                mesh_name = f"Frame_{frame+1}" if has_time else f"NetCDF_{self.variable_name}"
                mesh = bpy.data.meshes.new(mesh_name)
                obj = bpy.data.objects.new(mesh_name, mesh)
                mesh.from_pydata(vertices, [], faces)
                mesh.update()
                self.add_attributes(mesh, data, coords, dim_x, dim_y)
                context.collection.objects.link(obj)
                obj.data.materials.append(material)
                if has_time:
                    self.setup_animation(obj, frame, time_steps, loop_count)
                duration = time.time() - per_item_start
                processed = frame + 1
                elapsed = time.time() - start_wall
                avg = (elapsed / processed) if processed > 0 else 0.0
                remaining = max(0, time_steps - processed)
                eta_dt = datetime.now() + timedelta(seconds=avg * remaining) if avg > 0 else datetime.now()
                print(f"[NetCDF] Imported time step {processed}/{time_steps} in {duration:.2f}s. ETA ~ {eta_dt.strftime('%H:%M:%S')}")
            dataset.close()
            self.report({'INFO'}, "Imported NetCDF data successfully")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error importing file: {str(e)}")
            return {'CANCELLED'}

    def add_attributes(self, mesh, data, coords, dim_x, dim_y):
        """Add per-point attributes from NetCDF arrays, matching vertex count."""
        rows, cols = int(data.shape[-2]), int(data.shape[-1])
        vertex_count = rows * cols

        attr = mesh.attributes.new(name=self.variable_name, type='FLOAT', domain='POINT')
        flat_values = np.ravel(data).astype(float)
        for idx in range(min(vertex_count, flat_values.size)):
            v = flat_values[idx]
            attr.data[idx].value = float(v) if not np.isnan(v) else 0.0

        if dim_x in coords:
            x_vals = np.asarray(coords[dim_x], dtype=float)
            attr_x = mesh.attributes.new(name=f"coord_{dim_x}", type='FLOAT', domain='POINT')
            k = 0
            for i in range(rows):
                for j in range(cols):
                    attr_x.data[k].value = float(x_vals[j]) if j < x_vals.size else 0.0
                    k += 1
        if dim_y in coords:
            y_vals = np.asarray(coords[dim_y], dtype=float)
            attr_y = mesh.attributes.new(name=f"coord_{dim_y}", type='FLOAT', domain='POINT')
            k = 0
            for i in range(rows):
                for j in range(cols):
                    attr_y.data[k].value = float(y_vals[i]) if i < y_vals.size else 0.0
                    k += 1

    def create_material(self, variable_data, variable_name):
        """Create a material that maps scalar values to colors."""
        material = bpy.data.materials.new(name=f"NetCDF_{variable_name}_Material")
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        nodes.clear()
        attribute_node = nodes.new(type='ShaderNodeAttribute')
        attribute_node.attribute_name = variable_name
        map_range = nodes.new(type='ShaderNodeMapRange')
        color_ramp = nodes.new(type='ShaderNodeValToRGB')
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        output = nodes.new(type='ShaderNodeOutputMaterial')
        try:
            data = np.asarray(variable_data)
            flat_data = data.ravel()
            valid_mask = np.logical_and(~np.isnan(flat_data), ~np.isinf(flat_data))
            if valid_mask.size > 0 and valid_mask.any():
                valid_data = flat_data[valid_mask]
                if valid_data.size > 0:
                    min_val = float(np.min(valid_data))
                    max_val = float(np.max(valid_data))
                else:
                    min_val = 0.0
                    max_val = 1.0
            else:
                min_val = 0.0
                max_val = 1.0
        except Exception:
            min_val = 0.0
            max_val = 1.0
        map_range.inputs['From Min'].default_value = min_val
        map_range.inputs['From Max'].default_value = max_val
        map_range.inputs['To Min'].default_value = 0.0
        map_range.inputs['To Max'].default_value = 1.0
        links.new(attribute_node.outputs['Fac'], map_range.inputs['Value'])
        links.new(map_range.outputs['Result'], color_ramp.inputs['Fac'])
        links.new(color_ramp.outputs['Color'], bsdf.inputs['Base Color'])
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        return material

    def setup_animation(self, obj, frame, time_steps, loop_count):
        """Insert keyframes to reveal one frame per time step, repeated for loop_count."""
        base = frame + 1
        for k in range(loop_count):
            occurrence = base + (k * time_steps)
            keyframe_visibility_single_frame(obj, occurrence)
        enforce_constant_interpolation(obj)

__all__ = ["ImportNetCDFOperator"] 