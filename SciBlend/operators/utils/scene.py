import bpy
from typing import Iterable


def clear_scene(context: bpy.types.Context) -> None:
	"""Delete all objects in the current scene and purge orphan data blocks."""
	try:
		if bpy.ops.object.mode_set.poll():
			bpy.ops.object.mode_set(mode='OBJECT')
	except Exception:
		pass
	for obj in list(bpy.data.objects):
		try:
			obj.hide_set(False)
		except Exception:
			pass
		try:
			obj.hide_viewport = False
			obj.hide_select = False
		except Exception:
			pass
		try:
			obj.select_set(True)
		except Exception:
			pass
	try:
		context.view_layer.objects.active = None
	except Exception:
		pass
	try:
		if bpy.ops.object.delete.poll():
			bpy.ops.object.delete()
	except Exception:
		pass
	for datablocks in (
		bpy.data.meshes,
		bpy.data.curves,
		bpy.data.materials,
		bpy.data.images,
		bpy.data.armatures,
		bpy.data.node_groups,
		getattr(bpy.data, 'textures', []),
		bpy.data.collections,
	):
		try:
			for block in list(datablocks):
				if getattr(block, 'users', 0) == 0:
					try:
						datablocks.remove(block)
					except Exception:
						pass
		except Exception:
			pass


def keyframe_visibility_single_frame(obj: bpy.types.Object, frame: int) -> None:
	"""Insert keyframes so the object is visible only at the given frame.

	The function sets hide flags to be disabled exactly at 'frame' and enabled at 'frame-1' and 'frame+1'.
	"""
	obj.hide_viewport = False
	obj.hide_render = False
	obj.keyframe_insert(data_path="hide_viewport", frame=frame)
	obj.keyframe_insert(data_path="hide_render", frame=frame)
	obj.hide_viewport = True
	obj.hide_render = True
	obj.keyframe_insert(data_path="hide_viewport", frame=frame - 1)
	obj.keyframe_insert(data_path="hide_render", frame=frame - 1)
	obj.keyframe_insert(data_path="hide_viewport", frame=frame + 1)
	obj.keyframe_insert(data_path="hide_render", frame=frame + 1)


def enforce_constant_interpolation(obj: bpy.types.Object) -> None:
	"""Force all keyframes on the object's action to use CONSTANT interpolation."""
	if obj.animation_data and obj.animation_data.action:
		for fcurve in obj.animation_data.action.fcurves:
			for kf in fcurve.keyframe_points:
				kf.interpolation = 'CONSTANT' 