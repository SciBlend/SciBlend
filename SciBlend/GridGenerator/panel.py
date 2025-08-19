import bpy

class OBJECT_PT_GridGeneratorPanel(bpy.types.Panel):
    bl_label = "Grid Generator"
    bl_idname = "OBJECT_PT_grid_generator_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Grid Generator'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        grid_settings = scene.grid_settings

        # Grid Type
        box = layout.box()
        box.label(text="Grid Type", icon='MESH_CUBE')
        box.prop(grid_settings, "grid_type", text="Type")

        # Grid Settings
        box = layout.box()
        box.label(text="Grid Settings", icon='GRID')
        box.prop(grid_settings, "unit_measure", text="Unit of Measure")
        box.prop(grid_settings, "distance_x", text="Distance X")
        box.prop(grid_settings, "distance_y", text="Distance Y")
        box.prop(grid_settings, "distance_z", text="Distance Z")
        box.prop(grid_settings, "subdivisions", text="Subdivisions")

        # Nuevas opciones para el grid 2D
        if grid_settings.grid_type == '2D_GRID':
            box.prop(grid_settings, "grid_2d_orientation", text="2D Grid Orientation")
            box.prop(grid_settings, "length_axis_2d", text="2D Toggle Axis")

        layout.separator()

        # Number Settings
        box = layout.box()
        box.label(text="Number Settings", icon='FONT_DATA')
        box.prop(grid_settings, "show_numbers", text="Show Numbers")
        box.prop(grid_settings, "text_size", text="Text Size")
        box.prop(grid_settings, "use_custom_font", text="Custom Font")
        if grid_settings.use_custom_font:
            box.prop(grid_settings, "custom_font", text="Font File")

        layout.separator()

        # Edge Settings
        box = layout.box()
        box.label(text="Edge Settings", icon='MOD_WIREFRAME')
        box.prop(grid_settings, "edge_size", text="Edge Thickness")

        layout.separator()

        # Emissive Material Settings
        box = layout.box()
        box.label(text="Emissive Material", icon='MATERIAL')
        box.prop(grid_settings, "emission_color", text="Emission Color")
        box.prop(grid_settings, "emission_strength", text="Emission Strength")

        layout.separator()

        # Scene Resizing
        box = layout.box()
        box.label(text="Scene Resizing", icon='FULLSCREEN_ENTER')
        box.prop(grid_settings, "unit_scale", text="Unit Scale")
        box.prop(grid_settings, "target_unit_measure", text="New Unit Measure")

        layout.separator()

        # Text Offset Settings
        box = layout.box()
        box.label(text="Text Offset Settings", icon='ALIGN_LEFT')
        
        for axis in ['X', 'Y', 'Z']:
            box.label(text=f"{axis} Axis Text Settings:")
            row = box.row(align=True)
            row.prop(grid_settings, f"text_offset_{axis.lower()}", text="Offset")
            row.prop(grid_settings, f"text_direction_{axis.lower()}", text="")

        layout.separator()

        # Operations
        box = layout.box()
        box.label(text="Operations", icon='TOOL_SETTINGS')
        row = box.row(align=True)
        row.operator("object.generate_nodes",
                     text="Generate Nodes", icon='NODETREE')
        row.operator("object.create_edges", text="Create Edges",
                     icon='OUTLINER_OB_CURVE')

        row = box.row(align=True)
        row.operator("object.apply_emissive_material",
                     text="Apply Emissive Material", icon='MATERIAL')
        row.operator("object.resize_scene", text="Resize Scene",
                     icon='ARROW_LEFTRIGHT')

        row = box.row(align=True)
        row.operator("object.update_text_size",
                     text="Update Text Size", icon='FONT_DATA')
        row.operator("object.update_edge_size",
                     text="Update Edge Size", icon='MOD_WIREFRAME')