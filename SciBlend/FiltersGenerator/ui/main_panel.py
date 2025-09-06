import bpy


class FILTERSGENERATOR_PT_main_panel(bpy.types.Panel):
    bl_label = "Filters Generator"
    bl_idname = "FILTERSGENERATOR_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SciBlend'

    def draw(self, context):
        layout = self.layout
        layout.label(text="Stream and Volume filters", icon='FILTER')


class FILTERSGENERATOR_PT_stream_tracers(bpy.types.Panel):
    bl_label = "Stream Tracers"
    bl_idname = "FILTERSGENERATOR_PT_stream_tracers"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'FILTERSGENERATOR_PT_main_panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        s = getattr(context.scene, "filters_emitter_settings", None)
        if not s:
            layout.label(text="Filters settings unavailable", icon='ERROR')
            return

        layout.prop(s, "target_object", text="Domain Mesh")
        layout.prop(s, "vector_attribute", text="Vector Field")
        layout.prop(s, "emitter_type", text="Emitter")

        box = layout.box()
        box.label(text="Integrator", icon='MOD_PHYSICS')
        col = box.column(align=True)
        col.prop(s, "integration_direction", text="Direction")
        col.prop(s, "step_size")
        col.prop(s, "max_steps")
        col.prop(s, "max_length")
        col.prop(s, "min_velocity")
        col.prop(s, "k_neighbors")
        col.prop(s, "field_scale")
        col.prop(s, "normalize_field")
        col.prop(s, "stop_at_bounds")
        col.prop(s, "bbox_margin")

        row = layout.row(align=True)
        row.operator("filters.create_emitter", text="Create Emitter", icon='PARTICLES')
        row.operator("filters.place_emitter", text="Place", icon='MOUSE_LMB')

        layout.operator("filters.generate_streamline", text="Generate Streamline", icon='CURVE_DATA')


class FILTERSGENERATOR_PT_volume_filter(bpy.types.Panel):
    bl_label = "Volume Filter"
    bl_idname = "FILTERSGENERATOR_PT_volume_filter"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'FILTERSGENERATOR_PT_main_panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Coming soon", icon='INFO') 