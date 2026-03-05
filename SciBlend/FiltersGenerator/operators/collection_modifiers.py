import bpy
from bpy.types import Operator


class FILTERS_OT_modifier_item_add(Operator):
    """Add a new modifier to the collection modifiers stack."""
    bl_idname = "filters.modifier_item_add"
    bl_label = "Add Modifier"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        settings = context.scene.filters_modifier_settings
        item = settings.modifier_items.add()
        
        count = len(settings.modifier_items)
        item.name = f"Modifier {count}"
        
        settings.modifier_items_index = len(settings.modifier_items) - 1
        
        return {'FINISHED'}


class FILTERS_OT_modifier_item_remove(Operator):
    """Remove the active modifier from the stack."""
    bl_idname = "filters.modifier_item_remove"
    bl_label = "Remove Modifier"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, 'filters_modifier_settings', None)
        return settings and len(settings.modifier_items) > 0
    
    def execute(self, context):
        settings = context.scene.filters_modifier_settings
        idx = settings.modifier_items_index
        
        if 0 <= idx < len(settings.modifier_items):
            settings.modifier_items.remove(idx)
            
            if settings.modifier_items_index >= len(settings.modifier_items):
                settings.modifier_items_index = max(0, len(settings.modifier_items) - 1)
        
        return {'FINISHED'}


class FILTERS_OT_modifier_item_move_up(Operator):
    """Move the active modifier up in the stack."""
    bl_idname = "filters.modifier_item_move_up"
    bl_label = "Move Modifier Up"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, 'filters_modifier_settings', None)
        return settings and settings.modifier_items_index > 0
    
    def execute(self, context):
        settings = context.scene.filters_modifier_settings
        idx = settings.modifier_items_index
        
        settings.modifier_items.move(idx, idx - 1)
        settings.modifier_items_index = idx - 1
        
        return {'FINISHED'}


class FILTERS_OT_modifier_item_move_down(Operator):
    """Move the active modifier down in the stack."""
    bl_idname = "filters.modifier_item_move_down"
    bl_label = "Move Modifier Down"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, 'filters_modifier_settings', None)
        return settings and settings.modifier_items_index < len(settings.modifier_items) - 1
    
    def execute(self, context):
        settings = context.scene.filters_modifier_settings
        idx = settings.modifier_items_index
        
        settings.modifier_items.move(idx, idx + 1)
        settings.modifier_items_index = idx + 1
        
        return {'FINISHED'}


