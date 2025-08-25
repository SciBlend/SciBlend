import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, CollectionProperty
import os
import re
from .x3d_utils import import_x3d_minimal
from ..utils.scene import clear_scene, keyframe_visibility_single_frame, enforce_constant_interpolation


class ImportX3DOperator(bpy.types.Operator, ImportHelper):
    """Import X3D files into Blender (static or animated)."""
    bl_idname = "import_x3d.animation"
    bl_label = "Import X3D"
    filename_ext = ""

    files: CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )
    directory: StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        """Import selected .x3d files as a sequence (or a single file if one is selected)."""
        settings = context.scene.x3d_import_settings
        scale_factor = settings.scale_factor
        loop_count = max(1, getattr(settings, "loop_count", 1))

        selected_files = [f.name for f in self.files] if self.files else []
        if selected_files:
            x3d_files = [os.path.join(self.directory, f) for f in selected_files if f.lower().endswith('.x3d')]
        else:
            if self.filepath and self.filepath.lower().endswith('.x3d'):
                x3d_files = [self.filepath]
            else:
                x3d_files = []

        x3d_files = sorted([p for p in x3d_files if os.path.exists(p)])

        if settings.overwrite_scene:
            clear_scene(context)

        material = settings.shared_material
        if material is None:
            material = bpy.data.materials.new(name="SharedMaterial")
            material.use_nodes = True
            nodes = material.node_tree.nodes
            links = material.node_tree.links
            for node in list(nodes):
                nodes.remove(node)
            attribute_node = nodes.new(type='ShaderNodeAttribute')
            attribute_node.attribute_name = 'Col'
            bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
            material_output = nodes.new(type='ShaderNodeOutputMaterial')
            links.new(attribute_node.outputs['Color'], bsdf.inputs['Base Color'])
            links.new(bsdf.outputs['BSDF'], material_output.inputs['Surface'])

        imported_count = 0
        num_frames = len(x3d_files)
        for frame, x3d_file in enumerate(x3d_files, start=1):
            try:
                obj = import_x3d_minimal(x3d_file, name=os.path.basename(x3d_file), scale=scale_factor)
                imported_objects = [obj]
            except Exception:
                continue

            imported_count += 1
            for obj in imported_objects:
                if obj.type == 'MESH':
                    obj.data.materials.clear()
                    obj.data.materials.append(material)
                if num_frames > 1 or loop_count > 1:
                    for k in range(loop_count):
                        occurrence = frame + (k * num_frames)
                        keyframe_visibility_single_frame(obj, occurrence)
                    enforce_constant_interpolation(obj)

        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = max(1, (imported_count if num_frames > 0 else 1) * loop_count)
        bpy.context.scene.frame_current = 1

        for obj in bpy.data.objects:
            if obj.animation_data and obj.animation_data.action:
                for fcurve in obj.animation_data.action.fcurves:
                    for kf in fcurve.keyframe_points:
                        kf.interpolation = 'CONSTANT'
        return {'FINISHED'}


__all__ = [
    "ImportX3DOperator",
] 