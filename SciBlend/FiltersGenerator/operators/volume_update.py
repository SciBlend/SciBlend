import bpy
from mathutils import Vector
import os


_RANGE_CACHE = {}
_LAST_RANGE_ERROR = ""


def _ensure_node_group_elementwise_less_than():
    ng = bpy.data.node_groups.get("Element-wise LESS_THAN")
    if ng:
        return ng
    ng = bpy.data.node_groups.new(type='ShaderNodeTree', name="Element-wise LESS_THAN")
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    comb = ng.nodes.new('ShaderNodeCombineXYZ')
    m0 = ng.nodes.new('ShaderNodeMath'); m0.operation = 'LESS_THAN'
    m1 = ng.nodes.new('ShaderNodeMath'); m1.operation = 'LESS_THAN'
    m2 = ng.nodes.new('ShaderNodeMath'); m2.operation = 'LESS_THAN'
    out_vec = ng.interface.new_socket(name="Vector", in_out='OUTPUT', socket_type='NodeSocketVector')
    in_vec = ng.interface.new_socket(name="Vector", in_out='INPUT', socket_type='NodeSocketVector')
    in_val = ng.interface.new_socket(name="Value", in_out='INPUT', socket_type='NodeSocketFloat')
    ng.links.new(gi.outputs[0], sep.inputs[0])
    ng.links.new(gi.outputs[1], m0.inputs[1])
    ng.links.new(gi.outputs[1], m1.inputs[1])
    ng.links.new(gi.outputs[1], m2.inputs[1])
    ng.links.new(sep.outputs[0], m0.inputs[0])
    ng.links.new(sep.outputs[1], m1.inputs[0])
    ng.links.new(sep.outputs[2], m2.inputs[0])
    ng.links.new(m0.outputs[0], comb.inputs[0])
    ng.links.new(m1.outputs[0], comb.inputs[1])
    ng.links.new(m2.outputs[0], comb.inputs[2])
    ng.links.new(comb.outputs[0], go.inputs[0])
    return ng


def _ensure_node_group_elementwise_greater_than():
    ng = bpy.data.node_groups.get("Element-wise GREATER_THAN")
    if ng:
        return ng
    ng = bpy.data.node_groups.new(type='ShaderNodeTree', name="Element-wise GREATER_THAN")
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    comb = ng.nodes.new('ShaderNodeCombineXYZ')
    m0 = ng.nodes.new('ShaderNodeMath'); m0.operation = 'GREATER_THAN'
    m1 = ng.nodes.new('ShaderNodeMath'); m1.operation = 'GREATER_THAN'
    m2 = ng.nodes.new('ShaderNodeMath'); m2.operation = 'GREATER_THAN'
    out_vec = ng.interface.new_socket(name="Vector", in_out='OUTPUT', socket_type='NodeSocketVector')
    in_vec = ng.interface.new_socket(name="Vector", in_out='INPUT', socket_type='NodeSocketVector')
    in_val = ng.interface.new_socket(name="Value", in_out='INPUT', socket_type='NodeSocketFloat')
    ng.links.new(gi.outputs[0], sep.inputs[0])
    ng.links.new(gi.outputs[1], m0.inputs[1])
    ng.links.new(gi.outputs[1], m1.inputs[1])
    ng.links.new(gi.outputs[1], m2.inputs[1])
    ng.links.new(sep.outputs[0], m0.inputs[0])
    ng.links.new(sep.outputs[1], m1.inputs[0])
    ng.links.new(sep.outputs[2], m2.inputs[0])
    ng.links.new(m0.outputs[0], comb.inputs[0])
    ng.links.new(m1.outputs[0], comb.inputs[1])
    ng.links.new(m2.outputs[0], comb.inputs[2])
    ng.links.new(comb.outputs[0], go.inputs[0])
    return ng


