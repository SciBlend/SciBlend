from bpy.types import UIList

class COLOR_UL_Values_List(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'COLOR'
        split = layout.split(factor=0.3)
        split.prop(item, "value", text="", emboss=False, icon=custom_icon)
        split.prop(item, "color", text="")