"""Attribute interpolation and smoothing utilities for creating derived scalar attributes.

Provides multiple methods:
- Nearest Neighbor Smoothing (kdtree-based) - replaces with nearest neighbor's value
- Inverse Distance Weighting Smoothing (kdtree-based) - weighted average of neighbors
- Shepard Interpolation (VTK-based) - global smooth interpolation
- Laplacian Smoothing - topology-based averaging
"""

import bpy
from mathutils import Vector, kdtree
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def get_attribute_values(obj: bpy.types.Object, attribute_name: str) -> Tuple[List[float], str]:
    """Extract scalar values from a mesh attribute.
    
    Parameters
    ----------
    obj : bpy.types.Object
        Mesh object.
    attribute_name : str
        Name of the attribute.
        
    Returns
    -------
    Tuple[List[float], str]
        (values list, data_type string)
    """
    if obj.type != 'MESH':
        raise ValueError("Object must be a mesh")
    
    mesh = obj.data
    attrs = getattr(mesh, 'attributes', None)
    if not attrs or attribute_name not in attrs:
        raise ValueError(f"Attribute '{attribute_name}' not found")
    
    attr = attrs[attribute_name]
    data_type = getattr(attr, 'data_type', '')
    domain = getattr(attr, 'domain', '')
    
    if domain not in {'POINT', 'VERTEX'}:
        raise ValueError(f"Attribute must be on POINT/VERTEX domain, got: {domain}")
    
    values = []
    if data_type == 'FLOAT':
        values = [d.value for d in attr.data]
    elif data_type == 'FLOAT_VECTOR':
        values = [Vector(d.vector).length for d in attr.data]
    elif data_type in {'INT', 'INT8', 'INT32'}:
        values = [float(d.value) for d in attr.data]
    else:
        raise ValueError(f"Unsupported attribute type: {data_type}")
    
    return values, data_type


def build_kdtree(obj: bpy.types.Object) -> Tuple[kdtree.KDTree, List[Vector]]:
    """Build a KDTree from mesh vertices.
    
    Returns
    -------
    Tuple[kdtree.KDTree, List[Vector]]
        (kdtree, world_positions list)
    """
    mesh = obj.data
    world = obj.matrix_world
    
    positions = []
    for v in mesh.vertices:
        positions.append(world @ v.co)
    
    tree = kdtree.KDTree(len(positions))
    for i, p in enumerate(positions):
        tree.insert(p, i)
    tree.balance()
    
    return tree, positions


def smooth_nearest_neighbor(
    obj: bpy.types.Object,
    attribute_name: str,
    k_neighbors: int = 1
) -> List[float]:
    """Nearest neighbor smoothing - replace each value with the k-th nearest neighbor's value.
    
    This excludes the vertex itself, so k=1 means the closest OTHER vertex.
    
    Parameters
    ----------
    obj : bpy.types.Object
        Mesh object.
    attribute_name : str
        Source attribute name.
    k_neighbors : int
        Which neighbor to use (1 = closest, 2 = second closest, etc.)
        
    Returns
    -------
    List[float]
        Smoothed values.
    """
    values, _ = get_attribute_values(obj, attribute_name)
    tree, positions = build_kdtree(obj)
    
    results = []
    # We need k_neighbors + 1 because the first result is the vertex itself
    k = k_neighbors + 1
    
    for i, pos in enumerate(positions):
        neighbors = tree.find_n(pos, k)
        # Skip self (index 0 in results, which is the query point itself)
        other_neighbors = [(co, idx, dist) for co, idx, dist in neighbors if idx != i]
        
        if other_neighbors and len(other_neighbors) >= k_neighbors:
            # Get the k-th neighbor (0-indexed, so k_neighbors-1)
            _, neighbor_idx, _ = other_neighbors[min(k_neighbors - 1, len(other_neighbors) - 1)]
            results.append(values[neighbor_idx])
        else:
            # Fallback to original value
            results.append(values[i])
    
    return results


