import bpy
from bpy.props import IntProperty, PointerProperty, CollectionProperty, StringProperty, BoolProperty
from bpy.types import PropertyGroup, UIList, Operator

class CameraListItem(PropertyGroup):
    name: StringProperty()

class CameraRangeProperties(PropertyGroup):
    start_frame: IntProperty(name="Start Frame", default=1, min=1)
    end_frame: IntProperty(name="End Frame", default=250, min=1)

class CAMERA_UL_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            camera_obj = bpy.data.objects.get(item.name)
            if camera_obj and camera_obj.type == 'CAMERA':
                row.prop(camera_obj, "name", text="", emboss=False, icon='CAMERA_DATA')
                sub = row.row(align=True)
                sub.scale_x = 0.5
                sub.prop(camera_obj.camera_range, "start_frame", text="Start")
                sub.prop(camera_obj.camera_range, "end_frame", text="End")
            else:
                row.label(text=item.name, icon='ERROR')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='CAMERA_DATA')

class CAMERA_OT_add(Operator):
    bl_idname = "camera.add_to_list"
    bl_label = "Add Camera"
    bl_description = "Add a new camera to the scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.camera_add()
        new_camera = context.active_object
        new_camera.camera_range.start_frame = context.scene.frame_start
        new_camera.camera_range.end_frame = context.scene.frame_end
        item = context.scene.camera_list.add()
        item.name = new_camera.name
        
        context.scene.camera = new_camera
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'
                break
        
        return {'FINISHED'}

class CAMERA_OT_remove(Operator):
    bl_idname = "camera.remove_from_list"
    bl_label = "Remove Camera"
    bl_description = "Remove the selected camera from the scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera_list_index >= 0 and len(context.scene.camera_list) > 0

    def execute(self, context):
        scene = context.scene
        index = scene.camera_list_index
        camera_name = scene.camera_list[index].name
        camera_obj = bpy.data.objects.get(camera_name)
        
        if camera_obj:
            bpy.data.objects.remove(camera_obj, do_unlink=True)
        
        scene.camera_list.remove(index)
        scene.camera_list_index = min(max(0, index - 1), len(scene.camera_list) - 1)
        return {'FINISHED'}

class CAMERA_OT_move(Operator):
    bl_idname = "camera.move_in_list"
    bl_label = "Move Camera"
    bl_description = "Move the selected camera up or down in the list"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
        )
    )

    @classmethod
    def poll(cls, context):
        return len(context.scene.camera_list) > 1

    def execute(self, context):
        scene = context.scene
        index = scene.camera_list_index
        neighbor = index + (-1 if self.direction == 'UP' else 1)
        scene.camera_list.move(neighbor, index)
        scene.camera_list_index = neighbor
        return {'FINISHED'}

class CAMERA_OT_sort(Operator):
    bl_idname = "camera.sort_list"
    bl_label = "Sort Cameras"
    bl_description = "Sort cameras by their start frame"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        camera_list = [(item.name, bpy.data.objects[item.name].camera_range.start_frame) for item in scene.camera_list]
        sorted_list = sorted(camera_list, key=lambda x: x[1])
        scene.camera_list.clear()
        for name, _ in sorted_list:
            scene.camera_list.add().name = name
        return {'FINISHED'}

class CAMERA_OT_update_timeline(Operator):
    bl_idname = "camera.update_timeline"
    bl_label = "Update Timeline"
    bl_description = "Update timeline markers for camera ranges"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        for obj in scene.objects:
            if obj.type == 'CAMERA':
                update_camera_markers(obj, scene)
        return {'FINISHED'}

