"""Operator for applying attribute smoothing/interpolation to collections."""

import bpy
from bpy.types import Operator


class FILTERS_OT_apply_interpolation(Operator):
    """Apply smoothing/interpolation to create a new derived attribute on all meshes in the collection."""
    bl_idname = "filters.apply_interpolation"
    bl_label = "Apply Smoothing"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = getattr(context.scene, 'filters_interpolation_settings', None)
        if not settings:
            self.report({'ERROR'}, "Interpolation settings not available")
            return {'CANCELLED'}
        
        coll_name = getattr(settings, 'target_collection', '')
        if not coll_name:
            self.report({'ERROR'}, "No collection selected")
            return {'CANCELLED'}
        
        coll = bpy.data.collections.get(coll_name)
        if not coll:
            self.report({'ERROR'}, f"Collection '{coll_name}' not found")
            return {'CANCELLED'}
        
        # Get mesh objects from collection
        mesh_objects = [obj for obj in coll.objects if obj.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, "No mesh objects in collection")
            return {'CANCELLED'}
        
        source_attr = getattr(settings, 'source_attribute', '')
        if not source_attr:
            self.report({'ERROR'}, "No source attribute selected")
            return {'CANCELLED'}
        
        output_name = (getattr(settings, 'output_name', '') or 'smoothed').strip()
        if not output_name:
            self.report({'ERROR'}, "Output name is empty")
            return {'CANCELLED'}
        
        method = getattr(settings, 'method', 'IDW')
        k_neighbors = getattr(settings, 'k_neighbors', 8)
        idw_power = getattr(settings, 'idw_power', 2.0)
        gaussian_sigma = getattr(settings, 'gaussian_sigma', 1.0)
        laplacian_iterations = getattr(settings, 'laplacian_iterations', 1)
        laplacian_factor = getattr(settings, 'laplacian_factor', 0.5)
        shepard_power = getattr(settings, 'shepard_power', 2.0)
        shepard_res = getattr(settings, 'shepard_resolution', 50)
        include_self = getattr(settings, 'include_self', False)
        
        success_count = 0
        error_count = 0
        
        for obj in mesh_objects:
            # Check if this object has the source attribute
            mesh = obj.data
            attrs = getattr(mesh, 'attributes', None)
            if not attrs or source_attr not in attrs:
                continue
            
            try:
                from ..utils.interpolation import (
                    smooth_idw,
                    smooth_gaussian,
                    smooth_laplacian,
                    smooth_nearest_neighbor,
                    interpolate_shepard_vtk,
                    write_attribute_to_mesh,
                )
                
                values = None
                
                if method == 'IDW':
                    values = smooth_idw(
                        obj, source_attr,
                        k_neighbors=k_neighbors,
                        power=idw_power,
                        include_self=include_self
                    )
                
                elif method == 'GAUSSIAN':
                    values = smooth_gaussian(
                        obj, source_attr,
                        k_neighbors=k_neighbors,
                        sigma=gaussian_sigma
                    )
                
                elif method == 'LAPLACIAN':
                    values = smooth_laplacian(
                        obj, source_attr,
                        iterations=laplacian_iterations,
                        factor=laplacian_factor
                    )
                
                elif method == 'NEAREST':
                    values = smooth_nearest_neighbor(
                        obj, source_attr,
                        k_neighbors=k_neighbors
                    )
                
                elif method == 'SHEPARD':
                    values = interpolate_shepard_vtk(
                        obj, source_attr,
                        power=shepard_power,
                        sample_dimensions=(shepard_res, shepard_res, shepard_res)
                    )
                
                if values is not None:
                    if write_attribute_to_mesh(obj, output_name, values, domain='POINT'):
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"Smoothing failed for {obj.name}: {e}")
        
        if success_count > 0:
            msg = f"Created '{output_name}' on {success_count} mesh(es) using {method}"
            if error_count > 0:
                msg += f" ({error_count} failed)"
            self.report({'INFO'}, msg)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Smoothing failed on all objects ({error_count} errors)")
            return {'CANCELLED'}


class FILTERS_OT_compute_attribute_range(Operator):
    """Compute and display the min/max range of the selected attribute across the collection."""
    bl_idname = "filters.compute_attribute_range"
    bl_label = "Compute Range"
    bl_options = {'INTERNAL'}
    
    def execute(self, context):
        settings = getattr(context.scene, 'filters_interpolation_settings', None)
        if not settings:
            return {'CANCELLED'}
        
        coll_name = getattr(settings, 'target_collection', '')
        if not coll_name:
            self.report({'WARNING'}, "No collection selected")
            return {'CANCELLED'}
        
        coll = bpy.data.collections.get(coll_name)
        if not coll:
            self.report({'WARNING'}, f"Collection '{coll_name}' not found")
            return {'CANCELLED'}
        
        source_attr = getattr(settings, 'source_attribute', '')
        if not source_attr:
            self.report({'WARNING'}, "No attribute selected")
            return {'CANCELLED'}
        
        all_values = []
        
        for obj in coll.objects:
            if obj.type != 'MESH':
                continue
            
            mesh = obj.data
            attrs = getattr(mesh, 'attributes', None)
            if not attrs or source_attr not in attrs:
                continue
            
            attr = attrs[source_attr]
            data_type = getattr(attr, 'data_type', '')
            
            try:
                if data_type == 'FLOAT':
                    values = [d.value for d in attr.data]
                    all_values.extend(values)
                elif data_type == 'FLOAT_VECTOR':
                    from mathutils import Vector
                    values = [Vector(d.vector).length for d in attr.data]
                    all_values.extend(values)
                elif data_type in {'INT', 'INT8', 'INT32'}:
                    values = [float(d.value) for d in attr.data]
                    all_values.extend(values)
            except Exception:
                pass
        
        if all_values:
            min_val, max_val = min(all_values), max(all_values)
            self.report({'INFO'}, f"Range: [{min_val:.4f}, {max_val:.4f}] ({len(all_values)} values)")
        else:
            self.report({'WARNING'}, "Could not compute range")
        
        return {'FINISHED'}


__all__ = [
    'FILTERS_OT_apply_interpolation',
    'FILTERS_OT_compute_attribute_range',
]
