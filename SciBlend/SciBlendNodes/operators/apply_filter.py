import bpy
from bpy.types import Operator


class SCIBLENDNODES_OT_apply_filter_to_collection(Operator):
    bl_idname = "sciblend_nodes.apply_filter"
    bl_label = "Apply Filter to Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = getattr(context.scene, 'sciblend_nodes_settings', None)
        if not settings:
            self.report({'ERROR'}, "SciBlend Nodes settings not available")
            return {'CANCELLED'}

        coll_name = None
        try:
            if getattr(settings, 'collections_list', None) and 0 <= int(getattr(settings, 'collections_list_index', -1)) < len(settings.collections_list):
                coll_name = settings.collections_list[settings.collections_list_index].name
        except Exception:
            coll_name = None
        if not coll_name:
            coll_name = settings.target_collection

        node_group_name = settings.node_group_name
        if not coll_name:
            self.report({'ERROR'}, "Select a collection")
            return {'CANCELLED'}
        if not node_group_name:
            self.report({'ERROR'}, "Select a Geometry Nodes group")
            return {'CANCELLED'}

        coll = bpy.data.collections.get(coll_name)
        if not coll:
            self.report({'ERROR'}, f"Collection not found: {coll_name}")
            return {'CANCELLED'}
        ng = bpy.data.node_groups.get(node_group_name)
        if not ng or getattr(ng, 'bl_idname', '') != 'GeometryNodeTree':
            self.report({'ERROR'}, f"Invalid Geometry Nodes group: {node_group_name}")
            return {'CANCELLED'}

        try:
            settings.target_collection = coll_name
        except Exception:
            pass

        print(f"[SciBlend Nodes] Applying '{node_group_name}' to collection '{coll_name}'")

        def _iter_objects_in_collection(c):
            try:
                all_objs = list(getattr(c, 'all_objects', []))
                if all_objs:
                    return [o for o in all_objs]
            except Exception:
                pass
            objs = list(getattr(c, 'objects', []))
            try:
                for ch in getattr(c, 'children', []):
                    objs.extend(_iter_objects_in_collection(ch))
            except Exception:
                pass
            return objs

        all_objs = _iter_objects_in_collection(coll)
        print(f"[SciBlend Nodes] Found {len(all_objs)} objects (including children) in collection '{coll_name}'")

        default_mat = None
        try:
            for obj in all_objs:
                if getattr(obj, 'type', None) == 'MESH' and obj.active_material and obj.active_material.get('sciblend_colormap') is not None:
                    default_mat = obj.active_material
                    print(f"[SciBlend Nodes] Default shader material detected: '{default_mat.name}'")
                    break
        except Exception as e:
            print(f"[SciBlend Nodes] Material detection error: {e}")
            default_mat = None

        def _apply_to_objects(objs):
            count = 0
            for obj in objs:
                if getattr(obj, 'type', None) != 'MESH':
                    continue
                try:
                    print(f"[SciBlend Nodes] Processing object '{obj.name}'")
                    ours = [m for m in obj.modifiers if m.type == 'NODES' and bool(m.get('sciblend_nodes', False))]
                    print(f"[SciBlend Nodes] Existing ours: {[m.name for m in ours]}")
                    target_mod = None
                    for m in ours:
                        if m.get('sciblend_group', '') == ng.name:
                            target_mod = m
                            break
                    if target_mod is None:
                        target_mod = ours[0] if ours else None
                    created = False
                    if target_mod is None:
                        target_mod = obj.modifiers.new(name=ng.name, type='NODES')
                        created = True
                    target_mod.node_group = ng
                    try:
                        target_mod.name = ng.name
                    except Exception:
                        pass
                    try:
                        import uuid as _uuid
                        if not target_mod.get("sciblend_uid"):
                            target_mod["sciblend_uid"] = _uuid.uuid4().hex
                        current_uid = target_mod.get("sciblend_uid")
                        target_mod["sciblend_nodes"] = True
                        target_mod["sciblend_group"] = ng.name
                        target_mod["sciblend_collection"] = coll_name
                    except Exception:
                        current_uid = None
                        pass
                    if created:
                        print(f"[SciBlend Nodes] Created modifier '{target_mod.name}' on '{obj.name}'")
                    for m in list(obj.modifiers):
                        if m is target_mod:
                            continue
                        if m.type == 'NODES' and bool(m.get('sciblend_nodes', False)) and m.get('sciblend_group', '') == ng.name:
                            if current_uid and m.get('sciblend_uid', '') == current_uid:
                                continue
                            try:
                                print(f"[SciBlend Nodes] Removing duplicate owned modifier for group '{ng.name}' -> '{m.name}' on '{obj.name}'")
                                obj.modifiers.remove(m)
                            except Exception as e:
                                print(f"[SciBlend Nodes] Error removing modifier '{m.name}': {e}")
                    try:
                        for node in target_mod.node_group.nodes:
                            if node.bl_idname == 'GeometryNodeMeshToPoints':
                                try:
                                    node.inputs['Radius'].default_value = float(getattr(settings, 'points_radius', 0.05))
                                    print(f"[SciBlend Nodes] Set points radius to {float(getattr(settings, 'points_radius', 0.05))} on '{obj.name}'")
                                except Exception:
                                    if len(node.inputs) > 3:
                                        node.inputs[3].default_value = float(getattr(settings, 'points_radius', 0.05))
                                        print(f"[SciBlend Nodes] Set points radius via index 3 on '{obj.name}'")
                            if node.bl_idname == 'GeometryNodeSetMaterial' and default_mat is not None:
                                try:
                                    node.inputs['Material'].default_value = default_mat
                                except Exception:
                                    if len(node.inputs) > 2:
                                        node.inputs[2].default_value = default_mat
                                print(f"[SciBlend Nodes] Set material '{default_mat.name}' on '{obj.name}'")
                            if node.bl_idname == 'ShaderNodeMath' and getattr(node, 'operation', '') == 'MULTIPLY':
                                try:
                                    node.inputs[1].default_value = float(getattr(settings, 'scale', 1.0))
                                except Exception:
                                    pass
                    except Exception as e:
                        print(f"[SciBlend Nodes] Error tuning nodes on '{obj.name}': {e}")
                    try:
                        mods_info = [(m.name, bool(m.get('sciblend_nodes', False)), m.get('sciblend_group', ''), m.get('sciblend_uid','')) for m in obj.modifiers if m.type == 'NODES']
                        print(f"[SciBlend Nodes] Final GN modifiers on '{obj.name}': {mods_info}")
                    except Exception:
                        pass
                    count += 1
                except Exception as e:
                    print(f"[SciBlend Nodes] Error on object '{obj.name}': {e}")
                    continue
            return count

        applied = _apply_to_objects(all_objs)

        if applied == 0:
            nested = set()
            def _collect_nested(c):
                nested.add(c)
                for ch in getattr(c, 'children', []):
                    _collect_nested(ch)
            _collect_nested(coll)
            names = {c.name for c in nested}
            objs2 = [o for o in bpy.data.objects if any(c.name in names for c in getattr(o, 'users_collection', []))]
            print(f"[SciBlend Nodes] Fallback path: found {len(objs2)} candidate objects via users_collection")
            applied = _apply_to_objects(objs2)
            if applied == 0:
                self.report({'WARNING'}, f"No mesh objects found in collection '{coll_name}'")
                print(f"[SciBlend Nodes] No applicable mesh objects in '{coll_name}'")
                return {'CANCELLED'}

        self.report({'INFO'}, f"Applied '{node_group_name}' to {applied} mesh(es) in collection '{coll_name}'")
        print(f"[SciBlend Nodes] Finished applying '{node_group_name}' to {applied} mesh(es) in '{coll_name}'")
        return {'FINISHED'}


