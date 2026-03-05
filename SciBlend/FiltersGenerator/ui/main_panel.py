import bpy


class FILTERSGENERATOR_PT_main_panel(bpy.types.Panel):
    bl_label = "Filters Generator"
    bl_idname = "FILTERSGENERATOR_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SciBlend'
    bl_options = {'DEFAULT_CLOSED'}

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
        settings = getattr(context.scene, "filters_volume_settings", None)
        if not settings:
            layout.label(text="Volume settings unavailable", icon='ERROR')
            return

        layout.operator("filters.volume_import_vdb_sequence", text="Import VDB Sequence", icon='FILE_FOLDER')
        
        box = layout.box()
        box.label(text="Volumes", icon='OUTLINER_OB_VOLUME')
        row = box.row()
        row.template_list(
            "FILTERS_UL_volume_list",
            "",
            settings,
            "volume_items",
            settings,
            "volume_items_index",
            rows=3
        )
        
        col = row.column(align=True)
        col.operator("filters.volume_item_add", text="", icon='ADD')
        col.operator("filters.volume_item_remove", text="", icon='REMOVE')
        col.separator()
        col.operator("filters.volume_item_move_up", text="", icon='TRIA_UP')
        col.operator("filters.volume_item_move_down", text="", icon='TRIA_DOWN')
        
        if not settings.volume_items:
            layout.label(text="No volumes in list", icon='INFO')
            return
        
        if settings.volume_items_index >= len(settings.volume_items):
            return
        
        item = settings.volume_items[settings.volume_items_index]
        
        box = layout.box()
        box.label(text=f"Volume: {item.name}", icon='VOLUME_DATA')
        col = box.column(align=True)
        col.prop(item, "volume_object", text="Object")
        col.prop(item, "grid_name", text="Grid")
        col.prop(item, "colormap", text="Colormap")

        box = layout.box()
        box.label(text="Range & Density", icon='SEQ_LUMA_WAVEFORM')
        row = box.row(align=True)
        row.prop(item, "auto_range")
        row.operator("filters.volume_compute_range", text="Compute Range", icon='IPO_CONSTANT')
        col = box.column(align=True)
        col.prop(item, "from_min")
        col.prop(item, "from_max")
        
        box2 = layout.box()
        box2.label(text="Density/Alpha", icon='MOD_OPACITY')
        col2 = box2.column(align=True)
        col2.prop(item, "alpha_baseline")
        col2.prop(item, "alpha_multiplier")
        row2 = col2.row(align=True)
        row2.prop(item, "clip_min")
        row2.prop(item, "clip_max")
        
        box_render = layout.box()
        box_render.label(text="Volume Rendering", icon='SHADING_RENDERED')
        col_render = box_render.column(align=True)
        col_render.prop(item, "opacity_unit_distance")
        col_render.prop(item, "step_size")

        box3 = layout.box()
        box3.label(text="Vector Component", icon='ORIENTATION_GIMBAL')
        col3 = box3.column(align=True)
        col3.prop(item, "component_mode", text="Component")
        
        col.prop(item, "anisotropy")
        col.prop(item, "emission_strength")

        row = layout.row(align=True)
        row.operator("filters.volume_update_material", text="Update Material", icon='FILE_REFRESH')
        row.operator("filters.volume_regenerate_material", text="Regenerate", icon='SHADERFX')


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


