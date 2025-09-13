import bpy
from mathutils import Vector
from ..utils.field_sampling import VectorFieldSampler
from ..utils.integrators import integrate_streamline


class FILTERS_OT_generate_streamline(bpy.types.Operator):
    bl_idname = "filters.generate_streamline"
    bl_label = "Generate Streamline"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = getattr(context.scene, "filters_emitter_settings", None)
        if not s or not s.target_object or not s.vector_attribute:
            self.report({'ERROR'}, "Select a mesh and a vector attribute in Filters Generator.")
            return {'CANCELLED'}

        # Find selected emitter
        emitter = None
        for obj in context.selected_objects:
            if obj.name.startswith("StreamEmitter"):
                emitter = obj
                break
        if emitter is None:
            self.report({'ERROR'}, "Select a StreamEmitter object.")
            return {'CANCELLED'}

        emitter_type = emitter.get("filters_emitter_type", 'POINT')

        try:
            sampler = VectorFieldSampler(s.target_object, s.vector_attribute)
        except Exception as e:
            self.report({'ERROR'}, f"Sampler error: {e}")
            return {'CANCELLED'}

        def inside(p: Vector):
            if not s.stop_at_bounds:
                return True
            return sampler.inside_bbox(p, margin=max(0.0, s.bbox_margin))

        def field_func_forward(p: Vector):
            v = sampler.sample(p, k_neighbors=max(1, s.k_neighbors), normalize=bool(s.normalize_field))
            return v * s.field_scale

        def field_func_backward(p: Vector):
            v = sampler.sample(p, k_neighbors=max(1, s.k_neighbors), normalize=bool(s.normalize_field))
            return (-v) * s.field_scale

        seeds = []
        if emitter_type == 'POINT' or emitter.type == 'EMPTY':
            seeds = [emitter.matrix_world.translation.copy()]
        else:
            mesh = emitter.data
            mw = emitter.matrix_world
            if not hasattr(mesh, 'polygons') or len(mesh.polygons) == 0:
                seeds = [emitter.matrix_world.translation.copy()]
            else:
                seeds = [mw @ p.center for p in mesh.polygons]

        created = 0
        for seed in seeds:
            dir_mode = s.integration_direction
            if dir_mode in {'FORWARD', 'BOTH'}:
                pts_f = integrate_streamline(
                    seed,
                    step_size=max(1e-6, s.step_size),
                    max_steps=max(1, s.max_steps),
                    min_vel=max(0.0, s.min_velocity),
                    max_length=max(0.0, s.max_length),
                    field_func=field_func_forward,
                    inside_domain=inside,
                )
                if len(pts_f) >= 2:
                    self._create_curve(context, pts_f)
                    created += 1
            if dir_mode in {'BACKWARD', 'BOTH'}:
                pts_b = integrate_streamline(
                    seed,
                    step_size=max(1e-6, s.step_size),
                    max_steps=max(1, s.max_steps),
                    min_vel=max(0.0, s.min_velocity),
                    max_length=max(0.0, s.max_length),
                    field_func=field_func_backward,
                    inside_domain=inside,
                )
                if len(pts_b) >= 2:
                    if dir_mode == 'BOTH' and 'pts_f' in locals() and len(pts_f) >= 2:
                        merged = list(reversed(pts_b))[0:-1] + pts_f
                        self._create_curve(context, merged)
                    else:
                        self._create_curve(context, pts_b)
                    created += 1

        if created == 0:
            self.report({'WARNING'}, "No streamlines created from emitter")
            return {'CANCELLED'}

        return {'FINISHED'}

    def _create_curve(self, context, pts):
        curve_data = bpy.data.curves.new("Streamline", type='CURVE')
        curve_data.dimensions = '3D'
        spline = curve_data.splines.new('POLY')
        spline.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            spline.points[i].co = (p.x, p.y, p.z, 1.0)
        curve_obj = bpy.data.objects.new("Streamline", curve_data)
        context.collection.objects.link(curve_obj)


def register():
    bpy.utils.register_class(FILTERS_OT_generate_streamline)


def unregister():
    bpy.utils.unregister_class(FILTERS_OT_generate_streamline) 