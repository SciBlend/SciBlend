import bpy
from bpy.types import Operator
from bpy.props import EnumProperty, StringProperty, FloatProperty


def _ensure_interface_socket(nodegroup: bpy.types.NodeTree, name: str, in_out: str, socket_type: str) -> bpy.types.NodeTreeInterfaceSocket:
    """Return an interface socket with given name; create it if missing."""
    for s in nodegroup.interface.items_tree:
        if getattr(s, 'name', '') == name and getattr(s, 'in_out', '') == in_out:
            return s
    return nodegroup.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)


def _link(sockets_out, sockets_in):
    """Helper to link two sockets if both exist."""
    try:
        sockets_out.node.id_data.links.new(sockets_out, sockets_in)
    except Exception:
        pass


def _create_group_base(name: str) -> tuple[bpy.types.NodeTree, bpy.types.Node, bpy.types.Node]:
    """Create an empty Geometry Nodes group with standard Geometry input/output and return (group, in, out) nodes."""
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    nodes = ng.nodes
    links = ng.links
    nodes.clear()
    group_in = nodes.new('NodeGroupInput')
    group_out = nodes.new('NodeGroupOutput')
    group_in.location = (-800, 0)
    group_out.location = (900, 0)
    _ensure_interface_socket(ng, 'Geometry', 'INPUT', 'NodeSocketGeometry')
    _ensure_interface_socket(ng, 'Geometry', 'OUTPUT', 'NodeSocketGeometry')
    return ng, group_in, group_out


def _find_shader_material_for_collection(coll_name: str) -> bpy.types.Material | None:
    try:
        for obj in bpy.data.collections[coll_name].objects:
            if getattr(obj, 'type', None) != 'MESH':
                continue
            mat = obj.active_material or (obj.data.materials[0] if obj.data.materials else None)
            if mat and mat.get('sciblend_colormap') is not None:
                return mat
    except Exception:
        pass
    return None


def _preset_points_shader(group_name: str, attribute_name: str, material_name: str | None) -> bpy.types.NodeTree:
    """Create a preset: Mesh to Points + Set Material for shader application.

    The node group exposes a Material input on the interface but it is not linked to the Set Material node.
    If a material name is provided, it is assigned as the default on the Set Material node.
    """
    ng, gi, go = _create_group_base(group_name)
    nodes = ng.nodes
    links = ng.links

    mesh_to_points = nodes.new('GeometryNodeMeshToPoints')
    mesh_to_points.name = "Mesh to Points"
    mesh_to_points.mode = 'VERTICES'
    try:
        mesh_to_points.inputs[1].default_value = True
        mesh_to_points.inputs[2].default_value = (0.0, 0.0, 0.0)
    except Exception:
        pass

    set_material = nodes.new('GeometryNodeSetMaterial')
    set_material.name = "Set Material"
    try:
        set_material.inputs[1].default_value = True
    except Exception:
        pass

    _ensure_interface_socket(ng, 'Material', 'INPUT', 'NodeSocketMaterial')

    gi.width = 140.0
    go.width = 140.0
    mesh_to_points.location = (-200.0, 0.0)
    set_material.location = (200.0, 0.0)

    try:
        _link(gi.outputs['Geometry'], mesh_to_points.inputs['Mesh'])
    except Exception:
        _link(gi.outputs[0], mesh_to_points.inputs[0])
    try:
        _link(mesh_to_points.outputs['Points'], set_material.inputs['Geometry'])
    except Exception:
        _link(mesh_to_points.outputs[0], set_material.inputs[0])
    try:
        _link(set_material.outputs['Geometry'], go.inputs['Geometry'])
    except Exception:
        _link(set_material.outputs[0], go.inputs[0])

    try:
        if material_name and material_name in bpy.data.materials:
            set_material.inputs[2].default_value = bpy.data.materials[material_name]
    except Exception:
        pass

    return ng


