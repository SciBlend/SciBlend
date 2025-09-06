import bpy


class FILTERS_OT_place_emitter(bpy.types.Operator):
    bl_idname = "filters.place_emitter"
    bl_label = "Place Emitter at 3D Cursor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cursor_loc = context.scene.cursor.location.copy()
        emitter = None
        sel = context.selected_objects
        if sel:
            for obj in sel:
                if obj.type == 'EMPTY' and obj.name.startswith("StreamEmitter"):
                    emitter = obj
                    break
        if emitter is None:
            self.report({'ERROR'}, "Select a StreamEmitter object to place.")
            return {'CANCELLED'}
        emitter.location = cursor_loc
        return {'FINISHED'}


def register():
    bpy.utils.register_class(FILTERS_OT_place_emitter)


def unregister():
    bpy.utils.unregister_class(FILTERS_OT_place_emitter) 