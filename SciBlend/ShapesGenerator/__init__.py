import bpy
from bpy.props import IntProperty, StringProperty, EnumProperty, CollectionProperty, FloatProperty, BoolProperty, FloatVectorProperty, PointerProperty
from bpy.types import PropertyGroup, Operator, UIList, Panel

from .operators.png_overlay import SHAPESGENERATOR_OT_UpdateShapes, SHAPESGENERATOR_OT_NewShape, SHAPESGENERATOR_OT_DeleteShape
from .ui.png_overlay_panel import SHAPESGENERATOR_PT_Panel, SHAPESGENERATOR_UL_List
from .operators.custom_shape_importer import SHAPESGENERATOR_OT_ImportCustomShape

def update_shape(self, context):
    try:
        bpy.ops.shapesgenerator.update_shapes()
    except Exception as e:
        print(f"Error updating shapes: {str(e)}")

def update_linked_dimension(self, context):
    if self.link_dimensions:
        if self.get("_updating"):
            return
        self["_updating"] = True
        if self.get("_last_updated") == "x":
            aspect_ratio = self.dimension_x / self.get("_original_x", self.dimension_x)
            self.dimension_y = int(self.get("_original_y", self.dimension_y) * aspect_ratio)
        else:
            aspect_ratio = self.dimension_y / self.get("_original_y", self.dimension_y)
            self.dimension_x = int(self.get("_original_x", self.dimension_x) * aspect_ratio)
        self["_updating"] = False
    update_shape(self, context)

def update_dimension_x(self, context):
    if not self.get("_original_x"):
        self["_original_x"] = self.dimension_x
    self["_last_updated"] = "x"
    update_linked_dimension(self, context)

def update_dimension_y(self, context):
    if not self.get("_original_y"):
        self["_original_y"] = self.dimension_y
    self["_last_updated"] = "y"
    update_linked_dimension(self, context)

