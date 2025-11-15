import bpy
from bpy.types import UIList


class FILTERS_UL_volume_list(UIList):
    """
    UIList for displaying and managing multiple volume objects.
    """
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            vol_obj = item.volume_object
            if vol_obj and vol_obj.type == 'VOLUME':
                row.label(text=item.name, icon='VOLUME_DATA')
                if item.grid_name:
                    row.label(text=f"({item.grid_name})", icon='DOT')
            else:
                row.label(text=item.name, icon='ERROR')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='VOLUME_DATA')


def register():
    bpy.utils.register_class(FILTERS_UL_volume_list)


def unregister():
    bpy.utils.unregister_class(FILTERS_UL_volume_list)

