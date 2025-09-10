import bpy
from bpy.props import StringProperty
from typing import Optional
import os
import uuid
import tempfile

try:
    from .. import __package__ as _ROOT_PACKAGE
except Exception:
    _ROOT_PACKAGE = None

ADDON_ID = (_ROOT_PACKAGE if isinstance(_ROOT_PACKAGE, str) and _ROOT_PACKAGE else "sciblend")


def addon_preferences(context: Optional[bpy.types.Context] = None) -> Optional[bpy.types.AddonPreferences]:
    """Return the preferences object for this add-on if available.

    When Blender runs the add-on in development contexts or without the manifest,
    this function safely attempts to access the preferences using the configured
    add-on id.
    """
    if context is None:
        context = bpy.context
    try:
        return context.preferences.addons[ADDON_ID].preferences
    except Exception:
        return None


def get_assets_output_dir(context: Optional[bpy.types.Context] = None) -> str:
    """Return the effective output directory for generated images.

    If the user has configured a directory in preferences, it is returned after
    being resolved to an absolute path. Otherwise, a writable temporary directory
    provided by Blender or the operating system is used.
    """
    prefs = addon_preferences(context)
    if prefs and getattr(prefs, "asset_output_dir", "").strip():
        path = bpy.path.abspath(prefs.asset_output_dir)
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            pass
        return path
    if hasattr(bpy.app, "tempdir") and bpy.app.tempdir:
        return bpy.app.tempdir
    return tempfile.gettempdir()


def build_unique_png_path(base_name: str, context: Optional[bpy.types.Context] = None) -> str:
    """Construct a unique PNG file path within the configured output directory."""
    directory = get_assets_output_dir(context)
    safe_base = "".join(c if c.isalnum() or c in ".-_" else "_" for c in str(base_name) or "image")
    unique = uuid.uuid4().hex
    return os.path.join(directory, f"{safe_base}_{unique}.png")


class SciBlendPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_ID

    asset_output_dir: StringProperty(  # type: ignore
        name="Assets Output Directory",
        description="Directory where temporary legends and shapes images are saved",
        default="",
        subtype="DIR_PATH",
    )

    def draw(self, context: bpy.types.Context) -> None:
        """Draw the preferences UI layout for the add-on."""
        layout = self.layout
        col = layout.column()
        col.label(text="Output directory for temporary legends and shapes:")
        col.prop(self, "asset_output_dir") 