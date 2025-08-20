import bpy
from bpy_extras.object_utils import world_to_camera_view

class COMPOSITOR_PT_panel(bpy.types.Panel):
    bl_label = "Compositor"
    bl_idname = "COMPOSITOR_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Compositor'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        camera = scene.camera
        cset = getattr(scene, 'cinematography_settings', None)

        box = layout.box()
        box.label(text="Cinematography")

        row = box.row()
        row.prop(context.space_data, "lock_camera", text="Lock Camera to View")

        if not cset:
            box.label(text="Cinematography settings not available", icon='INFO')
            return

        row = box.row()
        row.prop(cset, "camera_type", expand=True)

        if camera and camera.type == 'CAMERA':
            if cset.camera_type == 'PERSP':
                self.draw_perspective_settings(context, box)
            elif cset.camera_type == 'ORTHO':
                self.draw_orthographic_settings(context, box)
            
            self.draw_clip_settings(context, box)

        box = layout.box()
        row = box.row()
        row.prop(cset, "show_camera_manager", icon="TRIA_DOWN" if cset.show_camera_manager else "TRIA_RIGHT", icon_only=True, emboss=False)
        row.label(text="Camera Manager")

        if cset.show_camera_manager:
            self.draw_camera_manager(context, box)

        self.draw_output_resolution(context, layout)

    def draw_output_resolution(self, context, layout):
        box = layout.box()
        box.label(text="Output Resolution")

        self.draw_render_resolution(context, box)

        self.draw_print_resolution(context, layout)

    def draw_camera_manager(self, context, layout):
        scene = context.scene
        cset = scene.cinematography_settings
        row = layout.row()
        row.template_list("CAMERA_UL_list", "", cset, "camera_list", cset, "camera_list_index", rows=3)

        col = row.column(align=True)
        col.operator("camera.add_to_list", icon='ADD', text="")
        col.operator("camera.remove_from_list", icon='REMOVE', text="")
        col.separator()
        col.operator("camera.move_in_list", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("camera.move_in_list", icon='TRIA_DOWN', text="").direction = 'DOWN'
        col.separator()
        col.operator("camera.sort_list", icon='SORTALPHA', text="")

        row = layout.row()
        row.operator("camera.update_timeline", text="Update Timeline")
        row.operator("camera.erase_all_keyframes", text="Erase All Keyframes")

        if cset.camera_list and cset.camera_list_index >= 0:
            camera_item = cset.camera_list[cset.camera_list_index]
            camera_obj = bpy.data.objects.get(camera_item.name)
            if camera_obj and camera_obj.type == 'CAMERA':
                box = layout.box()
                row = box.row()
                row.prop(camera_obj, "name")
                row = box.row()
                row.prop(camera_obj.camera_range, "start_frame")
                row.prop(camera_obj.camera_range, "end_frame")
                
                row = box.row()
                row.operator("camera.view_selected", text="View Camera")

    def draw_perspective_settings(self, context, layout):
        camera = context.scene.camera
        if camera and camera.type == 'CAMERA':
            layout.prop(camera.data, "lens")

    def draw_orthographic_settings(self, context, layout):
        camera = context.scene.camera
        if camera and camera.type == 'CAMERA':
            layout.prop(camera.data, "ortho_scale", text="Orthographic Scale")

    def draw_clip_settings(self, context, layout):
        camera = context.scene.camera
        if camera and camera.type == 'CAMERA':
            layout.separator()
            col = layout.column(align=True)
            col.label(text="Clipping:")
            col.prop(camera.data, "clip_start", text="Start")
            col.prop(camera.data, "clip_end", text="End")

    def draw_render_resolution(self, context, layout):
        cset = context.scene.cinematography_settings
        row = layout.row()
        row.label(text="Render Resolution:")
        
        sub_row = row.row(align=True)
        sub_row.prop(cset, "custom_resolution_x", text="X")
        sub_row.prop(cset, "custom_resolution_y", text="Y")
        
        row = layout.row()
        row.prop(cset, "resolution_linked", text="Link Resolution")

    def draw_print_resolution(self, context, layout):
        cset = context.scene.cinematography_settings
        layout.separator()

        box = layout.box()
        row = box.row()
        row.prop(cset, "show_cinema_formats", icon="TRIA_DOWN" if cset.show_cinema_formats else "TRIA_RIGHT", icon_only=True, emboss=False)
        row.label(text="Cinema Formats")

        if cset.show_cinema_formats:
            col = box.column(align=True)
            for item in cset.bl_rna.properties["cinema_format"].enum_items:
                op = col.operator("cinematography.set_cinema_resolution", text=item.name)
                if op:
                    op.format = item.identifier

        box = layout.box()
        row = box.row()
        row.prop(cset, "show_print_formats", icon="TRIA_DOWN" if cset.show_print_formats else "TRIA_RIGHT", icon_only=True, emboss=False)
        row.label(text="Print Formats")

        if cset.show_print_formats:
            col = box.column(align=True)
            for item in cset.bl_rna.properties["print_format"].enum_items:
                op = col.operator("cinematography.set_print_resolution", text=item.name)
                if op:
                    op.format = item.identifier

        row = layout.row()
        row.prop(cset, "frame_rate")
        
        row = layout.row()
        row.prop(cset, "resolution_orientation")
        
        row = layout.row()
        row.prop(cset, "print_dpi")

def register():
    print("Registering COMPOSITOR_PT_panel")
    try:
        bpy.utils.register_class(COMPOSITOR_PT_panel)
    except Exception as e:
        print(f"Error registering COMPOSITOR_PT_panel: {str(e)}")

def unregister():
    print("Unregistering COMPOSITOR_PT_panel")  
    try:
        bpy.utils.unregister_class(COMPOSITOR_PT_panel)
    except Exception as e:
        print(f"Error unregistering COMPOSITOR_PT_panel: {str(e)}")