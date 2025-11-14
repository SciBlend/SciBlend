import bpy

_UPDATING_NODES = False
_SCHEDULED_UPDATE = None


def _signature(settings):
    try:
        vo = getattr(settings, 'volume_object', None)
        so = getattr(settings, 'slice_object', None)
        return (
            getattr(vo, 'name', None),
            getattr(settings, 'grid_name', None),
            getattr(settings, 'colormap', None),
            bool(getattr(settings, 'auto_range', False)),
            float(getattr(settings, 'from_min', 0.0)),
            float(getattr(settings, 'from_max', 1.0)),
            float(getattr(settings, 'alpha_baseline', 0.0)),
            float(getattr(settings, 'alpha_multiplier', 0.0)),
            bool(getattr(settings, 'clip_min', True)),
            bool(getattr(settings, 'clip_max', False)),
            float(getattr(settings, 'anisotropy', 0.0)),
            float(getattr(settings, 'emission_strength', 0.0)),
            getattr(so, 'name', None),
            bool(getattr(settings, 'slice_invert', False)),
            getattr(settings, 'component_mode', None),
        )
    except Exception:
        return None


def _schedule_volume_nodes_update():
    global _SCHEDULED_UPDATE

    def _do_update():
        global _UPDATING_NODES, _SCHEDULED_UPDATE
        _SCHEDULED_UPDATE = None
        if _UPDATING_NODES:
            return None
        s = getattr(getattr(bpy.context, 'scene', None), 'filters_volume_settings', None)
        if not s:
            return None
        pending_sig = getattr(s, '_last_scheduled_signature', None)
        last_applied = getattr(s, '_last_applied_signature', None)
        if pending_sig is not None and pending_sig == last_applied:
            return None
        _UPDATING_NODES = True
        try:
            bpy.ops.filters.volume_update_material('EXEC_DEFAULT')
            if pending_sig is None:
                pending_sig = _signature(s)
            s._last_applied_signature = pending_sig
        except Exception:
            pass
        _UPDATING_NODES = False
        return None

    if _SCHEDULED_UPDATE is not None:
        try:
            bpy.app.timers.unregister(_SCHEDULED_UPDATE)
        except Exception:
            pass
    _SCHEDULED_UPDATE = _do_update
    try:
        bpy.app.timers.register(_SCHEDULED_UPDATE, first_interval=0.05)
    except Exception:
        pass


class VolumeRenderingSettings(bpy.types.PropertyGroup):
    volume_object: bpy.props.PointerProperty(type=bpy.types.Object, update=lambda self, ctx: _on_volume_settings_update(self, ctx))
    grid_name: bpy.props.EnumProperty(name="Grid", items=lambda self, ctx: _volume_grid_items(self, ctx), update=lambda self, ctx: _on_volume_settings_update(self, ctx))
    colormap: bpy.props.EnumProperty(name="Colormap", items=lambda self, ctx: _colormap_items(self, ctx), update=lambda self, ctx: _on_volume_settings_update(self, ctx))

    auto_range: bpy.props.BoolProperty(name="Auto Range", default=True, update=lambda self, ctx: _on_volume_settings_update(self, ctx))
    from_min: bpy.props.FloatProperty(name="From Min", default=0.0, update=lambda self, ctx: _on_volume_settings_update(self, ctx))
    from_max: bpy.props.FloatProperty(name="From Max", default=1.0, update=lambda self, ctx: _on_volume_settings_update(self, ctx))

    density_scale: bpy.props.FloatProperty(name="Density Scale", default=50.0, min=0.0, soft_max=1000.0, update=lambda self, ctx: _on_volume_settings_update(self, ctx))
    alpha_baseline: bpy.props.FloatProperty(name="Alpha Baseline", default=0.2, min=0.0, max=100.0, update=lambda self, ctx: _on_volume_settings_update(self, ctx))
    alpha_multiplier: bpy.props.FloatProperty(name="Alpha Multiplier", default=0.0, min=0.0, max=100.0, update=lambda self, ctx: _on_volume_settings_update(self, ctx))
    clip_min: bpy.props.BoolProperty(name="Clip Min", default=True, update=lambda self, ctx: _on_volume_settings_update(self, ctx))
    clip_max: bpy.props.BoolProperty(name="Clip Max", default=False, update=lambda self, ctx: _on_volume_settings_update(self, ctx))
    anisotropy: bpy.props.FloatProperty(name="Anisotropy", default=0.0, min=-0.9, max=0.9, update=lambda self, ctx: _on_volume_settings_update(self, ctx))
    emission_strength: bpy.props.FloatProperty(name="Emission", default=0.0, min=0.0, soft_max=10.0, update=lambda self, ctx: _on_volume_settings_update(self, ctx))

    component_mode: bpy.props.EnumProperty(
        name="Component",
        description="Choose which component of a vector grid to use",
        items=[
            ('X', 'X', ''),
            ('Y', 'Y', ''),
            ('Z', 'Z', ''),
            ('MAG', 'Magnitude', ''),
        ],
        default='MAG',
        update=lambda self, ctx: _on_volume_settings_update(self, ctx),
    )

    slice_object: bpy.props.PointerProperty(type=bpy.types.Object, update=lambda self, ctx: _on_volume_settings_update(self, ctx))
    slice_invert: bpy.props.BoolProperty(name="Invert Slice", default=False, update=lambda self, ctx: _on_volume_settings_update(self, ctx))

    last_import_dir: bpy.props.StringProperty(name="Last Import Dir", default="", subtype='DIR_PATH')
    last_import_files: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)


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
        items = [("", "(no grids)", "")]
    return items


def _colormap_items(self, context):
    try:
        from ..utils.colormaps import get_colormap_enum
        return get_colormap_enum()
    except Exception:
        return [("", "(no colormaps)", "")]


def _on_volume_settings_update(self, context):
    global _UPDATING_NODES
    try:
        s = self
        if _UPDATING_NODES:
            return
        if not s or not getattr(s, 'volume_object', None) or getattr(s.volume_object, 'type', '') != 'VOLUME':
            return
        try:
            valid = [item[0] for item in _volume_grid_items(self, context) or []]
            if getattr(s, 'grid_name', '') and valid and s.grid_name not in valid:
                return
        except Exception:
            pass
        sig = _signature(s)
        if sig is None:
            return
        last_applied = getattr(s, '_last_applied_signature', None)
        if last_applied is not None and sig == last_applied:
            return
        s._last_scheduled_signature = sig
        _schedule_volume_nodes_update()
    except Exception:
        pass


def register():
    bpy.utils.register_class(VolumeRenderingSettings)


def unregister():
    bpy.utils.unregister_class(VolumeRenderingSettings) 