import bpy
from bpy.types import UIList


# Mapping of modifier types to icons
MODIFIER_ICONS = {
    'SUBSURF': 'MOD_SUBSURF',
    'SMOOTH': 'MOD_SMOOTH',
    'LAPLACIANSMOOTH': 'MOD_SMOOTH',
    'CORRECTIVE_SMOOTH': 'MOD_SMOOTH',
    'DECIMATE': 'MOD_DECIM',
    'REMESH': 'MOD_REMESH',
    'SOLIDIFY': 'MOD_SOLIDIFY',
    'WIREFRAME': 'MOD_WIREFRAME',
    'TRIANGULATE': 'MOD_TRIANGULATE',
    'WELD': 'AUTOMERGE_ON',
    'WEIGHTED_NORMAL': 'MOD_NORMALEDIT',
    'EDGE_SPLIT': 'MOD_EDGESPLIT',
}


class FILTERS_UL_modifier_list(UIList):
    """UIList for displaying and managing collection modifiers."""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            
            # Enable/disable toggle
            row.prop(
                item, "enabled", text="",
                icon='CHECKBOX_HLT' if item.enabled else 'CHECKBOX_DEHLT',
                emboss=False
            )
            
            # Modifier icon and name
            mod_icon = MODIFIER_ICONS.get(item.modifier_type, 'MODIFIER')
            
            if item.enabled:
                row.label(text=item.name, icon=mod_icon)
            else:
                # Grayed out appearance for disabled items
                sub = row.row()
                sub.active = False
                sub.label(text=item.name, icon=mod_icon)
            
            # Show modifier type abbreviation
            type_labels = {
                'SUBSURF': 'Sub',
                'SMOOTH': 'Smo',
                'LAPLACIANSMOOTH': 'Lap',
                'CORRECTIVE_SMOOTH': 'Cor',
                'DECIMATE': 'Dec',
                'REMESH': 'Rem',
                'SOLIDIFY': 'Sol',
                'WIREFRAME': 'Wir',
                'TRIANGULATE': 'Tri',
                'WELD': 'Wld',
                'WEIGHTED_NORMAL': 'WN',
                'EDGE_SPLIT': 'ES',
            }
            type_label = type_labels.get(item.modifier_type, '?')
            row.label(text=f"[{type_label}]")
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            mod_icon = MODIFIER_ICONS.get(item.modifier_type, 'MODIFIER')
            layout.label(text="", icon=mod_icon)


def register():
    bpy.utils.register_class(FILTERS_UL_modifier_list)


def unregister():
    bpy.utils.unregister_class(FILTERS_UL_modifier_list)


