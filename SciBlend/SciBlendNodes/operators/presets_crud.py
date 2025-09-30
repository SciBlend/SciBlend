import bpy
from bpy.types import Operator


class SCIBLENDNODES_OT_preset_add(Operator):
    bl_idname = "sciblend_nodes.preset_add"
    bl_label = "Add Preset"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: bpy.props.StringProperty(name="Collection", default="")

    def execute(self, context):
        settings = getattr(context.scene, 'sciblend_nodes_settings', None)
        if not settings:
            return {'CANCELLED'}
        item = settings.presets.add()
        item.collection_name = self.collection_name or settings.target_collection
        item.preset = settings.preset
        item.attribute_name = settings.attribute_name
        item.vector_attribute_name = settings.vector_attribute_name
        item.material_override = settings.material_name
        item.points_radius = settings.points_radius
        item.scale = settings.scale
        try:
            item.scale_attribute_name = settings.scale_attribute_name if getattr(settings, 'scale_attribute_name', '') else 'NONE'
        except Exception:
            try:
                item.scale_attribute_name = 'NONE'
            except Exception:
                pass
        try:
            item.glyph_density = settings.glyph_density
            item.glyph_max_count = settings.glyph_max_count
            item.glyph_primitive = settings.glyph_primitive
            item.cone_vertices = settings.cone_vertices
            item.cone_radius_top = settings.cone_radius_top
            item.cone_radius_bottom = settings.cone_radius_bottom
            item.cone_depth = settings.cone_depth
            item.cyl_vertices = settings.cyl_vertices
            item.cyl_radius = settings.cyl_radius
            item.cyl_depth = settings.cyl_depth
            item.sphere_segments = settings.sphere_segments
            item.sphere_rings = settings.sphere_rings
            item.sphere_radius = settings.sphere_radius
        except Exception:
            pass
        item.radius = settings.radius
        item.voxel_size = settings.voxel_size
        item.threshold = settings.threshold
        item.plane_point = settings.plane_point
        item.plane_normal = settings.plane_normal
        settings.presets_index = len(settings.presets) - 1
        return {'FINISHED'}


class SCIBLENDNODES_OT_preset_remove(Operator):
    bl_idname = "sciblend_nodes.preset_remove"
    bl_label = "Remove Preset"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty(name="Index", default=-1)

    def execute(self, context):
        settings = getattr(context.scene, 'sciblend_nodes_settings', None)
        if not settings or not settings.presets:
            return {'CANCELLED'}
        idx = self.index if self.index >= 0 else int(getattr(settings, 'presets_index', -1))
        if 0 <= idx < len(settings.presets):
            settings.presets.remove(idx)
            settings.presets_index = max(0, idx - 1)
        return {'FINISHED'}


class SCIBLENDNODES_OT_preset_apply_selected(Operator):
    bl_idname = "sciblend_nodes.preset_apply_selected"
    bl_label = "Apply Selected Preset"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty(name="Index", default=-1)

    def execute(self, context):
        settings = getattr(context.scene, 'sciblend_nodes_settings', None)
        if not settings or not settings.presets:
            self.report({'ERROR'}, "No presets to apply")
            return {'CANCELLED'}
        idx = self.index if self.index >= 0 else int(getattr(settings, 'presets_index', -1))
        if not (0 <= idx < len(settings.presets)):
            self.report({'ERROR'}, "Invalid preset index")
            return {'CANCELLED'}
        item = settings.presets[idx]
        try:
            from .create_presets import _preset_points_shader, _preset_displace_normal, _preset_vector_glyphs
            base_name = f"SciBlend_{item.preset}"
            name = base_name
            i = 1
            while name in bpy.data.node_groups:
                i += 1
                name = f"{base_name}.{i:03d}"
            if item.preset == 'DISPLACE_NORMAL':
                ng = _preset_displace_normal(name, item.attribute_name, float(getattr(item, 'scale', 1.0)))
            elif item.preset == 'VECTOR_GLYPHS':
                sa = getattr(item, 'scale_attribute_name', '')
                sa2 = None if not sa or sa == 'NONE' else sa
                ng = _preset_vector_glyphs(
                    name,
                    item.vector_attribute_name,
                    float(getattr(item, 'scale', 1.0)),
                    sa2,
                    getattr(item, 'material_override', '') or None,
                    float(getattr(item, 'glyph_density', 1.0)),
                    int(getattr(item, 'glyph_max_count', 0)),
                    str(getattr(item, 'glyph_primitive', 'CONE')),
                    int(getattr(item, 'cone_vertices', 16)),
                    float(getattr(item, 'cone_radius_top', 0.0)),
                    float(getattr(item, 'cone_radius_bottom', 0.02)),
                    float(getattr(item, 'cone_depth', 0.1)),
                    int(getattr(item, 'cyl_vertices', 16)),
                    float(getattr(item, 'cyl_radius', 0.02)),
                    float(getattr(item, 'cyl_depth', 0.1)),
                    int(getattr(item, 'sphere_segments', 16)),
                    int(getattr(item, 'sphere_rings', 8)),
                    float(getattr(item, 'sphere_radius', 0.05)),
                )
            else:
                ng = _preset_points_shader(name, item.attribute_name, item.material_override or None)
        except Exception as e:
            print(f"[SciBlend Nodes] Preset apply failed: {e}")
            self.report({'ERROR'}, f"Failed to create preset: {e}")
            return {'CANCELLED'}
        settings.node_group_name = ng.name
        try:
            item.node_group_name = ng.name
        except Exception:
            pass
        try:
            if getattr(item, 'collection_name', ''):
                settings.target_collection = item.collection_name
        except Exception:
            pass
        print(f"[SciBlend Nodes] Created node group '{ng.name}' from selected preset; applying to collection")
        return bpy.ops.sciblend_nodes.apply_filter() 