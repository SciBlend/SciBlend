import bpy


class FILTERS_OT_create_emitter(bpy.types.Operator):
    bl_idname = "filters.create_emitter"
    bl_label = "Create Stream Emitter"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = getattr(context.scene, "filters_emitter_settings", None)
        if not settings:
            self.report({'ERROR'}, "Filters settings not available")
            return {'CANCELLED'}
        if not settings.target_object or not settings.vector_attribute:
            self.report({'ERROR'}, "Select a mesh and a vector attribute.")
            return {'CANCELLED'}

        emitter_type = settings.emitter_type
        if emitter_type == 'POINT':
            obj = bpy.data.objects.new("StreamEmitter", None)
            obj.empty_display_type = 'ARROWS'
            obj.empty_display_size = 0.3
        else:
            mesh = bpy.data.meshes.new("StreamEmitterMesh")
            from mathutils import Vector
            verts = [
                (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
                (-0.5, -0.5,  0.5), (0.5, -0.5,  0.5), (0.5, 0.5,  0.5), (-0.5, 0.5,  0.5),
            ]
            faces = [
                (0, 1, 2, 3), (4, 5, 6, 7),
                (0, 1, 5, 4), (2, 3, 7, 6),
                (1, 2, 6, 5), (0, 3, 7, 4),
            ]
            mesh.from_pydata([Vector(v) for v in verts], [], faces)
            mesh.update()
            obj = bpy.data.objects.new("StreamEmitter", mesh)
            obj.display_type = 'WIRE'
            obj.show_in_front = True
            obj.scale = (0.3, 0.3, 0.3)

        context.collection.objects.link(obj)

        obj["filters_domain_object"] = settings.target_object.name
        obj["filters_vector_attr"] = settings.vector_attribute
        obj["filters_emitter_type"] = emitter_type

        for o in context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj

        return {'FINISHED'}


def register():
    bpy.utils.register_class(FILTERS_OT_create_emitter)


def unregister():
    bpy.utils.unregister_class(FILTERS_OT_create_emitter) 