class FILTERS_OT_apply_collection_modifiers(Operator):
    """Apply all enabled modifiers to every mesh in the target collection."""
    bl_idname = "filters.apply_collection_modifiers"
    bl_label = "Apply Collection Modifiers"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, 'filters_modifier_settings', None)
        return settings and settings.target_collection and len(settings.modifier_items) > 0
    
    def execute(self, context):
        settings = context.scene.filters_modifier_settings
        coll_name = settings.target_collection
        
        if not coll_name:
            self.report({'ERROR'}, "Select a collection first")
            return {'CANCELLED'}
        
        coll = bpy.data.collections.get(coll_name)
        if not coll:
            self.report({'ERROR'}, f"Collection not found: {coll_name}")
            return {'CANCELLED'}
        
        # Get all mesh objects in collection (including nested)
        mesh_objects = [obj for obj in coll.all_objects if obj.type == 'MESH']
        if not mesh_objects:
            self.report({'WARNING'}, f"No mesh objects found in collection '{coll_name}'")
            return {'CANCELLED'}
        
        enabled_items = [item for item in settings.modifier_items if item.enabled]
        if not enabled_items:
            self.report({'WARNING'}, "No enabled modifiers to apply")
            return {'CANCELLED'}
        
        applied_count = 0
        errors = []
        
        for obj in mesh_objects:
            for item in enabled_items:
                try:
                    mod = self._ensure_modifier(obj, item)
                    if mod:
                        self._configure_modifier(mod, item)
                        applied_count += 1
                except Exception as e:
                    errors.append(f"{obj.name}/{item.name}: {e}")
        
        if errors:
            print(f"[FiltersGenerator] Modifier application errors:")
            for err in errors:
                print(f"  - {err}")
        
        self.report({'INFO'}, f"Applied {len(enabled_items)} modifier(s) to {len(mesh_objects)} mesh(es)")
        return {'FINISHED'}
    
    def _ensure_modifier(self, obj, item):
        """Create or find existing modifier with SciBlend tag."""
        tag_name = f"sciblend_mod_{item.name}"
        mod_name = f"SciBlend_{item.name}"
        
        # Check for existing modifier with our tag or matching name
        for mod in obj.modifiers:
            # Try to check custom property, fall back to name matching
            try:
                if mod.get('sciblend_collection_mod') == tag_name:
                    # If type changed, remove and recreate
                    if mod.type != item.modifier_type:
                        obj.modifiers.remove(mod)
                        break
                    return mod
            except TypeError:
                # Modifier doesn't support IDProperties, check by name
                if mod.name == mod_name or mod.name.startswith(mod_name):
                    if mod.type != item.modifier_type:
                        obj.modifiers.remove(mod)
                        break
                    return mod
        
        # Create new modifier
        try:
            mod = obj.modifiers.new(name=mod_name, type=item.modifier_type)
            # Try to set custom property for tracking
            try:
                mod['sciblend_collection_mod'] = tag_name
            except TypeError:
                # Some modifiers don't support IDProperties, that's ok
                pass
            return mod
        except Exception as e:
            print(f"[FiltersGenerator] Error creating modifier {item.modifier_type} on {obj.name}: {e}")
            return None
    
    def _configure_modifier(self, mod, item):
        """Configure modifier settings from item properties."""
        mod_type = item.modifier_type
        
        if mod_type == 'SUBSURF':
            mod.levels = item.subsurf_levels
            mod.render_levels = item.subsurf_render_levels
            mod.uv_smooth = item.subsurf_uv_smooth
            
        elif mod_type == 'SMOOTH':
            mod.factor = item.smooth_factor
            mod.iterations = item.smooth_iterations
            
        elif mod_type == 'LAPLACIANSMOOTH':
            mod.iterations = item.laplacian_iterations
            mod.lambda_factor = item.laplacian_lambda
            mod.lambda_border = item.laplacian_lambda_border
            mod.use_volume_preserve = item.laplacian_use_volume_preserve
            mod.use_normalized = item.laplacian_use_normalized
            
        elif mod_type == 'CORRECTIVE_SMOOTH':
            mod.factor = item.corrective_factor
            mod.iterations = item.corrective_iterations
            mod.smooth_type = item.corrective_smooth_type
            mod.use_only_smooth = item.corrective_use_only_smooth
            mod.use_pin_boundary = item.corrective_use_pin_boundary
            
        elif mod_type == 'DECIMATE':
            mod.decimate_type = item.decimate_mode
            if item.decimate_mode == 'COLLAPSE':
                mod.ratio = item.decimate_ratio
                mod.use_symmetry = item.decimate_use_symmetry
            elif item.decimate_mode == 'DISSOLVE':
                mod.angle_limit = item.decimate_angle_limit
                
        elif mod_type == 'REMESH':
            mod.mode = item.remesh_mode
            if item.remesh_mode == 'VOXEL':
                mod.voxel_size = item.remesh_voxel_size
            else:
                mod.octree_depth = item.remesh_octree_depth
                mod.scale = item.remesh_scale
            mod.use_smooth_shade = item.remesh_use_smooth_shade
            mod.use_remove_disconnected = item.remesh_use_remove_disconnected
            
        elif mod_type == 'SOLIDIFY':
            mod.thickness = item.solidify_thickness
            mod.offset = item.solidify_offset
            mod.use_even_offset = item.solidify_use_even_offset
            mod.use_rim = item.solidify_use_rim
            mod.use_rim_only = item.solidify_use_rim_only
            
        elif mod_type == 'WIREFRAME':
            mod.thickness = item.wireframe_thickness
            mod.use_replace = item.wireframe_use_replace
            mod.use_even_offset = item.wireframe_use_even_offset
            mod.use_relative_offset = item.wireframe_use_relative_offset
            mod.use_boundary = item.wireframe_use_boundary
            
        elif mod_type == 'TRIANGULATE':
            mod.quad_method = item.triangulate_quad_method
            mod.ngon_method = item.triangulate_ngon_method
            mod.min_vertices = item.triangulate_min_vertices
            mod.keep_custom_normals = item.triangulate_keep_custom_normals
            
        elif mod_type == 'WELD':
            mod.merge_threshold = item.weld_threshold
            mod.mode = item.weld_mode
            
        elif mod_type == 'WEIGHTED_NORMAL':
            mod.mode = item.weighted_normal_mode
            mod.weight = item.weighted_normal_weight
            mod.thresh = item.weighted_normal_thresh
            mod.keep_sharp = item.weighted_normal_keep_sharp
            mod.face_influence = item.weighted_normal_face_influence
            
        elif mod_type == 'EDGE_SPLIT':
            mod.split_angle = item.edge_split_angle
            mod.use_edge_angle = item.edge_split_use_edge_angle
            mod.use_edge_sharp = item.edge_split_use_edge_sharp


