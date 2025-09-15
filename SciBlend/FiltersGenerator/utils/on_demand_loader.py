import bpy
import os
import logging
from collections import deque
from typing import Optional, Tuple
from ...operators.utils.volume_mesh_data import get_model, register_model, unregister_model

logger = logging.getLogger(__name__)
if not logger.handlers:
	logger.setLevel(logging.INFO)

_SUPPORTED_EXTS = ('.vtk', '.vtu', '.pvtu')
_LRU_QUEUE: deque[str] = deque(maxlen=16)


def _safe_info(msg: str) -> None:
	try:
		logger.info(msg)
	except Exception:
		try:
			print(msg)
		except Exception:
			pass


def _safe_error(msg: str) -> None:
	try:
		logger.error(msg)
	except Exception:
		try:
			print(msg)
		except Exception:
			pass


def _get_scene_on_demand_settings(context) -> Tuple[bool, str, int]:
	"""Return tuple (enabled, root_dir, max_cached) from scene settings, with safe defaults."""
	sc = getattr(context, 'scene', None)
	if not sc:
		_safe_error("On-demand: no scene in context")
		return False, '', 0
	enabled = bool(getattr(sc, 'on_demand_volume_enabled', False))
	root = str(getattr(sc, 'on_demand_data_root', '') or '')
	max_cached = int(getattr(sc, 'on_demand_max_cached', 4) or 0)
	_safe_info(f"On-demand: enabled={enabled} root='{root}' max_cached={max_cached}")
	return enabled, root, max_cached


def _find_candidate_file(root_dir: str, obj: bpy.types.Object) -> Optional[str]:
	"""Find a VTK file matching object metadata or name within root_dir."""
	if not root_dir or not os.path.isdir(root_dir):
		_safe_error(f"On-demand: root dir invalid '{root_dir}'")
		return None
	meta_dir = str(obj.get('sciblend_volume_source_dir', '') or '')
	meta_file = str(obj.get('sciblend_volume_source_file', '') or '')
	_safe_info(f"On-demand: meta_dir='{meta_dir}' meta_file='{meta_file}' obj='{obj.name}'")
	if meta_file:
		if meta_dir:
			path = os.path.join(meta_dir, meta_file)
			if os.path.isfile(path):
				_safe_info(f"On-demand: using meta full path '{path}'")
				return path
		cand = os.path.join(root_dir, meta_file)
		if os.path.isfile(cand):
			_safe_info(f"On-demand: using data-root+filename '{cand}'")
			return cand
	name_variants = {obj.name}
	for suf in ("_SliceLive", "_ClipLive", "_ContourLive", "_ThresholdLive"):
		if obj.name.endswith(suf):
			name_variants.add(obj.name[: -len(suf)])
	_safe_info(f"On-demand: scanning root for variants {sorted(name_variants)}")
	try:
		candidates = []
		for entry in os.listdir(root_dir):
			low = entry.lower()
			if not low.endswith(_SUPPORTED_EXTS):
				continue
			stem = os.path.splitext(entry)[0]
			if any(stem.startswith(v) or stem == v for v in name_variants):
				candidates.append(os.path.join(root_dir, entry))
		if candidates:
			candidates.sort()
			_safe_info(f"On-demand: candidate '{candidates[0]}'")
			return candidates[0]
	except Exception as e:
		_safe_error(f"On-demand: listing root failed: {e}")
		return None
	_safe_error("On-demand: no candidate found")
	return None


def _load_volume_model_from_file(filepath: str):
	"""Load a VolumeMeshData from a VTK file without creating a Blender mesh object."""
	try:
		from .vtk_read import read_volume_data_from_vtk
		volume_data, _ = read_volume_data_from_vtk(filepath)
		for i, v in enumerate(volume_data.vertices):
			try:
				v.blender_v_index = i
			except Exception:
				pass
		_safe_info(f"On-demand: loaded model with {len(volume_data.vertices)} verts, {len(volume_data.faces)} faces, {len(volume_data.cells)} cells")
		return volume_data
	except Exception as e:
		_safe_error(f"On-demand: read_grid failed: {e}")
		return None


def ensure_model_for_object(context, obj: bpy.types.Object):
	"""Ensure a VolumeMeshData model is registered for obj.name using on-demand loading if enabled.

	If the model exists, returns it. If on-demand is disabled or loading fails, returns None.
	"""
	model = get_model(obj.name)
	if model is not None:
		_safe_info(f"On-demand: model already in registry for '{obj.name}'")
		return model
	enabled, root_dir, max_cached = _get_scene_on_demand_settings(context)
	if not enabled:
		_safe_info("On-demand: disabled")
		return None
	filepath = _find_candidate_file(root_dir, obj)
	if not filepath:
		_safe_error(f"On-demand: no file found for '{obj.name}'")
		return None
	_safe_info(f"On-demand: loading '{filepath}'")
	model = _load_volume_model_from_file(filepath)
	if model is None:
		_safe_error("On-demand: load returned None")
		return None
	register_model(obj.name, model)
	_safe_info(f"On-demand: registered model for '{obj.name}'")
	try:
		_LRU_QUEUE.append(obj.name)
		while max_cached > 0 and len(_LRU_QUEUE) > max_cached:
			old = _LRU_QUEUE.popleft()
			if old != obj.name:
				unregister_model(old)
				_safe_info(f"On-demand: evicted '{old}' from registry")
	except Exception as e:
		_safe_error(f"On-demand: LRU error: {e}")
	return model


def clear_on_demand_cache():
	"""Clear all lazily registered models and the LRU queue."""
	try:
		while _LRU_QUEUE:
			name = _LRU_QUEUE.popleft()
			unregister_model(name)
			_safe_info(f"On-demand: cleared '{name}'")
	except Exception as e:
		_safe_error(f"On-demand: clear error: {e}")
		pass 