class SCIBLENDNODES_OT_apply_preset(Operator):
    bl_idname = "sciblend_nodes.apply_preset"
    bl_label = "Apply Preset to Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = getattr(context.scene, 'sciblend_nodes_settings', None)
        if not settings:
            self.report({'ERROR'}, "SciBlend Nodes settings not available")
            return {'CANCELLED'}

        coll_name = None
        try:
            if getattr(settings, 'collections_list', None) and 0 <= int(getattr(settings, 'collections_list_index', -1)) < len(settings.collections_list):
                coll_name = settings.collections_list[settings.collections_list_index].name
        except Exception:
            coll_name = None
        if not coll_name:
            coll_name = settings.target_collection
        if not coll_name:
            self.report({'ERROR'}, "Select a collection")
            return {'CANCELLED'}

        try:
            settings.target_collection = coll_name
        except Exception:
            pass

        print(f"[SciBlend Nodes] Creating preset '{settings.preset}' for collection '{coll_name}'")

        sig = f"{settings.preset}|{coll_name}|{settings.attribute_name}|{settings.vector_attribute_name}|{settings.material_name}|{settings.scale}|{settings.radius}|{settings.voxel_size}|{settings.threshold}|{tuple(settings.plane_point)}|{tuple(settings.plane_normal)}"
        if getattr(settings, 'last_applied_signature', '') == sig:
            print("[SciBlend Nodes] Skipping preset creation (signature unchanged)")
            return {'CANCELLED'}

        try:
            from .create_presets import _preset_points_shader, _preset_displace_normal, _preset_vector_glyphs
            base_name = f"SciBlend_{settings.preset}"
            name = base_name
            i = 1
            while name in bpy.data.node_groups:
                i += 1
                name = f"{base_name}.{i:03d}"
            if settings.preset == 'DISPLACE_NORMAL':
                ng = _preset_displace_normal(name, settings.attribute_name, float(getattr(settings, 'scale', 1.0)))
            elif settings.preset == 'VECTOR_GLYPHS':
                sa = getattr(settings, 'scale_attribute_name', '')
                sa2 = None if not sa or sa == 'NONE' else sa
                ng = _preset_vector_glyphs(
                    name,
                    settings.vector_attribute_name,
                    float(getattr(settings, 'scale', 1.0)),
                    sa2,
                    getattr(settings, 'material_name', '') or None,
                    float(getattr(settings, 'glyph_density', 1.0)),
                    int(getattr(settings, 'glyph_max_count', 0)),
                    str(getattr(settings, 'glyph_primitive', 'CONE')),
                    int(getattr(settings, 'cone_vertices', 16)),
                    float(getattr(settings, 'cone_radius_top', 0.0)),
                    float(getattr(settings, 'cone_radius_bottom', 0.02)),
                    float(getattr(settings, 'cone_depth', 0.1)),
                    int(getattr(settings, 'cyl_vertices', 16)),
                    float(getattr(settings, 'cyl_radius', 0.02)),
                    float(getattr(settings, 'cyl_depth', 0.1)),
                    int(getattr(settings, 'sphere_segments', 16)),
                    int(getattr(settings, 'sphere_rings', 8)),
                    float(getattr(settings, 'sphere_radius', 0.05)),
                )
            else:
                ng = _preset_points_shader(name, settings.attribute_name, settings.material_name or None)
        except Exception as e:
            print(f"[SciBlend Nodes] Preset creation error: {e}")
            self.report({'ERROR'}, f"Failed to create preset: {e}")
            return {'CANCELLED'}

        settings.node_group_name = ng.name
        settings.last_applied_signature = sig
        settings.last_applied_group_name = ng.name
        print(f"[SciBlend Nodes] Created node group '{ng.name}', applying to collection '{coll_name}'")
        return bpy.ops.sciblend_nodes.apply_filter()


