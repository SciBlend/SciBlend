import bpy
from .panel import OBJECT_PT_GridGeneratorPanel
from .operators.generate_nodes import GenerateNodesOperator
from .operators.create_edges import CreateEdgesOperator
from .operators.update_operators import (
    UpdateTextSizeOperator,
    UpdateEdgeSizeOperator,
    ApplyEmissiveMaterialOperator,
    ResizeSceneOperator
)
from .properties.grid_settings import GridSettings

def register():
    bpy.utils.register_class(OBJECT_PT_GridGeneratorPanel)
    bpy.utils.register_class(GenerateNodesOperator)
    bpy.utils.register_class(CreateEdgesOperator)
    bpy.utils.register_class(UpdateTextSizeOperator)
    bpy.utils.register_class(UpdateEdgeSizeOperator)
    bpy.utils.register_class(ApplyEmissiveMaterialOperator)
    bpy.utils.register_class(ResizeSceneOperator)
    bpy.utils.register_class(GridSettings)
    bpy.types.Scene.grid_settings = bpy.props.PointerProperty(
        type=GridSettings)


def unregister():
    bpy.utils.unregister_class(OBJECT_PT_GridGeneratorPanel)
    bpy.utils.unregister_class(GenerateNodesOperator)
    bpy.utils.unregister_class(CreateEdgesOperator)
    bpy.utils.unregister_class(UpdateTextSizeOperator)
    bpy.utils.unregister_class(UpdateEdgeSizeOperator)
    bpy.utils.unregister_class(ApplyEmissiveMaterialOperator)
    bpy.utils.unregister_class(ResizeSceneOperator)
    bpy.utils.unregister_class(GridSettings)
    del bpy.types.Scene.grid_settings