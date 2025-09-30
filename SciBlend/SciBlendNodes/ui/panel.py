import bpy
from bpy.types import Panel


class SCIBLENDNODES_PT_panel(Panel):
    bl_idname = "SCIBLENDNODES_PT_panel"
    bl_label = "SciBlend Nodes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SciBlend'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """Draw SciBlend Nodes UI: collections list, presets list, and per-preset settings below the lists."""
        layout = self.layout
        scene = context.scene
        settings = getattr(scene, 'sciblend_nodes_settings', None)
        if not settings:
            layout.label(text="SciBlend Nodes not available", icon='INFO')
            return

        if len(settings.collections_list) == 0:
            try:
                from ..properties.settings import _rebuild_collections_list
                _rebuild_collections_list(settings)
            except Exception:
                pass

        box = layout.box()
        box.label(text="Collections", icon='OUTLINER_COLLECTION')
        row = box.row(align=True)
        row.prop(settings, "search_filter", text="Search")
        row = box.row()
        row.template_list("SCIBLENDNODES_UL_collection_list", "", settings, "collections_list", settings, "collections_list_index", rows=5)

        if settings.collections_list and 0 <= settings.collections_list_index < len(settings.collections_list):
            coll_name = settings.collections_list[settings.collections_list_index].name
            try:
                settings.target_collection = coll_name
            except Exception:
                pass
            row_actions = box.row(align=True)
            row_actions.prop(settings, "rename_collection_name", text="New Name")
            row_actions.operator("sciblend_nodes.rename_collection", text="Rename", icon='OUTLINER_COLLECTION')
            row_actions.operator("sciblend_nodes.clear_collection_geo_nodes", text="Remove Geo Nodes", icon='TRASH')

            layout.separator()
            box = layout.box()
            box.label(text=f"Presets for '{coll_name}'", icon='NODETREE')
            row = box.row()
            row.template_list("SCIBLENDNODES_UL_preset_list", "", settings, "presets", settings, "presets_index", rows=5)
            col = row.column(align=True)
            add = col.operator("sciblend_nodes.preset_add", icon='ADD', text="")
            add.collection_name = coll_name
            col.operator("sciblend_nodes.preset_remove", icon='REMOVE', text="")

            if settings.presets and 0 <= settings.presets_index < len(settings.presets):
                item = settings.presets[settings.presets_index]
                settings_box = layout.box()
                settings_box.label(text="Preset Settings", icon='PREFERENCES')
                row = settings_box.row(align=True)
                row.prop(item, 'preset', text="Type")

                if item.preset == 'POINTS_SHADER':
                    settings_box.prop(item, 'points_radius', text="Point Size")
                    settings_box.prop(item, 'material_override', text="Material Override")
                elif item.preset == 'DISPLACE_NORMAL':
                    settings_box.prop(item, 'attribute_name', text="Attribute")
                    settings_box.prop(item, 'scale', text="Scale")
                elif item.preset == 'VECTOR_GLYPHS':
                    settings_box.prop(item, 'vector_attribute_name', text="Vector Attribute")
                    settings_box.prop(item, 'scale_attribute_name', text="Scale Attribute")
                    settings_box.prop(item, 'scale', text="Scale")
                    settings_box.prop(item, 'glyph_density', text="Density")
                    settings_box.prop(item, 'glyph_max_count', text="Max Glyphs")
                    settings_box.prop(item, 'glyph_primitive', text="Primitive")
                    if item.glyph_primitive == 'CONE':
                        col = settings_box.column(align=True)
                        col.prop(item, 'cone_vertices')
                        col.prop(item, 'cone_radius_top')
                        col.prop(item, 'cone_radius_bottom')
                        col.prop(item, 'cone_depth')
                    elif item.glyph_primitive == 'CYLINDER':
                        col = settings_box.column(align=True)
                        col.prop(item, 'cyl_vertices')
                        col.prop(item, 'cyl_radius')
                        col.prop(item, 'cyl_depth')
                    else:
                        col = settings_box.column(align=True)
                        col.prop(item, 'sphere_segments')
                        col.prop(item, 'sphere_rings')
                        col.prop(item, 'sphere_radius')

                action_row = settings_box.row(align=True)
                apply_op = action_row.operator("sciblend_nodes.preset_apply_selected", text="Apply Selected Preset", icon='CHECKMARK')
                apply_op.index = settings.presets_index