import bpy
import bmesh
from mathutils import Vector, Matrix
from bpy_extras import view3d_utils

def create_annotation(start, normal, length, thickness):
    """
    Create an annotation object (cone) at a specified location.

    Args:
        start (Vector): The starting point of the annotation.
        normal (Vector): The direction the annotation should point.
        length (float): The length of the annotation.
        thickness (float): The thickness (radius) of the annotation.

    Returns:
        tuple: A tuple containing the created annotation object and its end point.
    """
    end = start + normal * length
    
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=16,
        radius1=thickness,  
        radius2=thickness,
        depth=length,
        matrix=Matrix.Identity(4)
    )

    for v in bm.verts:
        v.co.z += length / 2

    rot_matrix = normal.to_track_quat('Z', 'Y').to_matrix().to_4x4()

    bmesh.ops.transform(bm, matrix=rot_matrix, verts=bm.verts)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(start), verts=bm.verts)

    mesh = bpy.data.meshes.new("Annotation")
    bm.to_mesh(mesh)
    bm.free()

    annotation_obj = bpy.data.objects.new("Annotation", mesh)
    bpy.context.collection.objects.link(annotation_obj)
    
    # Disable shadow casting (version-safe)
    if hasattr(annotation_obj, "visible_shadow"):
        annotation_obj.visible_shadow = False
    else:
        cycles_vis = getattr(annotation_obj, "cycles_visibility", None)
        if cycles_vis and hasattr(cycles_vis, "shadow"):
            cycles_vis.shadow = False
    
    return annotation_obj, end

def create_text(location, text, size=0.1):
    """
    Create a text object at a specified location.

    Args:
        location (Vector): The location where the text should be placed.
        text (str): The content of the text object.
        size (float, optional): The size of the text. Defaults to 0.1.

    Returns:
        bpy.types.Object: The created text object.
    """
    bpy.ops.object.text_add(enter_editmode=False, location=location)
    text_obj = bpy.context.active_object
    text_obj.data.body = text
    text_obj.data.size = size
    
    # Disable shadow casting (version-safe)
    if hasattr(text_obj, "visible_shadow"):
        text_obj.visible_shadow = False
    else:
        cycles_vis = getattr(text_obj, "cycles_visibility", None)
        if cycles_vis and hasattr(cycles_vis, "shadow"):
            cycles_vis.shadow = False
    
    return text_obj

def create_emission_material(name, color, strength):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    # Disable shadow casting (version-safe)
    if hasattr(mat, "shadow_method"):
        try:
            mat.shadow_method = 'NONE'
        except Exception:
            pass
    # For newer Blender, disable shadow by using emission-only with no shadow links
    node_tree = mat.node_tree
    nodes = node_tree.nodes
    nodes.clear()
    
    emission_node = nodes.new(type='ShaderNodeEmission')
    emission_node.inputs[0].default_value = color
    emission_node.inputs[1].default_value = strength
    
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    
    node_tree.links.new(emission_node.outputs[0], output_node.inputs[0])
    
    return mat

class NOTESGENERATOR_OT_add_annotation(bpy.types.Operator):
    """Operator for adding annotations to the scene."""
    bl_idname = "notesgenerator.add_annotation"
    bl_label = "Add Annotation"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        context.window.cursor_set('CROSSHAIR')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'LEFTMOUSE':
            self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
            return self.execute(context)
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            context.window.cursor_set('DEFAULT')
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def execute(self, context):
        try:
            props = context.scene.annotation_properties
            
            # Cast a ray from the view to the object
            region = context.region
            rv3d = context.region_data
            view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, self.mouse_pos)
            ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, self.mouse_pos)
            
            # Find the intersection with the object
            result, location, normal, index, obj, matrix = context.scene.ray_cast(context.view_layer.depsgraph, ray_origin, view_vector)
            
            if result:
                scale_factors = {
                    'MM': 0.001,
                    'CM': 0.01,
                    'DM': 0.1,
                    'M': 1,
                    'DAM': 10,
                    'HM': 100,
                    'KM': 1000
                }
                scale_factor = scale_factors[props.annotation_scale]
                
                scaled_length = props.annotation_length * scale_factor
                scaled_thickness = props.annotation_thickness * scale_factor
                scaled_text_size = props.text_size * scale_factor
                scaled_text_distance = props.text_distance * scale_factor

                # Create the annotation at the intersection point
                annotation_obj, end_point = create_annotation(location, normal, scaled_length, scaled_thickness)
                
                mat = create_emission_material("Annotation_Material", props.annotation_color, props.emission_strength)
                annotation_obj.data.materials.append(mat)

                text_position = end_point + normal * (scaled_length * scaled_text_distance)
                text_obj = create_text(text_position, props.annotation_text, scaled_text_size)
                
                text_mat = create_emission_material("Text_Material", props.annotation_color, props.emission_strength)
                text_obj.data.materials.append(text_mat)

                if context.scene.camera:
                    constraint = text_obj.constraints.new(type='TRACK_TO')
                    constraint.target = context.scene.camera
                    constraint.track_axis = 'TRACK_Z'
                    constraint.up_axis = 'UP_Y'
                    constraint.use_target_z = True
                else:
                    self.report({'WARNING'}, "No camera found in the scene. Text will not be oriented.")

                annotation_obj["is_annotation"] = True
                text_obj["is_annotation_text"] = True

                self.report({'INFO'}, "Annotation created successfully")
                context.window.cursor_set('DEFAULT')
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "Could not find a suitable location on the object")
                context.window.cursor_set('DEFAULT')
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"An error occurred: {str(e)}")
            import traceback
            traceback.print_exc()
            context.window.cursor_set('DEFAULT')
            return {'CANCELLED'}

def register():
    """Register the NOTESGENERATOR_OT_add_annotation operator."""
    bpy.utils.register_class(NOTESGENERATOR_OT_add_annotation)

def unregister():
    """Unregister the NOTESGENERATOR_OT_add_annotation operator."""
    bpy.utils.unregister_class(NOTESGENERATOR_OT_add_annotation)

if __name__ == "__main__":
    register()