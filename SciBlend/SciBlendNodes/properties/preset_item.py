import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, EnumProperty, FloatProperty, FloatVectorProperty


def _update_preset_item(self, context):
    try:
        print("[SciBlend Nodes][Preset Update] Start")
        print(f"[SciBlend Nodes][Preset Update] Preset: {getattr(self, 'preset', '')}")
        print(f"[SciBlend Nodes][Preset Update] Current NG: {getattr(self, 'node_group_name', '')}")
        print(f"[SciBlend Nodes][Preset Update] Values: points_radius={getattr(self, 'points_radius', None)}, material_override='{getattr(self, 'material_override', '')}', attribute='{getattr(self, 'attribute_name', '')}', vector_attribute='{getattr(self, 'vector_attribute_name', '')}', scale={getattr(self, 'scale', None)}, radius={getattr(self, 'radius', None)}, voxel_size={getattr(self, 'voxel_size', None)}, threshold={getattr(self, 'threshold', None)}, plane_point={tuple(getattr(self, 'plane_point', ()))}, plane_normal={tuple(getattr(self, 'plane_normal', ()))}")
        scene = getattr(bpy.context, 'scene', None)
        settings = getattr(scene, 'sciblend_nodes_settings', None) if scene else None
        target_coll = getattr(settings, 'target_collection', '') if settings else ''
        print(f"[SciBlend Nodes][Preset Update] Context target_collection: '{target_coll}', row collection_name: '{getattr(self, 'collection_name', '')}'")
        if target_coll and getattr(self, 'collection_name', '') and self.collection_name != target_coll:
            print("[SciBlend Nodes][Preset Update] Skip: row belongs to different collection than current selection")
            return
        ng_name = getattr(self, 'node_group_name', '')
        if not ng_name:
            print(f"[SciBlend Nodes][Preset Update] Resolving NG from collection: '{target_coll}'")
            coll = bpy.data.collections.get(target_coll) if target_coll else None
            def _iter_objs(c):
                if not c:
                    return []
                try:
                    return list(getattr(c, 'all_objects', [])) or list(getattr(c, 'objects', []))
                except Exception:
                    return list(getattr(c, 'objects', []))
            for obj in _iter_objs(coll):
                if getattr(obj, 'type', None) != 'MESH':
                    continue
                for m in obj.modifiers:
                    if m.type == 'NODES' and bool(m.get('sciblend_nodes', False)):
                        grp = m.get('sciblend_group', '')
                        print(f"[SciBlend Nodes][Preset Update] Found owned modifier on '{obj.name}': {m.name}, group='{grp}'")
                        if grp:
                            self.node_group_name = grp
                            ng_name = grp
                            break
                if ng_name:
                    break
        if not ng_name or ng_name not in bpy.data.node_groups:
            print(f"[SciBlend Nodes][Preset Update] Abort: node group not resolved or missing: '{ng_name}'")
            return
        ng = bpy.data.node_groups[ng_name]
        print(f"[SciBlend Nodes][Preset Update] Updating node group: '{ng.name}' with 4 nodes")
        if getattr(self, 'preset', '') == 'POINTS_SHADER':
            for n in ng.nodes:
                if n.bl_idname == 'GeometryNodeMeshToPoints':
                    try:
                        n.inputs['Radius'].default_value = float(getattr(self, 'points_radius', 0.05))
                        print(f"[SciBlend Nodes][Preset Update] MeshToPoints.radius -> {float(getattr(self, 'points_radius', 0.05))}")
                    except Exception:
                        if len(n.inputs) > 3:
                            n.inputs[3].default_value = float(getattr(self, 'points_radius', 0.05))
                            print(f"[SciBlend Nodes][Preset Update] MeshToPoints.inputs[3] -> {float(getattr(self, 'points_radius', 0.05))}")
                if n.bl_idname == 'GeometryNodeSetMaterial':
                    mat_name = getattr(self, 'material_override', '')
                    if mat_name and mat_name in bpy.data.materials:
                        try:
                            n.inputs['Material'].default_value = bpy.data.materials[mat_name]
                        except Exception:
                            if len(n.inputs) > 2:
                                n.inputs[2].default_value = bpy.data.materials[mat_name]
                        print(f"[SciBlend Nodes][Preset Update] SetMaterial.material -> '{mat_name}'")
        elif self.preset == 'DISPLACE_NORMAL':
            named_attr = None
            scalar_mult = None
            for n in ng.nodes:
                if n.bl_idname == 'GeometryNodeInputNamedAttribute':
                    named_attr = n
                if n.bl_idname == 'ShaderNodeMath' and getattr(n, 'operation', '') == 'MULTIPLY':
                    scalar_mult = n
            if named_attr is not None:
                try:
                    named_attr.inputs['Name'].default_value = getattr(self, 'attribute_name', 'Col')
                except Exception:
                    named_attr.inputs[0].default_value = getattr(self, 'attribute_name', 'Col')
                print(f"[SciBlend Nodes][Preset Update] NamedAttribute.name -> '{getattr(self, 'attribute_name', 'Col')}'")
            if scalar_mult is not None:
                try:
                    scalar_mult.inputs[1].default_value = float(getattr(self, 'scale', 1.0))
                except Exception:
                    pass
                print(f"[SciBlend Nodes][Preset Update] Scale -> {float(getattr(self, 'scale', 1.0))}")
        elif self.preset == 'VECTOR_GLYPHS':
            vec_attr = None
            vec_scale = None
            for n in ng.nodes:
                if n.bl_idname == 'GeometryNodeInputNamedAttribute':
                    vec_attr = n
                if n.bl_idname == 'ShaderNodeMath' and getattr(n, 'operation', '') == 'MULTIPLY':
                    vec_scale = n
            if vec_attr is not None:
                try:
                    vec_attr.inputs['Name'].default_value = getattr(self, 'vector_attribute_name', 'velocity')
                except Exception:
                    vec_attr.inputs[0].default_value = getattr(self, 'vector_attribute_name', 'velocity')
                print(f"[SciBlend Nodes][Preset Update] VectorAttribute.name -> '{getattr(self, 'vector_attribute_name', 'velocity')}'")
            if vec_scale is not None:
                try:
                    vec_scale.inputs[1].default_value = float(getattr(self, 'scale', 1.0))
                except Exception:
                    pass
                print(f"[SciBlend Nodes][Preset Update] Vector scale -> {float(getattr(self, 'scale', 1.0))}")
        elif self.preset == 'POINTS_TO_VOLUME':
            for n in ng.nodes:
                if n.bl_idname == 'GeometryNodePointsToVolume':
                    try:
                        n.inputs['Radius'].default_value = float(getattr(self, 'radius', 0.05))
                    except Exception:
                        if len(n.inputs) > 1:
                            n.inputs[1].default_value = float(getattr(self, 'radius', 0.05))
                    print(f"[SciBlend Nodes][Preset Update] PointsToVolume.radius -> {float(getattr(self, 'radius', 0.05))}")
                if n.bl_idname == 'GeometryNodeVolumeToMesh':
                    try:
                        n.inputs['Voxel Size'].default_value = float(getattr(self, 'voxel_size', 0.1))
                        n.inputs['Threshold'].default_value = float(getattr(self, 'threshold', 0.1))
                    except Exception:
                        if len(n.inputs) > 2:
                            n.inputs[1].default_value = float(getattr(self, 'voxel_size', 0.1))
                            n.inputs[2].default_value = float(getattr(self, 'threshold', 0.1))
                    print(f"[SciBlend Nodes][Preset Update] VolumeToMesh.voxel={float(getattr(self, 'voxel_size', 0.1))}, thr={float(getattr(self, 'threshold', 0.1))}")
        elif self.preset == 'SLICE_PLANE':
            for n in ng.nodes:
                if n.bl_idname == 'GeometryNodeInputVector':
                    label = (getattr(n, 'name', '') or '').lower()
                    try:
                        if 'normal' in label:
                            n.vector = tuple(getattr(self, 'plane_normal', (0.0, 0.0, 1.0)))
                            print(f"[SciBlend Nodes][Preset Update] Plane.normal -> {tuple(getattr(self, 'plane_normal', (0.0, 0.0, 1.0)))}")
                        else:
                            n.vector = tuple(getattr(self, 'plane_point', (0.0, 0.0, 0.0)))
                            print(f"[SciBlend Nodes][Preset Update] Plane.point -> {tuple(getattr(self, 'plane_point', (0.0, 0.0, 0.0)))}")
                    except Exception:
                        pass
        print("[SciBlend Nodes][Preset Update] Done")
    except Exception as e:
        print(f"[SciBlend Nodes][Preset Update] Exception: {e}")