def _preset_displace_normal(group_name: str, attribute_name: str, scale: float) -> bpy.types.NodeTree:
    """Create a preset: Displace vertices along their normal using a FLOAT attribute and a scale factor."""
    ng, gi, go = _create_group_base(group_name)

    nodes = ng.nodes
    links = ng.links

    named_attr = nodes.new('GeometryNodeInputNamedAttribute')
    try:
        named_attr.data_type = 'FLOAT'
    except Exception:
        pass

    math_mult = nodes.new('ShaderNodeMath')
    math_mult.operation = 'MULTIPLY'
    try:
        math_mult.inputs[1].default_value = float(scale)
    except Exception:
        pass

    normal = nodes.new('GeometryNodeInputNormal')

    vec_scale = nodes.new('ShaderNodeVectorMath')
    try:
        vec_scale.operation = 'SCALE'
    except Exception:
        vec_scale.operation = 'MULTIPLY'

    set_pos = nodes.new('GeometryNodeSetPosition')

    named_attr.location = (-400.0, 200.0)
    math_mult.location = (-200.0, 200.0)
    normal.location = (-200.0, 0.0)
    vec_scale.location = (0.0, 100.0)
    set_pos.location = (200.0, 0.0)

    try:
        _link(gi.outputs['Geometry'], set_pos.inputs['Geometry'])
    except Exception:
        _link(gi.outputs[0], set_pos.inputs[0])

    try:
        _link(named_attr.outputs['Attribute'], math_mult.inputs[0])
    except Exception:
        _link(named_attr.outputs[0], math_mult.inputs[0])

    try:
        _link(normal.outputs['Normal'], vec_scale.inputs[0])
    except Exception:
        _link(normal.outputs[0], vec_scale.inputs[0])

    try:
        _link(math_mult.outputs['Value'], vec_scale.inputs[3])
    except Exception:
        try:
            _link(math_mult.outputs[0], vec_scale.inputs[1])
        except Exception:
            pass

    try:
        _link(vec_scale.outputs['Vector'], set_pos.inputs['Offset'])
    except Exception:
        _link(vec_scale.outputs[0], set_pos.inputs[3])

    try:
        _link(set_pos.outputs['Geometry'], go.inputs['Geometry'])
    except Exception:
        _link(set_pos.outputs[0], go.inputs[0])

    try:
        named_attr.inputs['Name'].default_value = attribute_name
    except Exception:
        try:
            named_attr.inputs[0].default_value = attribute_name
        except Exception:
            pass

    return ng


