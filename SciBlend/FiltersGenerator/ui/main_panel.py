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
        s = getattr(context.scene, "filters_volume_settings", None)
        if not s:
            layout.label(text="Volume settings unavailable", icon='ERROR')
            return

        layout.operator("filters.volume_import_vdb_sequence", text="Import VDB Sequence", icon='FILE_FOLDER')
        layout.prop(s, "volume_object", text="Volume")
        layout.prop(s, "grid_name", text="Grid")
        layout.prop(s, "colormap", text="Colormap")

        box = layout.box()
        box.label(text="Range & Density", icon='SEQ_LUMA_WAVEFORM')
        row = box.row(align=True)
        row.prop(s, "auto_range")
        row.operator("filters.volume_compute_range", text="Compute Range", icon='IPO_CONSTANT')
        col = box.column(align=True)
        col.prop(s, "from_min")
        col.prop(s, "from_max")
        col.prop(s, "density_scale")
        col.prop(s, "anisotropy")
        col.prop(s, "emission_strength")

        box = layout.box()
        box.label(text="Slice", icon='MOD_SOLIDIFY')
        col = box.column(align=True)
        col.prop(s, "slice_object", text="Slicing Object")
        col.prop(s, "slice_invert")

        layout.operator("filters.volume_update_material", text="Update Material", icon='SHADING_RENDERED')


class FILTERSGENERATOR_PT_geometry_filters(bpy.types.Panel):
    bl_label = "Geometry Filters"
    bl_idname = "FILTERSGENERATOR_PT_geometry_filters"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'FILTERSGENERATOR_PT_main_panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="Threshold (closed surface)", icon='MESH_DATA')
        s = getattr(context.scene, "filters_threshold_settings", None)
        if not s:
            box.label(text="Threshold settings unavailable", icon='ERROR')
        else:
            col = box.column(align=True)
            col.prop(s, "target_object", text="Domain Mesh")
            row = col.row(align=True)
            row.prop(s, "domain", text="Domain")
            if getattr(s, 'domain', 'CELL') == 'POINT':
                row = col.row(align=True)
                row.prop(s, "aggregator", text="Aggregator")
            col.prop(s, "attribute", text="Attribute")
            row = col.row(align=True)
            row.prop(s, "min_value")
            row.prop(s, "max_value")
            col.operator("filters.build_threshold_surface", text="Build/Update", icon='MESH_DATA')

        box = layout.box()
        box.label(text="Contour (isosurface)", icon='MESH_DATA')
        c = getattr(context.scene, "filters_contour_settings", None)
        if not c:
            box.label(text="Contour settings unavailable", icon='ERROR')
        else:
            col = box.column(align=True)
            col.prop(c, "target_object", text="Domain Mesh")
            row = col.row(align=True)
            row.prop(c, "domain", text="Domain")
            if getattr(c, 'domain', 'CELL') == 'POINT':
                row = col.row(align=True)
                row.prop(c, "aggregator", text="Aggregator")
            col.prop(c, "attribute", text="Attribute")
            col.prop(c, "iso_value", text="Iso Value")
            col.operator("filters.build_contour_surface", text="Build/Update", icon='MESH_DATA')

        box = layout.box()
        box.label(text="Slice (plane)", icon='MESH_DATA')
        sl = getattr(context.scene, "filters_slice_settings", None)
        if not sl:
            box.label(text="Slice settings unavailable", icon='ERROR')
        else:
            col = box.column(align=True)
            col.prop(sl, "target_object", text="Domain Mesh")
            row = col.row(align=True)
            row.prop(sl, "plane_object", text="Slice Plane")
            row.operator("filters.slice_ensure_plane", text="Ensure", icon='MESH_PLANE')
            col.operator("filters.build_slice_surface", text="Build/Update", icon='MESH_DATA')

        box = layout.box()
        box.label(text="Clip (plane)", icon='MESH_DATA')
        cl = getattr(context.scene, "filters_clip_settings", None)
        if not cl:
            box.label(text="Clip settings unavailable", icon='ERROR')
            return
        col = box.column(align=True)
        col.prop(cl, "target_object", text="Domain Mesh")
        row = col.row(align=True)
        row.prop(cl, "plane_object", text="Clip Plane")
        row.operator("filters.clip_ensure_plane", text="Ensure", icon='MESH_PLANE')
        col.prop(cl, "side", text="Side")
        col.operator("filters.build_clip_surface", text="Build/Update", icon='MESH_DATA') 