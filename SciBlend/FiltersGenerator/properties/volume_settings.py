import bpy


class VolumeRenderingSettings(bpy.types.PropertyGroup):
    volume_object: bpy.props.PointerProperty(type=bpy.types.Object)
    grid_name: bpy.props.EnumProperty(name="Grid", items=lambda self, ctx: _volume_grid_items(self, ctx))
    colormap: bpy.props.EnumProperty(name="Colormap", items=lambda self, ctx: _colormap_items(self, ctx))

    auto_range: bpy.props.BoolProperty(name="Auto Range", default=True)
    from_min: bpy.props.FloatProperty(name="From Min", default=0.0)
    from_max: bpy.props.FloatProperty(name="From Max", default=1.0)

    density_scale: bpy.props.FloatProperty(name="Density Scale", default=50.0, min=0.0, soft_max=1000.0)
    anisotropy: bpy.props.FloatProperty(name="Anisotropy", default=0.0, min=-0.9, max=0.9)
    emission_strength: bpy.props.FloatProperty(name="Emission", default=0.0, min=0.0, soft_max=10.0)

    slice_object: bpy.props.PointerProperty(type=bpy.types.Object)
    slice_invert: bpy.props.BoolProperty(name="Invert Slice", default=False)

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


def register():
    bpy.utils.register_class(VolumeRenderingSettings)


def unregister():
    bpy.utils.unregister_class(VolumeRenderingSettings) 