class FILTERSGENERATOR_PT_attribute_interpolation(bpy.types.Panel):
    bl_label = "Attribute Smoothing"
    bl_idname = "FILTERSGENERATOR_PT_attribute_interpolation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'FILTERSGENERATOR_PT_main_panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        s = getattr(context.scene, "filters_interpolation_settings", None)
        if not s:
            layout.label(text="Smoothing settings unavailable", icon='ERROR')
            return

        layout.prop(s, "target_collection", text="Collection")
        
        # Show mesh count in collection
        coll_name = getattr(s, 'target_collection', '')
        if coll_name:
            coll = bpy.data.collections.get(coll_name)
            if coll:
                mesh_count = sum(1 for obj in coll.objects if obj.type == 'MESH')
                layout.label(text=f"{mesh_count} mesh(es) in collection", icon='OUTLINER_OB_MESH')
        
        row = layout.row(align=True)
        row.prop(s, "source_attribute", text="Source")
        row.operator("filters.compute_attribute_range", text="", icon='SEQ_HISTOGRAM')
        
        layout.prop(s, "method", text="Method")

        box = layout.box()
        box.label(text="Parameters", icon='PREFERENCES')
        col = box.column(align=True)
        
        method = getattr(s, 'method', 'IDW')
        
        # IDW parameters
        if method == 'IDW':
            col.prop(s, "k_neighbors")
            col.prop(s, "idw_power")
            col.prop(s, "include_self")
        
        # Gaussian parameters
        elif method == 'GAUSSIAN':
            col.prop(s, "k_neighbors")
            col.prop(s, "gaussian_sigma")
        
        # Laplacian parameters
        elif method == 'LAPLACIAN':
            col.prop(s, "laplacian_iterations")
            col.prop(s, "laplacian_factor")
        
        # Nearest neighbor parameters
        elif method == 'NEAREST':
            col.prop(s, "k_neighbors", text="K-th Neighbor")
        
        # Shepard (VTK) parameters
        elif method == 'SHEPARD':
            col.prop(s, "shepard_power")
            col.prop(s, "shepard_resolution")

        layout.separator()
        layout.prop(s, "output_name", text="Output Name")
        layout.operator("filters.apply_interpolation", text="Apply Smoothing", icon='MOD_SMOOTH')