class FILTERS_OT_remove_collection_modifiers(Operator):
    """Remove all SciBlend collection modifiers from meshes in the target collection."""
    bl_idname = "filters.remove_collection_modifiers"
    bl_label = "Remove Collection Modifiers"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, 'filters_modifier_settings', None)
        return settings and settings.target_collection
    
    def execute(self, context):
        settings = context.scene.filters_modifier_settings
        coll_name = settings.target_collection
        
        if not coll_name:
            self.report({'ERROR'}, "Select a collection first")
            return {'CANCELLED'}
        
        coll = bpy.data.collections.get(coll_name)
        if not coll:
            self.report({'ERROR'}, f"Collection not found: {coll_name}")
            return {'CANCELLED'}
        
        removed_count = 0
        affected_meshes = 0
        
        for obj in coll.all_objects:
            if obj.type != 'MESH':
                continue
            
            had_any = False
            for mod in list(obj.modifiers):
                # Check if this is a SciBlend modifier by custom property or name
                is_sciblend_mod = False
                try:
                    if mod.get('sciblend_collection_mod'):
                        is_sciblend_mod = True
                except TypeError:
                    # Modifier doesn't support IDProperties, check by name prefix
                    if mod.name.startswith('SciBlend_'):
                        is_sciblend_mod = True
                
                if is_sciblend_mod:
                    try:
                        obj.modifiers.remove(mod)
                        removed_count += 1
                        had_any = True
                    except Exception as e:
                        print(f"[FiltersGenerator] Failed removing modifier '{mod.name}' on '{obj.name}': {e}")
            
            if had_any:
                affected_meshes += 1
        
        self.report({'INFO'}, f"Removed {removed_count} modifier(s) from {affected_meshes} mesh(es)")
        return {'FINISHED'}


class FILTERS_OT_update_collection_modifiers(Operator):
    """Update existing SciBlend modifiers with current settings."""
    bl_idname = "filters.update_collection_modifiers"
    bl_label = "Update Modifiers"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, 'filters_modifier_settings', None)
        return settings and settings.target_collection and len(settings.modifier_items) > 0
    
    def execute(self, context):
        # Simply re-apply - the _ensure_modifier will find existing ones
        return bpy.ops.filters.apply_collection_modifiers()


class FILTERS_OT_modifier_item_duplicate(Operator):
    """Duplicate the active modifier item."""
    bl_idname = "filters.modifier_item_duplicate"
    bl_label = "Duplicate Modifier"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, 'filters_modifier_settings', None)
        return settings and len(settings.modifier_items) > 0
    
    def execute(self, context):
        settings = context.scene.filters_modifier_settings
        idx = settings.modifier_items_index
        
        if not (0 <= idx < len(settings.modifier_items)):
            return {'CANCELLED'}
        
        source = settings.modifier_items[idx]
        new_item = settings.modifier_items.add()
        
        # Copy all properties
        for prop in source.bl_rna.properties:
            if not prop.is_readonly:
                try:
                    setattr(new_item, prop.identifier, getattr(source, prop.identifier))
                except Exception:
                    pass
        
        new_item.name = f"{source.name} Copy"
        settings.modifier_items_index = len(settings.modifier_items) - 1
        
        return {'FINISHED'}


def register():
    bpy.utils.register_class(FILTERS_OT_modifier_item_add)
    bpy.utils.register_class(FILTERS_OT_modifier_item_remove)
    bpy.utils.register_class(FILTERS_OT_modifier_item_move_up)
    bpy.utils.register_class(FILTERS_OT_modifier_item_move_down)
    bpy.utils.register_class(FILTERS_OT_apply_collection_modifiers)
    bpy.utils.register_class(FILTERS_OT_remove_collection_modifiers)
    bpy.utils.register_class(FILTERS_OT_update_collection_modifiers)
    bpy.utils.register_class(FILTERS_OT_modifier_item_duplicate)


def unregister():
    bpy.utils.unregister_class(FILTERS_OT_modifier_item_duplicate)
    bpy.utils.unregister_class(FILTERS_OT_update_collection_modifiers)
    bpy.utils.unregister_class(FILTERS_OT_remove_collection_modifiers)
    bpy.utils.unregister_class(FILTERS_OT_apply_collection_modifiers)
    bpy.utils.unregister_class(FILTERS_OT_modifier_item_move_down)
    bpy.utils.unregister_class(FILTERS_OT_modifier_item_move_up)
    bpy.utils.unregister_class(FILTERS_OT_modifier_item_remove)
    bpy.utils.unregister_class(FILTERS_OT_modifier_item_add)