def _preset_vector_glyphs(
    group_name: str,
    vector_attribute_name: str,
    scale: float,
    scale_attribute_name: str | None = None,
    material_name: str | None = None,
    glyph_density: float = 1.0,
    glyph_max_count: int = 10000,
    glyph_primitive: str = 'CONE',
    cone_vertices: int = 16,
    cone_radius_top: float = 0.0,
    cone_radius_bottom: float = 0.02,
    cone_depth: float = 0.1,
    cyl_vertices: int = 16,
    cyl_radius: float = 0.02,
    cyl_depth: float = 0.1,
    sphere_segments: int = 16,
    sphere_rings: int = 8,
    sphere_radius: float = 0.05,
) -> bpy.types.NodeTree:
    """Create Vector Glyphs node group exactly matching the provided reference tree."""
    def _find_input(node, name: str, fallback_index: int = 0):
        for s in node.inputs:
            if getattr(s, 'name', '') == name:
                return s
        return node.inputs[fallback_index] if len(node.inputs) > fallback_index else None

    def _find_output(node, name: str, fallback_index: int = 0):
        for s in node.outputs:
            if getattr(s, 'name', '') == name:
                return s
        return node.outputs[fallback_index] if len(node.outputs) > fallback_index else None

    def _link(nodes_links, out_node, out_name: str, in_node, in_name: str, out_idx: int = 0, in_idx: int = 0):
        out_socket = _find_output(out_node, out_name, out_idx)
        in_socket = _find_input(in_node, in_name, in_idx)
        if out_socket is not None and in_socket is not None:
            nodes_links.new(out_socket, in_socket)

    ng, gi, go = _create_group_base(group_name)
    nodes = ng.nodes
    links = ng.links

    _ensure_interface_socket(ng, 'Material', 'INPUT', 'NodeSocketMaterial')

    mesh_to_points = nodes.new('GeometryNodeMeshToPoints')
    mesh_to_points.name = 'Mesh to Points'
    mesh_to_points.mode = 'VERTICES'
    if len(mesh_to_points.inputs) > 3:
        mesh_to_points.inputs[1].default_value = True
        mesh_to_points.inputs[3].default_value = 0.05

    cone = nodes.new('GeometryNodeMeshCone')
    if len(cone.inputs) >= 6:
        cone.inputs[0].default_value = int(cone_vertices)
        cone.inputs[3].default_value = float(cone_radius_top)
        cone.inputs[4].default_value = float(cone_radius_bottom)
        cone.inputs[5].default_value = float(cone_depth)

    cylinder = nodes.new('GeometryNodeMeshCylinder')
    if len(cylinder.inputs) >= 5:
        cylinder.inputs[0].default_value = int(cyl_vertices)
        cylinder.inputs[3].default_value = float(cyl_radius)
        cylinder.inputs[4].default_value = float(cyl_depth)

    sphere = nodes.new('GeometryNodeMeshUVSphere')
    if len(sphere.inputs) >= 3:
        sphere.inputs[0].default_value = int(sphere_segments)
        sphere.inputs[1].default_value = int(sphere_rings)
        sphere.inputs[2].default_value = float(sphere_radius)

    named_x = nodes.new('GeometryNodeInputNamedAttribute')
    named_y = nodes.new('GeometryNodeInputNamedAttribute')
    named_z = nodes.new('GeometryNodeInputNamedAttribute')
    named_x.data_type = 'FLOAT'
    named_y.data_type = 'FLOAT'
    named_z.data_type = 'FLOAT'

    ax, ay, az = 'Vel_X', 'Vel_Y', 'Vel_Z'
    if isinstance(vector_attribute_name, str) and vector_attribute_name.startswith('COMPOSITE|'):
        parts = vector_attribute_name.split('|')
        if len(parts) >= 4:
            ax, ay, az = parts[1], parts[2], parts[3]
    _find_input(named_x, 'Name', 0).default_value = ax
    _find_input(named_y, 'Name', 0).default_value = ay
    _find_input(named_z, 'Name', 0).default_value = az

    combine_xyz = nodes.new('ShaderNodeCombineXYZ')
    _link(links, named_x, 'Attribute', combine_xyz, 'X', 0, 0)
    _link(links, named_y, 'Attribute', combine_xyz, 'Y', 0, 1)
    _link(links, named_z, 'Attribute', combine_xyz, 'Z', 0, 2)

    align = nodes.new('FunctionNodeAlignRotationToVector')
    align.axis = 'Z'
    align.pivot_axis = 'AUTO'
    _link(links, combine_xyz, 'Vector', align, 'Vector')

    named_mag = nodes.new('GeometryNodeInputNamedAttribute')
    named_mag.data_type = 'FLOAT'
    _find_input(named_mag, 'Name', 0).default_value = scale_attribute_name or 'Vel_Magnitude'

    mult = nodes.new('ShaderNodeMath')
    mult.name = 'Math.001'
    mult.operation = 'MULTIPLY'
    _find_input(mult, 'Value_001', 1).default_value = float(scale)
    _link(links, named_mag, 'Attribute', mult, 'Value')

    combine_xyz_scale = nodes.new('ShaderNodeCombineXYZ')
    _link(links, mult, 'Value', combine_xyz_scale, 'X')
    _link(links, mult, 'Value', combine_xyz_scale, 'Y')
    _link(links, mult, 'Value', combine_xyz_scale, 'Z')

    inst = nodes.new('GeometryNodeInstanceOnPoints')
    _find_input(inst, 'Pick Instance', 3).default_value = False

    realize = nodes.new('GeometryNodeRealizeInstances')
    set_mat = nodes.new('GeometryNodeSetMaterial')
    _find_input(set_mat, 'Selection', 1).default_value = True
    if material_name and material_name in bpy.data.materials:
        _find_input(set_mat, 'Material', 2).default_value = bpy.data.materials[material_name]

    ads = nodes.new('GeometryNodeAttributeDomainSize')
    ads.component = 'POINTCLOUD'

    math_div = nodes.new('ShaderNodeMath')
    math_div.name = 'Math.002'
    math_div.operation = 'DIVIDE'
    _find_input(math_div, 'Value', 0).default_value = float(glyph_max_count) if glyph_max_count > 0 else 0.0

    math_min = nodes.new('ShaderNodeMath')
    math_min.name = 'Math.004'
    math_min.operation = 'MINIMUM'
    _find_input(math_min, 'Value_001', 1).default_value = float(glyph_density)

    rv_bool = nodes.new('FunctionNodeRandomValue')
    rv_bool.data_type = 'BOOLEAN'

    index_node = nodes.new('GeometryNodeInputIndex')

    reroute_pts = nodes.new('NodeReroute')

    _link(links, gi, 'Geometry', mesh_to_points, 'Mesh')
    _link(links, mesh_to_points, 'Points', ads, 'Geometry')

    _link(links, ads, 'Point Count', math_div, 'Value_001', 0, 1)
    _link(links, math_div, 'Value', math_min, 'Value')

    _link(links, math_min, 'Value', rv_bool, 'Probability')
    _link(links, index_node, 'Index', rv_bool, 'ID')

    _link(links, mesh_to_points, 'Points', reroute_pts, 'Input')
    _link(links, reroute_pts, 'Output', inst, 'Points')

    _link(links, cone, 'Mesh', inst, 'Instance')
    _link(links, align, 'Rotation', inst, 'Rotation')
    _link(links, combine_xyz_scale, 'Vector', inst, 'Scale')

    _link(links, inst, 'Instances', realize, 'Geometry')
    _link(links, realize, 'Geometry', set_mat, 'Geometry')
    _link(links, set_mat, 'Geometry', go, 'Geometry')

    _link(links, rv_bool, 'Value', inst, 'Selection', 3, 1)

    return ng


