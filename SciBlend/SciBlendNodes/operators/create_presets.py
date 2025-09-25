import bpy
from bpy.types import Operator
from bpy.props import EnumProperty, StringProperty


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
    group_in.location = (-600, 0)
    group_out.location = (600, 0)
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


class SCIBLENDNODES_OT_create_preset(Operator):
    """Create the 'Points + Shader' Geometry Nodes preset and select it in SciBlend Nodes."""
    bl_idname = "sciblend_nodes.create_preset"
    bl_label = "Create Preset Node Group"
    bl_options = {'REGISTER', 'UNDO'}

    preset: EnumProperty(
        name="Preset",
        items=[('POINTS_SHADER', "Points + Shader", "Convert mesh to points and set material")],
        default='POINTS_SHADER',
    )

    attribute_name: StringProperty(name="Attribute", default="Col")
    material_name: StringProperty(name="Material", default="")

    def execute(self, context):
        settings = getattr(context.scene, 'sciblend_nodes_settings', None)
        if not settings:
            self.report({'ERROR'}, "SciBlend Nodes settings not available")
            return {'CANCELLED'}

        name = f"SciBlend_{self.preset}"
        try:
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