class ShapesGeneratorItem(PropertyGroup):
    name: StringProperty(default="Shape")
    shape_type: EnumProperty(
        name="Shape Type",
        items=[
            ('ARROW', "Arrow", "Arrow shape"),
            ('CIRCLE', "Circle", "Circle shape"),
            ('RECTANGLE', "Rectangle", "Rectangle shape"),
            ('FANCY_ARROW', "Fancy Arrow", "Fancy arrow shape"),
            ('ELLIPSE', "Ellipse", "Ellipse shape"),
            ('TEXT', "Text", "Text"),
            ('LATEX', "LaTeX", "LaTeX formula"),
            ('CUSTOM', "Custom", "Custom imported shape"),  # Nueva opción
        ],
        default='ARROW',
        update=update_shape
    )
    arrow_length: FloatProperty(name="Arrow Length", default=100.0, min=1.0, update=update_shape)
    arrow_width: FloatProperty(name="Arrow Width", default=50.0, min=1.0, update=update_shape)
    circle_radius: FloatProperty(name="Circle Radius", default=50.0, min=1.0, update=update_shape)
    rectangle_width: FloatProperty(name="Rectangle Width", default=100.0, min=1.0, update=update_shape)
    rectangle_height: FloatProperty(name="Rectangle Height", default=50.0, min=1.0, update=update_shape)
    ellipse_width: FloatProperty(name="Ellipse Width", default=100.0, min=1.0, update=update_shape)
    ellipse_height: FloatProperty(name="Ellipse Height", default=50.0, min=1.0, update=update_shape)
    star_outer_radius: FloatProperty(name="Star Outer Radius", default=50.0, min=1.0, update=update_shape)
    star_inner_radius: FloatProperty(name="Star Inner Radius", default=25.0, min=1.0, update=update_shape)
    star_points: IntProperty(name="Star Points", default=5, min=3, max=20, update=update_shape)
    fill_color: FloatVectorProperty(
        name="Fill Color",
        subtype='COLOR',
        default=(1.0, 0.0, 0.0, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        update=update_shape
    )
    fill_alpha: FloatProperty(
        name="Fill Opacity",
        default=1.0,
        min=0.0,
        max=1.0,
        update=update_shape
    )
    line_color: FloatVectorProperty(
        name="Line Color",
        subtype='COLOR',
        default=(0.0, 0.0, 0.0, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        update=update_shape
    )
    line_alpha: FloatProperty(
        name="Line Opacity",
        default=1.0,
        min=0.0,
        max=1.0,
        update=update_shape
    )
    line_width: FloatProperty(name="Line Width", default=2.0, min=0.0, update=update_shape)
    line_size: FloatProperty(
        name="Line Size",
        default=1.0,
        min=0.1,
        max=10.0,
        description="Size of the line for the shape",
        update=update_shape
    )
    position_x: FloatProperty(
        name="X Position",
        default=0.0,
        min=-2.0,  
        max=2.0,   
        description="Horizontal position of the shape",
        update=update_shape
    )
    position_y: FloatProperty(
        name="Y Position",
        default=0.0,
        min=-2.0,  
        max=2.0,  
        description="Vertical position of the shape",
        update=update_shape
    )
    rotation: FloatProperty(
        name="Rotation",
        default=0.0,
        min=-360.0,
        max=360.0,
        subtype='ANGLE',
        update=update_shape
    )
    dimension: FloatProperty(
        name="Dimension",
        default=100.0,
        min=1.0,
        update=update_shape
    )
    link_dimensions: BoolProperty(
        name="Link Dimensions",
        default=True,
        update=update_shape
    )

    text_content: StringProperty(
        name="Text Content",
        default="Sample Text",
        update=update_shape
    )
    font_size: IntProperty(
        name="Font Size",
        default=12,
        min=1,
        update=update_shape
    )
    font_path: StringProperty(
        name="Font Path",
        default="",
        subtype='FILE_PATH',
        update=update_shape
    )
    latex_formula: StringProperty(
        name="LaTeX Formula",
        default=r"$E = mc^2$",
        update=update_shape
    )

    font_color: FloatVectorProperty(
        name="Font Color",
        subtype='COLOR',
        default=(0.0, 0.0, 0.0, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        update=update_shape
    )

    dimension_x: IntProperty(
        name="Width",
        description="Width of the shape in pixels",
        default=100,
        min=1,
        update=update_dimension_x
    )
    dimension_y: IntProperty(
        name="Height",
        description="Height of the shape in pixels",
        default=100,
        min=1,
        update=update_dimension_y
    )
    link_dimensions: BoolProperty(
        name="Link Dimensions",
        default=True,
        update=update_shape
    )

    custom_shape_path: StringProperty(
        name="Custom Shape Path",
        default="",
        subtype='FILE_PATH',
        update=update_shape
    )

    scale_x: FloatProperty(
        name="Scale X",
        default=1.0,
        min=0.01,
        max=10.0,
        description="Scale X of the shape",
        update=update_shape
    )
    scale_y: FloatProperty(
        name="Scale Y",
        default=1.0,
        min=0.01,
        max=10.0,
        description="Scale Y of the shape",
        update=update_shape
    )

classes = (
    ShapesGeneratorItem,
    SHAPESGENERATOR_OT_UpdateShapes,
    SHAPESGENERATOR_OT_NewShape,
    SHAPESGENERATOR_OT_DeleteShape,
    SHAPESGENERATOR_UL_List,
    SHAPESGENERATOR_PT_Panel,
    SHAPESGENERATOR_OT_ImportCustomShape,  
)

def register():
    if hasattr(bpy.types.Scene, "shapesgenerator_shapes"):
        print("Warning: 'shapesgenerator_shapes' already exists. Shapes Generator may not work correctly.")
    else:
        for cls in classes:
            try:
                bpy.utils.register_class(cls)
            except ValueError:
                bpy.utils.unregister_class(cls)
                bpy.utils.register_class(cls)

        bpy.types.Scene.shapesgenerator_shapes = CollectionProperty(type=ShapesGeneratorItem)
        bpy.types.Scene.shapesgenerator_active_shape_index = IntProperty()

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

    del bpy.types.Scene.shapesgenerator_shapes
    del bpy.types.Scene.shapesgenerator_active_shape_index

if __name__ == "__main__":
    register()
