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
            return {'CANCELLED'}
        idx = self.index if self.index >= 0 else int(getattr(settings, 'presets_index', -1))
        if not (0 <= idx < len(settings.presets)):
            return {'CANCELLED'}
        item = settings.presets[idx]
        try:
            from .create_presets import _preset_points_shader
            base_name = f"SciBlend_{item.preset}"
            name = base_name
            i = 1
            while name in bpy.data.node_groups:
                i += 1
                name = f"{base_name}.{i:03d}"
            ng = _preset_points_shader(name, item.attribute_name, item.material_override or None)
        except Exception:
            return {'CANCELLED'}
        settings.node_group_name = ng.name
        try:
            item.node_group_name = ng.name
        except Exception:
            pass
        return bpy.ops.sciblend_nodes.apply_filter() 