class CAMERA_OT_erase_all_keyframes(Operator):
    bl_idname = "camera.erase_all_keyframes"
    bl_label = "Erase All Camera Keyframes"
    bl_description = "Erase all camera keyframes, timeline markers, and reset camera ranges"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        
        marker_count = len(scene.timeline_markers)
        scene.timeline_markers.clear()
        self.report({'INFO'}, f"Cleared {marker_count} timeline markers")
        
        camera_count = 0
        for obj in scene.objects:
            if obj.type == 'CAMERA':
                camera_count += 1
                self.report({'INFO'}, f"Processing camera: {obj.name}")
                
                if obj.animation_data:
                    obj.animation_data_clear()
                    self.report({'INFO'}, f"Cleared animation data for {obj.name}")
                
                if hasattr(obj, "camera_range"):
                    obj.camera_range.start_frame = scene.frame_start
                    obj.camera_range.end_frame = scene.frame_end
                    self.report({'INFO'}, f"Reset camera range for {obj.name}")
                
                if obj.animation_data and obj.animation_data.action:
                    obj.animation_data.action.fcurves.clear()
                    self.report({'INFO'}, f"Removed all keyframes for {obj.name}")

        self.report({'INFO'}, f"Processed {camera_count} cameras")
        
        scene.camera_list.clear()
        for obj in scene.objects:
            if obj.type == 'CAMERA':
                item = scene.camera_list.add()
                item.name = obj.name
        scene.camera_list_index = 0 if len(scene.camera_list) > 0 else -1
        
        for area in context.screen.areas:
            area.tag_redraw()
        
        self.report({'INFO'}, "All camera keyframes, timeline markers, and camera ranges have been reset")
        return {'FINISHED'}

class CAMERA_OT_view_selected(Operator):
    bl_idname = "camera.view_selected"
    bl_label = "View Selected Camera"
    bl_description = "Switch view to the selected camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        if scene.camera_list and scene.camera_list_index >= 0:
            camera_item = scene.camera_list[scene.camera_list_index]
            camera_obj = bpy.data.objects.get(camera_item.name)
            if camera_obj and camera_obj.type == 'CAMERA':
                context.scene.camera = camera_obj
                bpy.ops.view3d.view_camera()
        return {'FINISHED'}

def update_camera_range(self, context):
    scene = context.scene
    for obj in scene.objects:
        if obj.type == 'CAMERA':
            update_camera_markers(obj, scene)

def update_camera_markers(camera, scene):
    camera_name = camera.name
    start_frame = camera.camera_range.start_frame
    end_frame = camera.camera_range.end_frame

    markers_to_remove = [m for m in scene.timeline_markers if m.camera == camera]
    for marker in markers_to_remove:
        scene.timeline_markers.remove(marker)

    scene.timeline_markers.new(f"{camera_name}_start", frame=start_frame)
    scene.timeline_markers.new(f"{camera_name}_end", frame=end_frame)

    for marker in scene.timeline_markers:
        if marker.name.startswith(camera_name):
            marker.camera = camera

def update_camera_list_index(self, context):
    if context.scene.camera_list and context.scene.camera_list_index >= 0:
        camera_item = context.scene.camera_list[context.scene.camera_list_index]
        camera_obj = bpy.data.objects.get(camera_item.name)
        if camera_obj and camera_obj.type == 'CAMERA':
            context.scene.camera = camera_obj
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.spaces[0].region_3d.view_perspective = 'CAMERA'
                    break

classes = (
    CameraListItem,
    CameraRangeProperties,
    CAMERA_UL_list,
    CAMERA_OT_add,
    CAMERA_OT_remove,
    CAMERA_OT_move,
    CAMERA_OT_sort,
    CAMERA_OT_update_timeline,
    CAMERA_OT_erase_all_keyframes,
    CAMERA_OT_view_selected, 
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.camera_range = PointerProperty(type=CameraRangeProperties)
    bpy.types.Scene.camera_list = CollectionProperty(type=CameraListItem)
    bpy.types.Scene.camera_list_index = IntProperty(update=update_camera_list_index)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Object.camera_range
    del bpy.types.Scene.camera_list
    del bpy.types.Scene.camera_list_index

if __name__ == "__main__":
    register()