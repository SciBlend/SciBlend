import bpy
from bpy.types import UIList


class SCIBLENDNODES_UL_preset_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        """Render a single preset row with inline controls depending on preset type."""
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, 'preset', text="", emboss=False, icon='NODETREE')
            if item.preset == 'POINTS_SHADER':
                row.prop(item, 'points_radius', text="Size")
            elif item.preset == 'DISPLACE_NORMAL':
                row.prop(item, 'attribute_name', text="Attr")
                row.prop(item, 'scale', text="Scale")
            elif item.preset == 'VECTOR_GLYPHS':
                row.prop(item, 'vector_attribute_name', text="Vector")
                row.prop(item, 'scale', text="Scale")
            elif item.preset == 'POINTS_TO_VOLUME':
                row.prop(item, 'radius', text="R")
                row.prop(item, 'voxel_size', text="Vox")
                row.prop(item, 'threshold', text="Th")
            elif item.preset == 'SLICE_PLANE':
                row.prop(item, 'plane_point', text="Point")
                row.prop(item, 'plane_normal', text="Normal")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='NODETREE')

    def filter_items(self, context, data, propname):
        """Filter presets so only those tied to the selected collection are displayed."""
        items = getattr(data, propname, [])
        flags = [self.bitflag_filter_item] * len(items)
        try:
            settings = getattr(context.scene, 'sciblend_nodes_settings', None)
            selected = None
            if settings and getattr(settings, 'collections_list', None) and 0 <= int(getattr(settings, 'collections_list_index', -1)) < len(settings.collections_list):
                selected = settings.collections_list[settings.collections_list_index].name
            if not selected and settings:
                selected = getattr(settings, 'target_collection', '')
            if selected:
                for i, it in enumerate(items):
                    if getattr(it, 'collection_name', '') != selected:
                        flags[i] &= ~self.bitflag_filter_item
        except Exception:
            pass
        return flags, [] 