class PresetListItem(PropertyGroup):
    collection_name: StringProperty(name="Collection", default="")
    preset: EnumProperty(
        name="Preset",
        items=[
            ('POINTS_SHADER', "Points + Shader", "Convert mesh to points and set material"),
        ],
        default='POINTS_SHADER',
        update=_update_preset_item,
    )
    attribute_name: StringProperty(name="Attribute", default="Col", update=_update_preset_item)
    vector_attribute_name: StringProperty(name="Vector Attribute", default="velocity", update=_update_preset_item)
    material_override: StringProperty(name="Material", default="", update=_update_preset_item)
    points_radius: FloatProperty(name="Point Size", default=0.05, min=0.0, update=_update_preset_item)
    scale: FloatProperty(name="Scale", default=1.0, min=0.0, update=_update_preset_item)
    radius: FloatProperty(name="Radius", default=0.05, min=0.0, update=_update_preset_item)
    voxel_size: FloatProperty(name="Voxel Size", default=0.1, min=0.0, update=_update_preset_item)
    threshold: FloatProperty(name="Threshold", default=0.1, min=0.0, update=_update_preset_item)
    plane_point: FloatVectorProperty(name="Plane Point", default=(0.0, 0.0, 0.0), update=_update_preset_item)
    plane_normal: FloatVectorProperty(name="Plane Normal", default=(0.0, 0.0, 1.0), update=_update_preset_item)
    node_group_name: StringProperty(name="Node Group", default="") 