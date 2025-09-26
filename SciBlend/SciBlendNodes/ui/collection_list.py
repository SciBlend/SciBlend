import bpy
from bpy.types import UIList


class SCIBLENDNODES_UL_collection_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            coll = bpy.data.collections.get(item.name)
            if coll:
                row.label(text=item.name, icon='OUTLINER_COLLECTION')
            else:
                row.label(text=item.name, icon='ERROR')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='OUTLINER_COLLECTION') 