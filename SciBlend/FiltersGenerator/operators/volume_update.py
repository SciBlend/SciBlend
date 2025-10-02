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
    name = "slice cube"
    cube = bpy.data.objects.get(name)
    if cube is None or cube.type != 'MESH':
        mesh = bpy.data.meshes.new("SliceCubeMesh")
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
        if fp and os.path.exists(fp):
            dirpath = os.path.dirname(fp)
            files = [os.path.basename(fp)]
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


def _compute_vdb_grid_min_max(filepath: str, grid_name: str):
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
    key = (filepath, grid_name)
    if key in _RANGE_CACHE:
        return _RANGE_CACHE[key]
    try:
        try:
            import pyopenvdb as vdb
        except Exception:
            try:
                import openvdb as vdb
            except Exception:
                _LAST_RANGE_ERROR = "pyopenvdb/openvdb is not installed."
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
                            mags = np.sqrt((vec * vec).sum(axis=1))
                            min_v = float(mags.min(initial=float('inf')))
                            max_v = float(mags.max(initial=float('-inf')))
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


def ensure_volume_material_for_object(context, obj, settings):
    mat_name = "SciBlend_Volume"
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
    attr.attribute_name = settings.grid_name or "density"
    attr.location = (-600, 0)
    mapr = nt.nodes.new('ShaderNodeMapRange'); mapr.location = (-400, 0)
    try:
        if getattr(settings, 'auto_range', False) and getattr(settings, 'grid_name', ''):
            fp = _resolve_vdb_filepath_for_frame(context, settings)
            rng = _compute_vdb_grid_min_max(fp, settings.grid_name)
            if rng:
                settings.from_min, settings.from_max = rng
    except Exception:
        pass
    mapr.inputs[1].default_value = settings.from_min
    mapr.inputs[2].default_value = settings.from_max
    mapr.inputs[3].default_value = 0.0
    mapr.inputs[4].default_value = 1.0
    math_mul = nt.nodes.new('ShaderNodeMath'); math_mul.operation = 'MULTIPLY'; math_mul.location = (-100, -50)
    math_mul.inputs[1].default_value = settings.density_scale
    pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.location = (200, 0)
    pv.inputs[4].default_value = settings.anisotropy
    pv.inputs[6].default_value = settings.emission_strength
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.location = (-150, 200)
    try:
        from ..utils.colormaps import apply_colormap_to_ramp
        apply_colormap_to_ramp(settings.colormap, cr)
    except Exception:
        pass
    tex = nt.nodes.new('ShaderNodeTexCoord'); tex.location = (-200, -250)
    slice_group = nt.nodes.new('ShaderNodeGroup'); slice_group.node_tree = _ensure_node_group_slice_cube(); slice_group.location = (350, -200)

    nt.links.new(attr.outputs[0], mapr.inputs[0])
    nt.links.new(mapr.outputs[0], math_mul.inputs[0])
    nt.links.new(mapr.outputs[0], cr.inputs[0])
    nt.links.new(cr.outputs[0], pv.inputs[0])
    nt.links.new(math_mul.outputs[0], pv.inputs[2])
    nt.links.new(pv.outputs[0], slice_group.inputs[0])
    nt.links.new(tex.outputs[3], slice_group.inputs[1])
    nt.links.new(slice_group.outputs[0], out.inputs[1])

    cube = _ensure_slice_cube_object(obj)
    try:
        tex.object = cube
    except Exception:
        pass
    try:
        settings.slice_object = cube
    except Exception:
        pass

    if obj.data and hasattr(obj.data, 'materials'):
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

    return mat


class FILTERS_OT_volume_update_material(bpy.types.Operator):
    bl_idname = "filters.volume_update_material"
    bl_label = "Update Material"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene.filters_volume_settings
        if not s.volume_object or s.volume_object.type != 'VOLUME':
            self.report({'ERROR'}, "Select a Volume object")
            return {'CANCELLED'}
        try:
            if getattr(s, 'auto_range', False) and getattr(s, 'grid_name', ''):
                fp = _resolve_vdb_filepath_for_frame(context, s)
                rng = _compute_vdb_grid_min_max(fp, s.grid_name)
                if rng:
                    s.from_min, s.from_max = rng
        except Exception:
            pass
        mat = ensure_volume_material_for_object(context, s.volume_object, s)
        nt = mat.node_tree
        attr = next((n for n in nt.nodes if n.type == 'ATTRIBUTE'), None)
        if attr:
            attr.attribute_name = s.grid_name or "density"
        mapr = next((n for n in nt.nodes if n.type == 'MAP_RANGE'), None)
        if mapr:
            mapr.inputs[1].default_value = s.from_min
            mapr.inputs[2].default_value = s.from_max
        math_mul = next((n for n in nt.nodes if getattr(n, 'operation', '') == 'MULTIPLY'), None)
        if math_mul:
            math_mul.inputs[1].default_value = s.density_scale
        pv = next((n for n in nt.nodes if n.type == 'VOLUME_PRINCIPLED'), None)
        if pv:
            pv.inputs[4].default_value = s.anisotropy
            pv.inputs[6].default_value = s.emission_strength
        cr = next((n for n in nt.nodes if n.type == 'VALTORGB'), None)
        if cr:
            try:
                from ..utils.colormaps import apply_colormap_to_ramp
                apply_colormap_to_ramp(s.colormap, cr)
            except Exception:
                pass
        cube = _ensure_slice_cube_object(s.volume_object)
        tex = next((n for n in nt.nodes if n.type == 'TEX_COORD'), None)
        if tex:
            try:
                tex.object = cube
            except Exception:
                pass
        try:
            s.slice_object = cube
        except Exception:
            pass
        slice_group = next((n for n in nt.nodes if n.type == 'GROUP' and n.node_tree and n.node_tree.name == 'Slice Cube'), None)
        if slice_group:
            try:
                idx = 2
                slice_group.inputs[idx].default_value = bool(s.slice_invert)
            except Exception:
                pass
        return {'FINISHED'}


class FILTERS_OT_volume_compute_range(bpy.types.Operator):
    bl_idname = "filters.volume_compute_range"
    bl_label = "Compute Range"
    bl_options = {'REGISTER'}

    def execute(self, context):
        s = context.scene.filters_volume_settings
        if not s.volume_object or s.volume_object.type != 'VOLUME' or not s.grid_name:
            self.report({'ERROR'}, "Select volume and grid")
            return {'CANCELLED'}
        rng = None
        try:
            fp = _resolve_vdb_filepath_for_frame(context, s)
            rng = _compute_vdb_grid_min_max(fp, s.grid_name)
        except Exception:
            rng = None
        if not rng:
            from_filepath = _resolve_vdb_filepath_for_frame(context, s)
            reason = _LAST_RANGE_ERROR or "Unknown reason"
            self.report({'WARNING'}, f"Could not compute range: {reason} | file: {from_filepath}")
            return {'CANCELLED'}
        s.from_min, s.from_max = rng
        if s.auto_range:
            bpy.ops.filters.volume_update_material('INVOKE_DEFAULT')
        return {'FINISHED'}


def register():
    bpy.utils.register_class(FILTERS_OT_volume_update_material)
    bpy.utils.register_class(FILTERS_OT_volume_compute_range)


def unregister():
    bpy.utils.unregister_class(FILTERS_OT_volume_compute_range)
    bpy.utils.unregister_class(FILTERS_OT_volume_update_material) 