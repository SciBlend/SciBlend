import bpy
from bpy.types import UIList


class SHADER_UL_collection_list(UIList):
    """UIList to display collections with shader status indicators."""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        """Draw a single collection item in the list.
        
        Parameters
        ----------
        context : bpy.types.Context
            Blender context.
        layout : bpy.types.UILayout
            Layout to draw into.
        data : PropertyGroup
            The data containing the collection.
        item : CollectionShaderItem
            The collection shader item to draw.
        icon : int
            Icon identifier.
        active_data : PropertyGroup
            The data containing the active index.
        active_propname : str
            Name of the active property.
        """
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            
            coll = bpy.data.collections.get(item.collection_name)
            if coll:
                mat = None
                if item.material_name:
                    mat = bpy.data.materials.get(item.material_name)
                    
                if mat and item.is_shader_generator:
                    row.label(text=item.collection_name, icon='MATERIAL')
                else:
                    row.label(text=item.collection_name, icon='OUTLINER_COLLECTION')
            else:
                row.label(text=item.collection_name, icon='ERROR')
                
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='OUTLINER_COLLECTION')