def smooth_idw(
    obj: bpy.types.Object,
    attribute_name: str,
    k_neighbors: int = 8,
    power: float = 2.0,
    include_self: bool = False
) -> List[float]:
    """Inverse Distance Weighting smoothing - weighted average of neighbor values.
    
    Parameters
    ----------
    obj : bpy.types.Object
        Mesh object.
    attribute_name : str
        Source attribute name.
    k_neighbors : int
        Number of neighbors to consider.
    power : float
        Distance weighting power (higher = more local).
    include_self : bool
        If True, include the vertex's own value in the average.
        
    Returns
    -------
    List[float]
        Smoothed values.
    """
    values, _ = get_attribute_values(obj, attribute_name)
    tree, positions = build_kdtree(obj)
    
    results = []
    # Request extra neighbors to account for excluding self
    k = k_neighbors + (0 if include_self else 1)
    
    for i, pos in enumerate(positions):
        neighbors = tree.find_n(pos, k)
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for co, idx, dist in neighbors:
            if not include_self and idx == i:
                continue
            
            if dist < 1e-10:
                # Very close point - give it high weight but not infinite
                weight = 1e10
            else:
                weight = 1.0 / (dist ** power)
            
            weighted_sum += values[idx] * weight
            total_weight += weight
        
        if total_weight > 0:
            results.append(weighted_sum / total_weight)
        else:
            results.append(values[i])
    
    return results


def smooth_laplacian(
    obj: bpy.types.Object,
    attribute_name: str,
    iterations: int = 1,
    factor: float = 0.5
) -> List[float]:
    """Laplacian smoothing based on mesh topology (connected vertices).
    
    Parameters
    ----------
    obj : bpy.types.Object
        Mesh object.
    attribute_name : str
        Source attribute name.
    iterations : int
        Number of smoothing iterations.
    factor : float
        Blend factor (0 = no change, 1 = full average).
        
    Returns
    -------
    List[float]
        Smoothed values.
    """
    values, _ = get_attribute_values(obj, attribute_name)
    mesh = obj.data
    
    # Build adjacency from edges
    num_verts = len(mesh.vertices)
    adjacency = [[] for _ in range(num_verts)]
    
    for edge in mesh.edges:
        v0, v1 = edge.vertices
        adjacency[v0].append(v1)
        adjacency[v1].append(v0)
    
    current = values[:]
    
    for _ in range(iterations):
        new_values = []
        for i in range(num_verts):
            neighbors = adjacency[i]
            if neighbors:
                avg = sum(current[n] for n in neighbors) / len(neighbors)
                # Blend between original and average
                new_val = current[i] * (1 - factor) + avg * factor
                new_values.append(new_val)
            else:
                new_values.append(current[i])
        current = new_values
    
    return current


def smooth_gaussian(
    obj: bpy.types.Object,
    attribute_name: str,
    k_neighbors: int = 8,
    sigma: float = 1.0
) -> List[float]:
    """Gaussian smoothing - weighted average with gaussian kernel.
    
    Parameters
    ----------
    obj : bpy.types.Object
        Mesh object.
    attribute_name : str
        Source attribute name.
    k_neighbors : int
        Number of neighbors to consider.
    sigma : float
        Gaussian sigma (standard deviation). Larger = smoother.
        
    Returns
    -------
    List[float]
        Smoothed values.
    """
    import math
    
    values, _ = get_attribute_values(obj, attribute_name)
    tree, positions = build_kdtree(obj)
    
    results = []
    k = k_neighbors + 1  # +1 to include self in neighborhood
    
    for i, pos in enumerate(positions):
        neighbors = tree.find_n(pos, k)
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for co, idx, dist in neighbors:
            # Gaussian weight: exp(-d²/(2σ²))
            weight = math.exp(-(dist ** 2) / (2 * sigma ** 2))
            weighted_sum += values[idx] * weight
            total_weight += weight
        
        if total_weight > 0:
            results.append(weighted_sum / total_weight)
        else:
            results.append(values[i])
    
    return results