def _ensure_node_group_slice_cube():
    ng = bpy.data.node_groups.get("Slice Cube")
    if ng:
        return ng
    lt = _ensure_node_group_elementwise_less_than()
    gt = _ensure_node_group_elementwise_greater_than()
    ng = bpy.data.node_groups.new(type='ShaderNodeTree', name="Slice Cube")
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')
    group_lt = ng.nodes.new('ShaderNodeGroup'); group_lt.node_tree = lt
    group_gt = ng.nodes.new('ShaderNodeGroup'); group_gt.node_tree = gt
    try:
        group_lt.inputs[1].default_value = -1.0
    except Exception:
        pass
    try:
        group_gt.inputs[1].default_value = 1.0
    except Exception:
        pass
    vadd = ng.nodes.new('ShaderNodeVectorMath'); vadd.operation = 'ADD'
    less = ng.nodes.new('ShaderNodeMath'); less.operation = 'LESS_THAN'; less.inputs[1].default_value = 0.5
    sep2 = ng.nodes.new('ShaderNodeSeparateXYZ')
    absx = ng.nodes.new('ShaderNodeMath'); absx.operation = 'ABSOLUTE'
    absy = ng.nodes.new('ShaderNodeMath'); absy.operation = 'ABSOLUTE'
    absz = ng.nodes.new('ShaderNodeMath'); absz.operation = 'ABSOLUTE'
    max1 = ng.nodes.new('ShaderNodeMath'); max1.operation = 'MAXIMUM'
    max2 = ng.nodes.new('ShaderNodeMath'); max2.operation = 'MAXIMUM'
    cmp1 = ng.nodes.new('ShaderNodeMath'); cmp1.operation = 'COMPARE'; cmp1.inputs[1].default_value = 0.0; cmp1.inputs[2].default_value = 0.1
    cmp2 = ng.nodes.new('ShaderNodeMath'); cmp2.operation = 'COMPARE'; cmp2.inputs[2].default_value = 0.5
    transp = ng.nodes.new('ShaderNodeBsdfTransparent')
    mix = ng.nodes.new('ShaderNodeMixShader')
    out_shader = ng.interface.new_socket(name="Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
    in_shader = ng.interface.new_socket(name="Shader", in_out='INPUT', socket_type='NodeSocketShader')
    in_slice_obj = ng.interface.new_socket(name="Slicing Object", in_out='INPUT', socket_type='NodeSocketVector')
    in_invert = ng.interface.new_socket(name="Invert", in_out='INPUT', socket_type='NodeSocketBool')
    ng.links.new(gi.outputs[1], group_lt.inputs[0])
    ng.links.new(gi.outputs[1], group_gt.inputs[0])
    ng.links.new(group_lt.outputs[0], vadd.inputs[0])
    ng.links.new(group_gt.outputs[0], vadd.inputs[1])
    ng.links.new(gi.outputs[2], less.inputs[0])
    ng.links.new(vadd.outputs[0], sep2.inputs[0])
    ng.links.new(sep2.outputs[0], absx.inputs[0])
    ng.links.new(sep2.outputs[1], absy.inputs[0])
    ng.links.new(sep2.outputs[2], absz.inputs[0])
    ng.links.new(absx.outputs[0], max1.inputs[0])
    ng.links.new(absy.outputs[0], max1.inputs[1])
    ng.links.new(max1.outputs[0], max2.inputs[0])
    ng.links.new(absz.outputs[0], max2.inputs[1])
    ng.links.new(max2.outputs[0], cmp1.inputs[0])
    ng.links.new(less.outputs[0], cmp2.inputs[0])
    ng.links.new(cmp1.outputs[0], cmp2.inputs[1])
    ng.links.new(transp.outputs[0], mix.inputs[1])
    ng.links.new(gi.outputs[0], mix.inputs[2])
    ng.links.new(cmp2.outputs[0], mix.inputs[0])
    ng.links.new(mix.outputs[0], go.inputs[0])
    return ng


def _ensure_slice_cube_material():
    mat_name = "SliceCube_Transparent"
    mat = bpy.data.materials.get(mat_name)
    if mat:
        return mat
    
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    
    for node in mat.node_tree.nodes:
        mat.node_tree.nodes.remove(node)
    mat.node_tree.color_tag = 'NONE'
    mat.node_tree.description = ""
    mat.node_tree.default_group_node_width = 140
    
    principled_bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    principled_bsdf.name = "Principled BSDF"
    principled_bsdf.distribution = 'MULTI_GGX'
    principled_bsdf.subsurface_method = 'RANDOM_WALK'
    
    principled_bsdf.inputs[0].default_value = (0.800000011920929, 0.800000011920929, 0.800000011920929, 1.0)
    principled_bsdf.inputs[1].default_value = 0.0
    principled_bsdf.inputs[2].default_value = 0.5
    principled_bsdf.inputs[3].default_value = 1.5
    principled_bsdf.inputs[4].default_value = 0.0
    principled_bsdf.inputs[5].default_value = (0.0, 0.0, 0.0)
    principled_bsdf.inputs[7].default_value = 0.0
    principled_bsdf.inputs[8].default_value = 0.0
    principled_bsdf.inputs[9].default_value = (1.0, 0.20000000298023224, 0.10000000149011612)
    principled_bsdf.inputs[10].default_value = 0.05000000074505806
    principled_bsdf.inputs[12].default_value = 0.0
    principled_bsdf.inputs[13].default_value = 0.5
    principled_bsdf.inputs[14].default_value = (1.0, 1.0, 1.0, 1.0)
    principled_bsdf.inputs[15].default_value = 0.0
    principled_bsdf.inputs[16].default_value = 0.0
    principled_bsdf.inputs[17].default_value = (0.0, 0.0, 0.0)
    principled_bsdf.inputs[18].default_value = 0.0
    principled_bsdf.inputs[19].default_value = 0.0
    principled_bsdf.inputs[20].default_value = 0.029999999329447746
    principled_bsdf.inputs[21].default_value = 1.5
    principled_bsdf.inputs[22].default_value = (1.0, 1.0, 1.0, 1.0)
    principled_bsdf.inputs[23].default_value = (0.0, 0.0, 0.0)
    principled_bsdf.inputs[24].default_value = 0.0
    principled_bsdf.inputs[25].default_value = 0.5
    principled_bsdf.inputs[26].default_value = (1.0, 1.0, 1.0, 1.0)
    principled_bsdf.inputs[27].default_value = (1.0, 1.0, 1.0, 1.0)
    principled_bsdf.inputs[28].default_value = 0.0
    principled_bsdf.inputs[29].default_value = 0.0
    principled_bsdf.inputs[30].default_value = 1.3300000429153442
    
    material_output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    material_output.name = "Material Output"
    material_output.is_active_output = True
    material_output.target = 'ALL'
    material_output.inputs[2].default_value = (0.0, 0.0, 0.0)
    material_output.inputs[3].default_value = 0.0
    
    principled_bsdf.location = (-200.0, 100.0)
    material_output.location = (200.0, 100.0)
    
    principled_bsdf.width, principled_bsdf.height = 240.0, 100.0
    material_output.width, material_output.height = 140.0, 100.0
    
    mat.node_tree.links.new(principled_bsdf.outputs[0], material_output.inputs[0])
    
    mat.blend_method = 'BLEND'
    
    return mat


def _ensure_slice_cube_object(volume_obj: bpy.types.Object) -> bpy.types.Object:
    import hashlib
    vol_hash = hashlib.md5(volume_obj.name.encode()).hexdigest()[:8]
    name = f"Slicer_{vol_hash}"
    
    cube = bpy.data.objects.get(name)
    
    if cube is None or cube.type != 'MESH':
        mesh_name = f"SlicerMesh_{vol_hash}"
        mesh = bpy.data.meshes.new(mesh_name)
        verts = [
            (-1.0, -1.0, -1.0), (1.0, -1.0, -1.0), (1.0, 1.0, -1.0), (-1.0, 1.0, -1.0),
            (-1.0, -1.0,  1.0), (1.0, -1.0,  1.0), (1.0, 1.0,  1.0), (-1.0, 1.0,  1.0),
        ]
        faces = [
            (0, 1, 2, 3), (4, 5, 6, 7),
            (0, 1, 5, 4), (2, 3, 7, 6),
            (1, 2, 6, 5), (0, 3, 7, 4),
        ]
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        cube = bpy.data.objects.new(name, mesh)
        
        colls = volume_obj.users_collection
        if colls:
            colls[0].objects.link(cube)
        else:
            bpy.context.collection.objects.link(cube)
        
        cube.display_type = 'WIRE'
        cube.show_in_front = True
        cube.hide_viewport = False
        cube.hide_render = True
        mat = _ensure_slice_cube_material()
        if cube.data.materials:
            cube.data.materials[0] = mat
        else:
            cube.data.materials.append(mat)
    bb = [Vector(v) for v in volume_obj.bound_box]
    min_local = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    max_local = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    center_local = (min_local + max_local) * 0.5
    size_local = max_local - min_local
    mw = volume_obj.matrix_world.copy()
    world_center = mw @ center_local
    mw.translation = world_center
    cube.matrix_world = mw
    try:
        vs = [Vector(v.co) for v in cube.data.vertices]
        hx = max(abs(v.x) for v in vs) or 1.0
        hy = max(abs(v.y) for v in vs) or 1.0
        hz = max(abs(v.z) for v in vs) or 1.0
    except Exception:
        hx = hy = hz = 1.0
    scale_vec = Vector((
        (size_local.x * 0.5) / hx,
        (size_local.y * 0.5) / hy,
        (size_local.z * 0.5) / hz,
    ))
    try:
        cube.scale = scale_vec
    except Exception:
        pass
    
    mat = _ensure_slice_cube_material()
    if cube.data.materials:
        cube.data.materials[0] = mat
    else:
        cube.data.materials.append(mat)
    
    return cube

def _get_sequence_files(settings) -> list:
    dirpath = getattr(settings, 'last_import_dir', '') or ''
    try:
        files = [f.name for f in settings.last_import_files] if len(settings.last_import_files) else []
    except Exception:
        files = []
    if (not files) and getattr(getattr(settings, 'volume_object', None), 'data', None):
        fp = getattr(settings.volume_object.data, 'filepath', '')
        if fp:
            abs_fp = bpy.path.abspath(fp)
            if os.path.exists(abs_fp):
                dirpath = os.path.dirname(abs_fp)
                files = [os.path.basename(abs_fp)]
    return [dirpath, files]


def _resolve_vdb_filepath_for_frame(context, settings) -> str:
    dirpath, files = _get_sequence_files(settings)
    if not files:
        return ''
    frame = getattr(getattr(context, 'scene', None), 'frame_current', 1) or 1
    start = 1
    offset = 0
    try:
        vd = getattr(settings.volume_object, 'data', None)
        if vd is not None:
            start = getattr(vd, 'frame_start', start) or start
            offset = getattr(vd, 'frame_offset', offset) or offset
    except Exception:
        pass
    idx = frame - start + offset
    if idx < 0:
        idx = 0
    if idx >= len(files):
        idx = len(files) - 1
    name = files[int(idx)]
    try:
        return bpy.path.abspath(bpy.path.relpath(bpy.path.join(dirpath, name))) if hasattr(bpy.path, 'join') else os.path.join(dirpath, name)
    except Exception:
        return os.path.join(dirpath, name)


def _compute_vdb_grid_min_max(filepath: str, grid_name: str, component_mode: str = 'MAG'):
    global _LAST_RANGE_ERROR
    _LAST_RANGE_ERROR = ""
    if not filepath:
        _LAST_RANGE_ERROR = "No filepath resolved for current frame."
        return None
    if not os.path.exists(filepath):
        _LAST_RANGE_ERROR = f"File not found: {filepath}"
        return None
    if not grid_name:
        _LAST_RANGE_ERROR = "No grid selected."
        return None
    key = (filepath, grid_name, component_mode)
    if key in _RANGE_CACHE:
        return _RANGE_CACHE[key]
    try:
        try:
            import openvdb as vdb
        except Exception as e:
            _LAST_RANGE_ERROR = f"openvdb module not available: {e}"
            return None
        try:
            grid = vdb.read(filepath, grid_name)
        except Exception:
            _LAST_RANGE_ERROR = f"Grid '{grid_name}' not found or cannot be read from {os.path.basename(filepath)}"
            return None

        min_v = float('inf')
        max_v = float('-inf')

        values_iter = None
        for getter in (
            getattr(grid, 'citerOnValues', None),
            getattr(grid, 'iterOnValues', None),
            getattr(grid, 'citerAllValues', None),
            getattr(grid, 'iterAllValues', None),
        ):
            if callable(getter):
                try:
                    values_iter = getter()
                    break
                except Exception:
                    continue
        if values_iter is None:
            try:
                values_iter = grid.values()
            except Exception:
                pass
        if values_iter is None:
            _LAST_RANGE_ERROR = "Cannot iterate grid values."
            stats = {'min': float('inf'), 'max': float('-inf')}
            def _accumulate(x):
                try:
                    v = x
                    if isinstance(v, (list, tuple)):
                        s = 0.0
                        for c in v:
                            s += float(c) * float(c)
                        v = s ** 0.5
                    else:
                        v = float(v)
                    if v < stats['min']:
                        stats['min'] = v
                    if v > stats['max']:
                        stats['max'] = v
                except Exception:
                    pass
                return x
            try:
                if hasattr(grid, 'mapOn') and callable(getattr(grid, 'mapOn')):
                    grid.mapOn(_accumulate)
                    min_v, max_v = stats['min'], stats['max']
                elif hasattr(grid, 'mapAll') and callable(getattr(grid, 'mapAll')):
                    grid.mapAll(_accumulate)
                    min_v, max_v = stats['min'], stats['max']
                else:
                    try:
                        bb = grid.evalActiveVoxelBoundingBox()
                        if not bb or not isinstance(bb, (tuple, list)) or len(bb) != 2:
                            return None
                        (imin, jmin, kmin), (imax, jmax, kmax) = bb
                        shape = (imax - imin + 1, jmax - jmin + 1, kmax - kmin + 1)
                        import numpy as np
                        arr = None
                        try:
                            arr = np.empty(shape + (3,), dtype=np.float32)
                            grid.copyToArray(arr, ijk=(imin, jmin, kmin))
                            vec = arr.reshape(-1, 3).astype(np.float64)
                            if component_mode == 'X':
                                comp = vec[:, 0]
                            elif component_mode == 'Y':
                                comp = vec[:, 1]
                            elif component_mode == 'Z':
                                comp = vec[:, 2]
                            else:
                                comp = np.sqrt((vec * vec).sum(axis=1))
                            min_v = float(comp.min(initial=float('inf')))
                            max_v = float(comp.max(initial=float('-inf')))
                        except Exception:
                            arr = np.empty(shape, dtype=np.float32)
                            grid.copyToArray(arr, ijk=(imin, jmin, kmin))
                            bg = None
                            try:
                                bg = getattr(grid, 'background', None)
                            except Exception:
                                bg = None
                            if bg is not None:
                                try:
                                    bgf = float(bg)
                                    mask = arr != bgf
                                    if mask.any():
                                        min_v = float(arr[mask].min(initial=float('inf')))
                                        max_v = float(arr[mask].max(initial=float('-inf')))
                                    else:
                                        min_v = float(arr.min(initial=float('inf')))
                                        max_v = float(arr.max(initial=float('-inf')))
                                except Exception:
                                    min_v = float(arr.min(initial=float('inf')))
                                    max_v = float(arr.max(initial=float('-inf')))
                            else:
                                min_v = float(arr.min(initial=float('inf')))
                                max_v = float(arr.max(initial=float('-inf')))
                    except Exception:
                        return None
            except Exception:
                return None
        else:
            for item in values_iter:
                try:
                    val = getattr(item, 'value', item)
                except Exception:
                    val = item
                try:
                    if isinstance(val, (list, tuple)):
                        if component_mode == 'X':
                            val = float(val[0])
                        elif component_mode == 'Y':
                            val = float(val[1])
                        elif component_mode == 'Z':
                            val = float(val[2])
                        else:
                            comp = 0.0
                            for c in val:
                                comp += float(c) * float(c)
                            val = comp ** 0.5
                    else:
                        val = float(val)
                except Exception:
                    continue
                if val < min_v:
                    min_v = val
                if val > max_v:
                    max_v = val

        if min_v is float('inf') or max_v is float('-inf'):
            _LAST_RANGE_ERROR = "Grid has no values."
            return None
        result = (float(min_v), float(max_v))
        _RANGE_CACHE[key] = result
        return result
    except Exception as e:
        _LAST_RANGE_ERROR = f"Unexpected error: {e}"
        return None


def ensure_volume_material_for_object(context, obj, item):
    """
    Create or update a volume material for a specific object using settings from a VolumeItem.
    """
    mat_name = f"SciBlend_Volume_{obj.name}"
    mat = None
    for m in bpy.data.materials:
        if m.name == mat_name:
            mat = m
            break
    if not mat:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (500, 0)
    attr = nt.nodes.new('ShaderNodeAttribute')
    attr.attribute_type = 'GEOMETRY'
    attr.attribute_name = item.grid_name or "density"
    attr.location = (-600, 0)

    sep_xyz = nt.nodes.new('ShaderNodeSeparateXYZ'); sep_xyz.location = (-500, -120)
    vec_len = nt.nodes.new('ShaderNodeVectorMath'); vec_len.operation = 'LENGTH'; vec_len.location = (-500, -240)

    mapr = nt.nodes.new('ShaderNodeMapRange'); mapr.location = (-400, 0)


    try:
        if getattr(item, 'auto_range', False) and getattr(item, 'grid_name', ''):
            fp = _resolve_vdb_filepath_for_frame(context, item)
            if not fp and obj and obj.data and hasattr(obj.data, 'filepath'):
                fp = bpy.path.abspath(obj.data.filepath)
            rng = _compute_vdb_grid_min_max(fp, item.grid_name, getattr(item, 'component_mode', 'MAG'))
            if rng:
                item.from_min, item.from_max = rng
                print(f"Auto-computed range for '{item.grid_name}': [{item.from_min:.6e}, {item.from_max:.6e}]")
            else:
                global _LAST_RANGE_ERROR
                if _LAST_RANGE_ERROR:
                    print(f"Could not compute auto range: {_LAST_RANGE_ERROR}")
    except Exception as e:
        print(f"Error computing auto range: {e}")
    try:
        mapr.clamp = True
    except Exception:
        pass
    mapr.inputs[1].default_value = item.from_min
    mapr.inputs[2].default_value = item.from_max
    mapr.inputs[3].default_value = 0.0
    mapr.inputs[4].default_value = 1.0
    
    from ..utils.volume_node_groups import get_volume_density_node_group
    density_ctrl = nt.nodes.new('ShaderNodeGroup')
    density_ctrl.node_tree = get_volume_density_node_group()
    density_ctrl.location = (-100, -50)
    density_ctrl.inputs['Enable Lower Clip'].default_value = item.clip_min
    density_ctrl.inputs['Enable Upper Clip'].default_value = item.clip_max
    density_ctrl.inputs['Base Density'].default_value = item.alpha_baseline
    density_ctrl.inputs['Scale Factor'].default_value = item.alpha_multiplier
    density_ctrl.inputs['Opacity Unit Distance'].default_value = item.opacity_unit_distance
    density_ctrl.inputs['Step Size'].default_value = item.step_size
    
    pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.location = (200, 0)
    pv.inputs[4].default_value = item.anisotropy
    pv.inputs[6].default_value = item.emission_strength
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.location = (-150, 200)
    try:
        from ..utils.colormaps import apply_colormap_to_ramp
        apply_colormap_to_ramp(item.colormap, cr)
    except Exception:
        pass
    tex = nt.nodes.new('ShaderNodeTexCoord'); tex.location = (-200, -250)
    slice_group = nt.nodes.new('ShaderNodeGroup'); slice_group.node_tree = _ensure_node_group_slice_cube(); slice_group.location = (350, -200)

    src_for_map = None
    vout = None
    try:
        vout = attr.outputs.get('Vector') if hasattr(attr.outputs, 'get') else None
        if vout is None:
            vout = next((o for o in attr.outputs if getattr(o, 'type', '') == 'VECTOR'), None)
    except Exception:
        vout = None
    
    if vout is not None:
        nt.links.new(vout, sep_xyz.inputs[0])
        nt.links.new(vout, vec_len.inputs[0])
        mode = getattr(item, 'component_mode', 'MAG')
        if mode == 'X':
            src_for_map = sep_xyz.outputs[0]
        elif mode == 'Y':
            src_for_map = sep_xyz.outputs[1]
        elif mode == 'Z':
            src_for_map = sep_xyz.outputs[2]
        else:
            try:
                src_for_map = vec_len.outputs['Value']
            except Exception:
                src_for_map = vec_len.outputs[1] if len(vec_len.outputs) > 1 else vec_len.outputs[0]
    else:
        try:
            src_for_map = next((o for o in attr.outputs if getattr(o, 'type', '') == 'VALUE'), None)
        except Exception:
            src_for_map = None
    
    if src_for_map is not None:
        nt.links.new(src_for_map, mapr.inputs[0])

    nt.links.new(mapr.outputs[0], density_ctrl.inputs['Normalized Value'])
    nt.links.new(mapr.outputs[0], cr.inputs[0])
    nt.links.new(cr.outputs[0], pv.inputs[0])
    nt.links.new(density_ctrl.outputs['Density'], pv.inputs[2])
    nt.links.new(pv.outputs[0], slice_group.inputs[0])
    nt.links.new(tex.outputs[3], slice_group.inputs[1])
    nt.links.new(slice_group.outputs[0], out.inputs[1])

    cube = _ensure_slice_cube_object(obj)
    try:
        tex.object = cube
    except Exception as e:
        print(f"Error setting tex.object: {e}")
    try:
        item.slice_object = cube
    except Exception as e:
        print(f"Error setting slice_object: {e}")

    if obj.data and hasattr(obj.data, 'materials'):
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
    
    if obj.data and hasattr(obj.data, 'render'):
        try:
            obj.data.render.space = 'WORLD'
            obj.data.render.step_size = item.step_size
        except Exception as e:
            print(f"Could not set volume step size: {e}")

    return mat


def update_volume_item_material(context, item):
    """
    Update the material for a specific volume item.
    """
    from ..properties import volume_item
    
    if not item.volume_object or item.volume_object.type != 'VOLUME':
        return None
    
    if not item.grid_name or item.grid_name == 'NONE':
        return None
    
    original_flag = volume_item._UPDATING_NODES
    volume_item._UPDATING_NODES = True
    
    try:
        try:
            if getattr(item, 'auto_range', False) and getattr(item, 'grid_name', ''):
                fp = _resolve_vdb_filepath_for_frame(context, item)
                if not fp and item.volume_object and item.volume_object.data and hasattr(item.volume_object.data, 'filepath'):
                    fp = bpy.path.abspath(item.volume_object.data.filepath)
                rng = _compute_vdb_grid_min_max(fp, item.grid_name, getattr(item, 'component_mode', 'MAG'))
                if rng:
                    item.from_min, item.from_max = rng
                    print(f"Auto-computed range for '{item.grid_name}': [{item.from_min:.6e}, {item.from_max:.6e}]")
                else:
                    global _LAST_RANGE_ERROR
                    if _LAST_RANGE_ERROR:
                        print(f"Could not compute auto range: {_LAST_RANGE_ERROR}")
        except Exception as e:
            print(f"Error computing auto range: {e}")
        
        mat_name = f"SciBlend_Volume_{item.volume_object.name}"
        mat = bpy.data.materials.get(mat_name)
        
        if not mat or not mat.use_nodes:
            mat = ensure_volume_material_for_object(context, item.volume_object, item)
            return mat
        
        nt = mat.node_tree
        
        attr = next((n for n in nt.nodes if n.type == 'ATTRIBUTE'), None)
        if attr:
            attr.attribute_name = item.grid_name
        
        mapr = next((n for n in nt.nodes if n.type == 'MAP_RANGE'), None)
        if mapr:
            mapr.inputs[1].default_value = item.from_min
            mapr.inputs[2].default_value = item.from_max
        
        sep_xyz = next((n for n in nt.nodes if n.type == 'SEPARATE_XYZ'), None)
        vec_len = next((n for n in nt.nodes if n.type == 'VECT_MATH' and getattr(n, 'operation', '') == 'LENGTH'), None)
        
        if mapr and attr and sep_xyz and vec_len:
            try:
                for link in list(mapr.inputs[0].links):
                    nt.links.remove(link)
            except Exception:
                pass
            try:
                for link in list(sep_xyz.inputs[0].links):
                    nt.links.remove(link)
                for link in list(vec_len.inputs[0].links):
                    nt.links.remove(link)
            except Exception:
                pass
            
            vout = None
            try:
                vout = attr.outputs.get('Vector') if hasattr(attr.outputs, 'get') else None
                if vout is None:
                    vout = next((o for o in attr.outputs if getattr(o, 'type', '') == 'VECTOR'), None)
            except Exception:
                vout = None
            
            src_for_map = None
            if vout is not None:
                nt.links.new(vout, sep_xyz.inputs[0])
                nt.links.new(vout, vec_len.inputs[0])
                mode = getattr(item, 'component_mode', 'MAG')
                if mode == 'X':
                    src_for_map = sep_xyz.outputs[0]
                elif mode == 'Y':
                    src_for_map = sep_xyz.outputs[1]
                elif mode == 'Z':
                    src_for_map = sep_xyz.outputs[2]
                else:
                    try:
                        src_for_map = vec_len.outputs['Value']
                    except Exception:
                        src_for_map = vec_len.outputs[1] if len(vec_len.outputs) > 1 else vec_len.outputs[0]
            else:
                try:
                    src_for_map = next((o for o in attr.outputs if getattr(o, 'type', '') == 'VALUE'), None)
                except Exception:
                    src_for_map = None
            
            if src_for_map is not None:
                nt.links.new(src_for_map, mapr.inputs[0])
        
        density_ctrl = next((n for n in nt.nodes if n.type == 'GROUP' and n.node_tree and n.node_tree.name == 'SciBlend_Volume_Density'), None)
        if density_ctrl:
            try:
                density_ctrl.inputs['Enable Lower Clip'].default_value = item.clip_min
                density_ctrl.inputs['Enable Upper Clip'].default_value = item.clip_max
                density_ctrl.inputs['Base Density'].default_value = item.alpha_baseline
                density_ctrl.inputs['Scale Factor'].default_value = item.alpha_multiplier
                
                if 'Opacity Unit Distance' in density_ctrl.inputs:
                    density_ctrl.inputs['Opacity Unit Distance'].default_value = item.opacity_unit_distance
                if 'Step Size' in density_ctrl.inputs:
                    density_ctrl.inputs['Step Size'].default_value = item.step_size
            except Exception as e:
                print(f"Error updating density controller: {e}")
        else:
            print("WARNING: Density controller node not found. Material may need to be regenerated.")
        
        pv = next((n for n in nt.nodes if n.type == 'VOLUME_PRINCIPLED'), None)
        if pv:
            pv.inputs[4].default_value = item.anisotropy
            pv.inputs[6].default_value = item.emission_strength
        
        cr = next((n for n in nt.nodes if n.type == 'VALTORGB'), None)
        if cr:
            try:
                from ..utils.colormaps import apply_colormap_to_ramp
                apply_colormap_to_ramp(item.colormap, cr)
            except Exception:
                pass
        
        tex = next((n for n in nt.nodes if n.type == 'TEX_COORD'), None)
        if tex:
            current_tex_obj = getattr(tex, 'object', None)
            
            import hashlib
            vol_hash = hashlib.md5(item.volume_object.name.encode()).hexdigest()[:8]
            expected_slicer_name = f"Slicer_{vol_hash}"
            
            needs_update = (
                current_tex_obj is None or 
                current_tex_obj.name != expected_slicer_name or
                current_tex_obj.type != 'MESH'
            )
            
            if needs_update:
                cube = _ensure_slice_cube_object(item.volume_object)
                try:
                    tex.object = cube
                except Exception as e:
                    print(f"Error setting tex.object: {e}")
                
                try:
                    item.slice_object = cube
                except Exception as e:
                    print(f"Error setting item.slice_object: {e}")
            else:
                cube = current_tex_obj
        
        slice_group = next((n for n in nt.nodes if n.type == 'GROUP' and n.node_tree and n.node_tree.name == 'Slice Cube'), None)
        if slice_group:
            try:
                idx = 2
                slice_group.inputs[idx].default_value = bool(item.slice_invert)
                
                if tex:
                    tex_output = tex.outputs[3]
                    slice_input = slice_group.inputs[1]
                    is_connected = any(link.to_socket == slice_input for link in nt.links)
                    if not is_connected:
                        nt.links.new(tex_output, slice_input)
            except Exception as e:
                print(f"Error updating slice group: {e}")
        
        if item.volume_object and item.volume_object.data and hasattr(item.volume_object.data, 'materials'):
            if len(item.volume_object.data.materials) == 0:
                item.volume_object.data.materials.append(mat)
            elif item.volume_object.data.materials[0] != mat:
                item.volume_object.data.materials[0] = mat
        
        if item.volume_object and item.volume_object.data and hasattr(item.volume_object.data, 'render'):
            try:
                item.volume_object.data.render.space = 'WORLD'
                item.volume_object.data.render.step_size = item.step_size
            except Exception as e:
                print(f"Could not set volume step size: {e}")
        
        return mat
    finally:
        volume_item._UPDATING_NODES = original_flag


class FILTERS_OT_volume_update_material(bpy.types.Operator):
    """
    Update the material for the active volume item.
    """
    bl_idname = "filters.volume_update_material"
    bl_label = "Update Material"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..properties.volume_settings import get_active_volume_item
        
        item = get_active_volume_item(context)
        if not item:
            self.report({'ERROR'}, "No active volume item")
            return {'CANCELLED'}
        
        if not item.volume_object or item.volume_object.type != 'VOLUME':
            self.report({'ERROR'}, "Select a Volume object")
            return {'CANCELLED'}
        
        update_volume_item_material(context, item)
        
        return {'FINISHED'}


class FILTERS_OT_volume_compute_range(bpy.types.Operator):
    """
    Compute the value range for the active volume item.
    """
    bl_idname = "filters.volume_compute_range"
    bl_label = "Compute Range"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..properties.volume_settings import get_active_volume_item
        
        item = get_active_volume_item(context)
        if not item:
            self.report({'ERROR'}, "No active volume item")
            return {'CANCELLED'}
        
        if not item.volume_object or item.volume_object.type != 'VOLUME' or not item.grid_name:
            self.report({'ERROR'}, "Select volume and grid")
            return {'CANCELLED'}
        
        try:
            fp = _resolve_vdb_filepath_for_frame(context, item)
            if not fp and item.volume_object and item.volume_object.data and hasattr(item.volume_object.data, 'filepath'):
                fp = bpy.path.abspath(item.volume_object.data.filepath)
            
            rng = _compute_vdb_grid_min_max(fp, item.grid_name, getattr(item, 'component_mode', 'MAG'))
            
            if not rng:
                global _LAST_RANGE_ERROR
                error_msg = _LAST_RANGE_ERROR or "Could not compute range"
                self.report({'WARNING'}, error_msg)
                return {'CANCELLED'}
            
            item.from_min, item.from_max = rng
            self.report({'INFO'}, f"Range computed: [{item.from_min:.6e}, {item.from_max:.6e}]")
        except Exception as e:
            self.report({'ERROR'}, f"Error computing range: {e}")
            return {'CANCELLED'}
        
        if item.auto_range:
            bpy.ops.filters.volume_update_material('INVOKE_DEFAULT')
        
        return {'FINISHED'}


class FILTERS_OT_volume_cleanup_slicers(bpy.types.Operator):
    """
    Clean up orphaned slicer objects for the active volume.
    """
    bl_idname = "filters.volume_cleanup_slicers"
    bl_label = "Clean Up Orphaned Slicers"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..properties.volume_settings import get_active_volume_item
        
        item = get_active_volume_item(context)
        if not item or not item.volume_object:
            self.report({'ERROR'}, "No active volume item")
            return {'CANCELLED'}
        
        import hashlib
        vol_hash = hashlib.md5(item.volume_object.name.encode()).hexdigest()[:8]
        correct_slicer_name = f"Slicer_{vol_hash}"
        
        removed_count = 0
        removed_names = []
        
        for obj in list(bpy.data.objects):
            if 'Slicer' in obj.name and obj.name != correct_slicer_name:
                if obj.name.startswith('Slicer_') and (
                    item.volume_object.name[:30] in obj.name or
                    vol_hash in obj.name
                ):
                    removed_names.append(obj.name)
                    bpy.data.objects.remove(obj, do_unlink=True)
                    removed_count += 1
        
        if removed_count > 0:
            self.report({'INFO'}, f"Removed {removed_count} orphaned slicers: {', '.join(removed_names[:3])}")
        else:
            self.report({'INFO'}, f"No orphaned slicers found for {item.volume_object.name}")
        
        return {'FINISHED'}


def register():
    bpy.utils.register_class(FILTERS_OT_volume_update_material)
    bpy.utils.register_class(FILTERS_OT_volume_compute_range)
    bpy.utils.register_class(FILTERS_OT_volume_cleanup_slicers)


def unregister():
    bpy.utils.unregister_class(FILTERS_OT_volume_cleanup_slicers)
    bpy.utils.unregister_class(FILTERS_OT_volume_compute_range)
    bpy.utils.unregister_class(FILTERS_OT_volume_update_material) 