class FILTERSGENERATOR_PT_collection_modifiers(bpy.types.Panel):
    bl_label = "Collection Modifiers"
    bl_idname = "FILTERSGENERATOR_PT_collection_modifiers"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'FILTERSGENERATOR_PT_main_panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        settings = getattr(context.scene, "filters_modifier_settings", None)
        if not settings:
            layout.label(text="Modifier settings unavailable", icon='ERROR')
            return

        # Target collection selector
        layout.prop(settings, "target_collection", text="Collection")
        
        # Show mesh count in collection
        coll_name = getattr(settings, 'target_collection', '')
        if coll_name:
            coll = bpy.data.collections.get(coll_name)
            if coll:
                mesh_count = sum(1 for obj in coll.all_objects if obj.type == 'MESH')
                layout.label(text=f"{mesh_count} mesh(es) in collection", icon='OUTLINER_OB_MESH')
        
        # Modifiers list (inspired by Volume Filter)
        box = layout.box()
        box.label(text="Modifiers Stack", icon='MODIFIER')
        row = box.row()
        row.template_list(
            "FILTERS_UL_modifier_list",
            "",
            settings,
            "modifier_items",
            settings,
            "modifier_items_index",
            rows=4
        )
        
        col = row.column(align=True)
        col.operator("filters.modifier_item_add", text="", icon='ADD')
        col.operator("filters.modifier_item_remove", text="", icon='REMOVE')
        col.separator()
        col.operator("filters.modifier_item_move_up", text="", icon='TRIA_UP')
        col.operator("filters.modifier_item_move_down", text="", icon='TRIA_DOWN')
        col.separator()
        col.operator("filters.modifier_item_duplicate", text="", icon='DUPLICATE')
        
        if not settings.modifier_items:
            layout.label(text="Add modifiers to the stack", icon='INFO')
            return
        
        if settings.modifier_items_index >= len(settings.modifier_items):
            return
        
        item = settings.modifier_items[settings.modifier_items_index]
        
        # Modifier settings box
        box = layout.box()
        box.label(text=f"Settings: {item.name}", icon='PREFERENCES')
        col = box.column(align=True)
        col.prop(item, "modifier_type", text="Type")
        col.prop(item, "name", text="Name")
        
        # Dynamic settings based on modifier type
        settings_box = layout.box()
        mod_type = item.modifier_type
        
        if mod_type == 'SUBSURF':
            settings_box.label(text="Subdivision Surface", icon='MOD_SUBSURF')
            col = settings_box.column(align=True)
            col.prop(item, "subsurf_levels", text="Viewport Levels")
            col.prop(item, "subsurf_render_levels", text="Render Levels")
            col.prop(item, "subsurf_uv_smooth", text="UV Smooth")
            
        elif mod_type == 'SMOOTH':
            settings_box.label(text="Smooth", icon='MOD_SMOOTH')
            col = settings_box.column(align=True)
            col.prop(item, "smooth_factor")
            col.prop(item, "smooth_iterations")
            
        elif mod_type == 'LAPLACIANSMOOTH':
            settings_box.label(text="Laplacian Smooth", icon='MOD_SMOOTH')
            col = settings_box.column(align=True)
            col.prop(item, "laplacian_iterations")
            col.prop(item, "laplacian_lambda")
            col.prop(item, "laplacian_lambda_border")
            col.prop(item, "laplacian_use_volume_preserve")
            col.prop(item, "laplacian_use_normalized")
            
        elif mod_type == 'CORRECTIVE_SMOOTH':
            settings_box.label(text="Corrective Smooth", icon='MOD_SMOOTH')
            col = settings_box.column(align=True)
            col.prop(item, "corrective_factor")
            col.prop(item, "corrective_iterations")
            col.prop(item, "corrective_smooth_type")
            col.prop(item, "corrective_use_only_smooth")
            col.prop(item, "corrective_use_pin_boundary")
            
        elif mod_type == 'DECIMATE':
            settings_box.label(text="Decimate", icon='MOD_DECIM')
            col = settings_box.column(align=True)
            col.prop(item, "decimate_mode")
            if item.decimate_mode == 'COLLAPSE':
                col.prop(item, "decimate_ratio")
                col.prop(item, "decimate_use_symmetry")
            elif item.decimate_mode == 'DISSOLVE':
                col.prop(item, "decimate_angle_limit")
                
        elif mod_type == 'REMESH':
            settings_box.label(text="Remesh", icon='MOD_REMESH')
            col = settings_box.column(align=True)
            col.prop(item, "remesh_mode")
            if item.remesh_mode == 'VOXEL':
                col.prop(item, "remesh_voxel_size")
            else:
                col.prop(item, "remesh_octree_depth")
                col.prop(item, "remesh_scale")
            col.prop(item, "remesh_use_smooth_shade")
            col.prop(item, "remesh_use_remove_disconnected")
                
        elif mod_type == 'SOLIDIFY':
            settings_box.label(text="Solidify", icon='MOD_SOLIDIFY')
            col = settings_box.column(align=True)
            col.prop(item, "solidify_thickness")
            col.prop(item, "solidify_offset")
            col.prop(item, "solidify_use_even_offset")
            col.prop(item, "solidify_use_rim")
            col.prop(item, "solidify_use_rim_only")
            
        elif mod_type == 'WIREFRAME':
            settings_box.label(text="Wireframe", icon='MOD_WIREFRAME')
            col = settings_box.column(align=True)
            col.prop(item, "wireframe_thickness")
            col.prop(item, "wireframe_use_replace")
            col.prop(item, "wireframe_use_even_offset")
            col.prop(item, "wireframe_use_relative_offset")
            col.prop(item, "wireframe_use_boundary")
            
        elif mod_type == 'TRIANGULATE':
            settings_box.label(text="Triangulate", icon='MOD_TRIANGULATE')
            col = settings_box.column(align=True)
            col.prop(item, "triangulate_quad_method")
            col.prop(item, "triangulate_ngon_method")
            col.prop(item, "triangulate_min_vertices")
            col.prop(item, "triangulate_keep_custom_normals")
            
        elif mod_type == 'WELD':
            settings_box.label(text="Weld", icon='AUTOMERGE_ON')
            col = settings_box.column(align=True)
            col.prop(item, "weld_threshold")
            col.prop(item, "weld_mode")
            
        elif mod_type == 'WEIGHTED_NORMAL':
            settings_box.label(text="Weighted Normal", icon='MOD_NORMALEDIT')
            col = settings_box.column(align=True)
            col.prop(item, "weighted_normal_mode")
            col.prop(item, "weighted_normal_weight")
            col.prop(item, "weighted_normal_thresh")
            col.prop(item, "weighted_normal_keep_sharp")
            col.prop(item, "weighted_normal_face_influence")
            
        elif mod_type == 'EDGE_SPLIT':
            settings_box.label(text="Edge Split", icon='MOD_EDGESPLIT')
            col = settings_box.column(align=True)
            col.prop(item, "edge_split_angle")
            col.prop(item, "edge_split_use_edge_angle")
            col.prop(item, "edge_split_use_edge_sharp")
        
        # Action buttons
        layout.separator()
        row = layout.row(align=True)
        row.operator("filters.apply_collection_modifiers", text="Apply to Collection", icon='CHECKMARK')
        row.operator("filters.remove_collection_modifiers", text="Remove All", icon='X')