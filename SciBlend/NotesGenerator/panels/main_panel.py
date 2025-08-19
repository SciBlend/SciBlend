import bpy

class NOTESGENERATOR_PT_main_panel(bpy.types.Panel):
    bl_label = "Notes Generator"
    bl_idname = "NOTESGENERATOR_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Notes Generator'

    def draw(self, context):
        layout = self.layout
        props = context.scene.annotation_properties

        # Add Annotation
        box = layout.box()
        box.label(text="Add Annotation", icon='GREASEPENCIL')
        box.operator("notesgenerator.add_annotation", text="Add", icon='ADD')

        # Annotation Properties
        box = layout.box()
        box.label(text="Annotation Properties", icon='PROPERTIES')
        box.prop(props, "annotation_scale")
        box.prop(props, "annotation_text")
        box.prop(props, "annotation_length")
        box.prop(props, "annotation_thickness")
        box.prop(props, "text_size")
        box.prop(props, "text_distance")
        box.prop(props, "annotation_color")
        box.prop(props, "emission_strength")

def register():
    bpy.utils.register_class(NOTESGENERATOR_PT_main_panel)

def unregister():
    bpy.utils.unregister_class(NOTESGENERATOR_PT_main_panel)

if __name__ == "__main__":
    register()