class SCIBLENDNODES_OT_clear_collection_geo_nodes(Operator):
    bl_idname = "sciblend_nodes.clear_collection_geo_nodes"
    bl_label = "Remove Geo Nodes in Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Remove all Geometry Nodes modifiers from all mesh objects in the selected collection and clear its preset rows from the UI list."""
        settings = getattr(context.scene, 'sciblend_nodes_settings', None)
        if not settings:
            self.report({'ERROR'}, "SciBlend Nodes settings not available")
            return {'CANCELLED'}

        coll_name = None
        try:
            if getattr(settings, 'collections_list', None) and 0 <= int(getattr(settings, 'collections_list_index', -1)) < len(settings.collections_list):
                coll_name = settings.collections_list[settings.collections_list_index].name
        except Exception:
            coll_name = None
        if not coll_name:
            coll_name = getattr(settings, 'target_collection', '')
        if not coll_name:
            self.report({'ERROR'}, "Select a collection")
            return {'CANCELLED'}
        coll = bpy.data.collections.get(coll_name)
        if not coll:
            self.report({'ERROR'}, f"Collection not found: {coll_name}")
            return {'CANCELLED'}

        def _iter_objects_in_collection(c):
            try:
                all_objs = list(getattr(c, 'all_objects', []))
                if all_objs:
                    return [o for o in all_objs]
            except Exception:
                pass
            objs = list(getattr(c, 'objects', []))
            try:
                for ch in getattr(c, 'children', []):
                    objs.extend(_iter_objects_in_collection(ch))
            except Exception:
                pass
            return objs

        objs = _iter_objects_in_collection(coll)
        removed = 0
        affected_meshes = 0
        print(f"[SciBlend Nodes] Removing Geometry Nodes modifiers in collection '{coll_name}' for {len(objs)} object(s)")
        for obj in objs:
            if getattr(obj, 'type', None) != 'MESH':
                continue
            had_any = False
            for m in list(getattr(obj, 'modifiers', [])):
                if getattr(m, 'type', None) == 'NODES':
                    try:
                        obj.modifiers.remove(m)
                        removed += 1
                        had_any = True
                    except Exception as e:
                        print(f"[SciBlend Nodes] Failed removing modifier '{m.name}' on '{obj.name}': {e}")
            if had_any:
                affected_meshes += 1

        cleared = 0
        try:
            indices = [i for i, it in enumerate(getattr(settings, 'presets', [])) if getattr(it, 'collection_name', '') == coll_name]
            for i in reversed(indices):
                try:
                    settings.presets.remove(i)
                    cleared += 1
                except Exception as e:
                    print(f"[SciBlend Nodes] Failed removing preset row {i} for '{coll_name}': {e}")
            if getattr(settings, 'presets', None):
                next_idx = next((i for i, it in enumerate(settings.presets) if getattr(it, 'collection_name', '') == coll_name), -1)
                settings.presets_index = next_idx if next_idx >= 0 else min(settings.presets_index, max(0, len(settings.presets) - 1))
            else:
                settings.presets_index = 0
            print(f"[SciBlend Nodes] Cleared {cleared} preset row(s) for collection '{coll_name}'")
        except Exception as e:
            print(f"[SciBlend Nodes] Error clearing presets for '{coll_name}': {e}")

        self.report({'INFO'}, f"Removed {removed} Geometry Nodes modifier(s) from {affected_meshes} mesh(es) and {cleared} preset(s) in '{coll_name}'")
        print(f"[SciBlend Nodes] Removed {removed} GN modifiers from {affected_meshes} mesh(es) and {cleared} preset(s) in '{coll_name}'")
        return {'FINISHED'}