def interpolate_shepard_vtk(
    obj: bpy.types.Object,
    attribute_name: str,
    power: float = 2.0,
    sample_dimensions: Tuple[int, int, int] = (50, 50, 50)
) -> List[float]:
    """Shepard interpolation using VTK - creates a smooth field and resamples.
    
    This method creates a volumetric interpolation and samples back,
    which naturally produces smoothing.
    
    Parameters
    ----------
    obj : bpy.types.Object
        Source mesh object.
    attribute_name : str
        Name of the scalar attribute.
    power : float
        Shepard power parameter.
    sample_dimensions : Tuple[int, int, int]
        Resolution of the interpolation volume.
        
    Returns
    -------
    List[float]
        Interpolated/smoothed values.
    """
    vtkShepardMethod = None
    try:
        from vtkmodules.vtkImagingHybrid import vtkShepardMethod
    except ImportError:
        try:
            from vtkmodules.vtkFiltersCore import vtkShepardMethod
        except ImportError:
            pass
    
    if vtkShepardMethod is None:
        raise RuntimeError("vtkShepardMethod not available in this VTK build. Try using IDW or Gaussian smoothing instead.")
    
    try:
        from vtkmodules.vtkFiltersCore import vtkProbeFilter
        from vtkmodules.vtkCommonDataModel import vtkPolyData
        from vtkmodules.vtkCommonCore import vtkPoints, vtkFloatArray
    except ImportError as e:
        raise RuntimeError(f"VTK modules not available: {e}")
    
    values, _ = get_attribute_values(obj, attribute_name)
    mesh = obj.data
    world = obj.matrix_world
    
    # Build VTK point set
    vtk_points = vtkPoints()
    vtk_scalars = vtkFloatArray()
    vtk_scalars.SetName("values")
    
    for i, v in enumerate(mesh.vertices):
        co = world @ v.co
        vtk_points.InsertNextPoint(co.x, co.y, co.z)
        vtk_scalars.InsertNextValue(values[i])
    
    vtk_polydata = vtkPolyData()
    vtk_polydata.SetPoints(vtk_points)
    vtk_polydata.GetPointData().SetScalars(vtk_scalars)
    
    bounds = vtk_polydata.GetBounds()
    
    # Run Shepard interpolation
    shepard = vtkShepardMethod()
    shepard.SetInputData(vtk_polydata)
    shepard.SetPowerParameter(power)
    shepard.SetSampleDimensions(*sample_dimensions)
    shepard.SetModelBounds(bounds)
    shepard.Update()
    
    interpolated_image = shepard.GetOutput()
    
    # Probe back at original positions
    probe_points = vtkPolyData()
    probe_points.SetPoints(vtk_points)
    
    probe = vtkProbeFilter()
    probe.SetInputData(probe_points)
    probe.SetSourceData(interpolated_image)
    probe.Update()
    
    probed_output = probe.GetOutput()
    probed_scalars = probed_output.GetPointData().GetScalars()
    
    results = []
    if probed_scalars:
        for i in range(probed_scalars.GetNumberOfTuples()):
            results.append(probed_scalars.GetValue(i))
    else:
        results = values[:]
    
    return results


def write_attribute_to_mesh(
    obj: bpy.types.Object,
    attribute_name: str,
    values: List[float],
    domain: str = 'POINT'
) -> bool:
    """Write values as a new mesh attribute.
    
    Parameters
    ----------
    obj : bpy.types.Object
        Target mesh object.
    attribute_name : str
        Name for the new attribute.
    values : List[float]
        Values to write.
    domain : str
        Attribute domain ('POINT' or 'FACE').
        
    Returns
    -------
    bool
        True if successful.
    """
    if obj.type != 'MESH':
        return False
    
    mesh = obj.data
    attrs = mesh.attributes
    
    # Remove existing attribute with same name
    if attribute_name in attrs:
        try:
            attrs.remove(attrs[attribute_name])
        except Exception:
            pass
    
    try:
        new_attr = attrs.new(name=attribute_name, type='FLOAT', domain=domain)
        
        expected_len = len(mesh.vertices) if domain == 'POINT' else len(mesh.polygons)
        if len(values) == expected_len:
            new_attr.data.foreach_set('value', values)
        else:
            logger.warning(f"Value count mismatch: {len(values)} vs {expected_len}")
            for i, val in enumerate(values[:len(new_attr.data)]):
                new_attr.data[i].value = val
        
        return True
    except Exception as e:
        logger.error(f"Failed to write attribute: {e}")
        return False


__all__ = [
    'get_attribute_values',
    'build_kdtree',
    'smooth_nearest_neighbor',
    'smooth_idw',
    'smooth_laplacian',
    'smooth_gaussian',
    'interpolate_shepard_vtk',
    'write_attribute_to_mesh',
]

