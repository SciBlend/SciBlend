
import bpy


def register() -> None:
	"""Register the SciBlend add-on within Blender."""
	from .SciBlend import register as _register
	_register()


def unregister() -> None:
	"""Unregister the SciBlend add-on within Blender."""
	from .SciBlend import unregister as _unregister
	_unregister() 