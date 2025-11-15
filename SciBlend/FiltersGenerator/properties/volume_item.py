import bpy
from bpy.types import PropertyGroup
from bpy.props import PointerProperty, StringProperty, EnumProperty, FloatProperty, BoolProperty, CollectionProperty


_UPDATING_NODES = False


def _signature(item):
    try:
        vo = getattr(item, 'volume_object', None)
        so = getattr(item, 'slice_object', None)
        return (
            getattr(vo, 'name', None),
            getattr(item, 'grid_name', None),
            getattr(item, 'colormap', None),
            bool(getattr(item, 'auto_range', False)),
            float(getattr(item, 'from_min', 0.0)),
            float(getattr(item, 'from_max', 1.0)),
            float(getattr(item, 'alpha_baseline', 0.0)),
            float(getattr(item, 'alpha_multiplier', 0.0)),
            float(getattr(item, 'opacity_unit_distance', 1.0)),
            float(getattr(item, 'step_size', 0.1)),
            bool(getattr(item, 'clip_min', True)),
            bool(getattr(item, 'clip_max', False)),
            float(getattr(item, 'anisotropy', 0.0)),
            float(getattr(item, 'emission_strength', 0.0)),
            getattr(so, 'name', None),
            bool(getattr(item, 'slice_invert', False)),
            getattr(item, 'component_mode', None),
        )
    except Exception:
        return None


def _volume_grid_items(self, context):
    items = []
    obj = self.volume_object
    if obj and obj.type == 'VOLUME' and getattr(obj, 'data', None):
        try:
            grids = getattr(obj.data, 'grids', None)
            if grids:
                index = 0
                for g in grids:
                    name = getattr(g, 'name', None)
                    if name:
                        items.append((name, name, "", 'DOT', index))
                        index += 1
        except Exception:
            pass
    if not items:
        items = [("NONE", "(no grids)", "", 'INFO', 0)]
    return items


def _colormap_items(self, context):
    try:
        from ..utils.colormaps import get_colormap_enum
        return get_colormap_enum()
    except Exception:
        return [("", "(no colormaps)", "")]


def _on_volume_item_update(self, context):
    global _UPDATING_NODES
    try:
        if _UPDATING_NODES:
            return
        if not self or not getattr(self, 'volume_object', None) or getattr(self.volume_object, 'type', '') != 'VOLUME':
            return
        try:
            valid = [item[0] for item in _volume_grid_items(self, context) or []]
            if getattr(self, 'grid_name', '') and valid and self.grid_name not in valid and self.grid_name != 'NONE':
                return
        except Exception:
            pass
        sig = _signature(self)
        if sig is None:
            return
        last_applied = getattr(self, '_last_applied_signature', None)
        if last_applied is not None and sig == last_applied:
            return
        self._last_scheduled_signature = sig
        
        import importlib
        volume_settings = importlib.import_module('.volume_settings', package=__package__)
        volume_settings._schedule_volume_item_update(self)
    except Exception as e:
        import traceback
        print(f"Error in _on_volume_item_update: {e}")
        traceback.print_exc()


class VolumeItem(PropertyGroup):
    """
    Individual volume object settings for VDB rendering.
    """
    
    name: StringProperty(
        name="Name",
        default="Volume",
    )
    
    volume_object: PointerProperty(
        type=bpy.types.Object,
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    grid_name: EnumProperty(
        name="Grid",
        items=lambda self, ctx: _volume_grid_items(self, ctx),
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    colormap: EnumProperty(
        name="Colormap",
        items=lambda self, ctx: _colormap_items(self, ctx),
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    auto_range: BoolProperty(
        name="Auto Range",
        default=True,
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    from_min: FloatProperty(
        name="From Min",
        default=0.0,
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    from_max: FloatProperty(
        name="From Max",
        default=1.0,
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    density_scale: FloatProperty(
        name="Density Scale",
        default=50.0,
        min=0.0,
        soft_max=1000.0,
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    opacity_unit_distance: FloatProperty(
        name="Opacity Unit Distance",
        description="Similar to ParaView's Scalar Opacity Unit Distance. Controls opacity accumulation based on step size",
        default=1.0,
        min=0.0,
        max=100.0,
        soft_min=0.01,
        soft_max=10.0,
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    step_size: FloatProperty(
        name="Step Size",
        description="Distance between volume samples during rendering. Lower values = more detail but slower",
        default=0.05,
        min=0.001,
        max=1000.0,
        soft_min=0.01,
        soft_max=10.0,
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    alpha_baseline: FloatProperty(
        name="Alpha Baseline",
        default=0.0,
        min=0.0,
        max=100.0,
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    alpha_multiplier: FloatProperty(
        name="Alpha Multiplier",
        default=0.15,
        min=0.0,
        max=100.0,
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    clip_min: BoolProperty(
        name="Clip Min",
        default=True,
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    clip_max: BoolProperty(
        name="Clip Max",
        default=True,
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    anisotropy: FloatProperty(
        name="Anisotropy",
        default=0.0,
        min=-0.9,
        max=0.9,
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    emission_strength: FloatProperty(
        name="Emission",
        default=0.0,
        min=0.0,
        soft_max=10.0,
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    component_mode: EnumProperty(
        name="Component",
        description="Choose which component of a vector grid to use",
        items=[
            ('X', 'X', ''),
            ('Y', 'Y', ''),
            ('Z', 'Z', ''),
            ('MAG', 'Magnitude', ''),
        ],
        default='MAG',
        update=lambda self, ctx: _on_volume_item_update(self, ctx),
    )
    
    slice_object: PointerProperty(
        type=bpy.types.Object,
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    slice_invert: BoolProperty(
        name="Invert Slice",
        default=False,
        update=lambda self, ctx: _on_volume_item_update(self, ctx)
    )
    
    last_import_dir: StringProperty(
        name="Last Import Dir",
        default="",
        subtype='DIR_PATH'
    )
    
    last_import_files: CollectionProperty(type=bpy.types.PropertyGroup)


def register():
    pass


def unregister():
    pass