class SCIBLENDNODES_OT_rename_collection(Operator):
    bl_idname = "sciblend_nodes.rename_collection"
    bl_label = "Rename Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Rename the selected collection and update UI state and data references within SciBlend Nodes."""
        settings = getattr(context.scene, 'sciblend_nodes_settings', None)
        if not settings:
            self.report({'ERROR'}, "SciBlend Nodes settings not available")
            return {'CANCELLED'}

        coll_name = None
        try:
            if getattr(settings, 'collections_list', None) and 0 <= int(getattr(settings, 'collections_list_index', -1)) < len(settings.collections_list):
                coll_name = settings.collections_list[settings.collections_list_index].name
        except Exception:
            coll_name = None
        if not coll_name:
            coll_name = getattr(settings, 'target_collection', '')
        if not coll_name:
            self.report({'ERROR'}, "Select a collection")
            return {'CANCELLED'}
        coll = bpy.data.collections.get(coll_name)
        if not coll:
            self.report({'ERROR'}, f"Collection not found: {coll_name}")
            return {'CANCELLED'}

        new_name = getattr(settings, 'rename_collection_name', '').strip()
        if not new_name:
            self.report({'ERROR'}, "Enter a new name")
            return {'CANCELLED'}
        if new_name in bpy.data.collections:
            self.report({'ERROR'}, f"A collection with name '{new_name}' already exists")
            return {'CANCELLED'}

        print(f"[SciBlend Nodes] Renaming collection '{coll.name}' -> '{new_name}'")
        try:
            coll.name = new_name
        except Exception as e:
            self.report({'ERROR'}, f"Failed to rename: {e}")
            return {'CANCELLED'}

        updated = 0
        try:
            for it in getattr(settings, 'presets', []):
                if getattr(it, 'collection_name', '') == coll_name:
                    it.collection_name = new_name
                    updated += 1
        except Exception as e:
            print(f"[SciBlend Nodes] Failed updating preset rows: {e}")

        try:
            def _iter_objects_in_collection(c):
                try:
                    all_objs = list(getattr(c, 'all_objects', []))
                    if all_objs:
                        return [o for o in all_objs]
                except Exception:
                    pass
                objs = list(getattr(c, 'objects', []))
                try:
                    for ch in getattr(c, 'children', []):
                        objs.extend(_iter_objects_in_collection(ch))
                except Exception:
                    pass
                return objs
            for obj in _iter_objects_in_collection(coll):
                if getattr(obj, 'type', None) != 'MESH':
                    continue
                for m in getattr(obj, 'modifiers', []):
                    if getattr(m, 'type', None) == 'NODES' and bool(m.get('sciblend_nodes', False)):
                        try:
                            m['sciblend_collection'] = new_name
                        except Exception:
                            pass
        except Exception as e:
            print(f"[SciBlend Nodes] Failed updating modifiers metadata: {e}")

        try:
            if 0 <= int(getattr(settings, 'collections_list_index', -1)) < len(settings.collections_list):
                settings.collections_list[settings.collections_list_index].name = new_name
            settings.target_collection = new_name
        except Exception:
            pass

        self.report({'INFO'}, f"Renamed collection to '{new_name}', updated {updated} preset(s)")
        print(f"[SciBlend Nodes] Renamed collection to '{new_name}', updated {updated} preset(s)")
        return {'FINISHED'} 