class SCIBLENDNODES_OT_create_preset(Operator):
    """Create a SciBlend Nodes Geometry Nodes preset and select it in SciBlend Nodes."""
    bl_idname = "sciblend_nodes.create_preset"
    bl_label = "Create Preset Node Group"
    bl_options = {'REGISTER', 'UNDO'}

    preset: EnumProperty(
        name="Preset",
        items=[
            ('POINTS_SHADER', "Points + Shader", "Convert mesh to points and set material"),
            ('DISPLACE_NORMAL', "Displace by Attribute", "Displace vertices along normal scaled by a mesh attribute"),
            ('VECTOR_GLYPHS', "Vector Glyphs", "Instance oriented cones from a vector attribute"),
        ],
        default='POINTS_SHADER',
    )

    attribute_name: StringProperty(name="Attribute", default="Col")
    vector_attribute_name: StringProperty(name="Vector Attribute", default="velocity")
    material_name: StringProperty(name="Material", default="")
    scale: FloatProperty(name="Scale", default=1.0, min=0.0)
    scale_attribute_name: StringProperty(name="Scale Attribute", default="")

    def execute(self, context):
        settings = getattr(context.scene, 'sciblend_nodes_settings', None)
        if not settings:
            self.report({'ERROR'}, "SciBlend Nodes settings not available")
            return {'CANCELLED'}

        name = f"SciBlend_{self.preset}"
        try:
            if self.preset == 'DISPLACE_NORMAL':
                ng = _preset_displace_normal(name, self.attribute_name, self.scale)
            elif self.preset == 'VECTOR_GLYPHS':
                ng = _preset_vector_glyphs(name, self.vector_attribute_name, self.scale, (self.scale_attribute_name if self.scale_attribute_name not in {'', 'NONE'} else None), self.material_name or None)
            else:
                ng = _preset_points_shader(name, self.attribute_name, self.material_name or None)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create preset: {e}")
            return {'CANCELLED'}

        try:
            settings.node_group_name = ng.name
        except Exception:
            pass
        self.report({'INFO'}, f"Created node group '{ng.name}'")
        return {'FINISHED'} 