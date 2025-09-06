import bpy
import re


def _vector_attr_items(self, context):
    items = []
    obj = getattr(self, "target_object", None)
    if obj and getattr(obj, "type", None) == 'MESH':
        attrs = getattr(obj.data, "attributes", None)
        if attrs:
            # true vector attributes
            for a in attrs:
                data_type = getattr(a, "data_type", "")
                domain = getattr(a, "domain", "")
                if data_type == 'FLOAT_VECTOR' and domain in {'POINT', 'VERTEX'}:
                    items.append((a.name, a.name, "Vector attribute"))

            # composite from scalar components: *_X, *_Y, *_Z
            comp_groups = {}
            name_to_attr = {a.name: a for a in attrs}
            pattern = re.compile(r"^(?P<base>.+?)[._-](?P<comp>[XYZxyz])$")
            for a in attrs:
                if getattr(a, "data_type", "") != 'FLOAT':
                    continue
                if getattr(a, "domain", "") not in {'POINT', 'VERTEX'}:
                    continue
                m = pattern.match(a.name)
                if not m:
                    continue
                base = m.group('base')
                comp = m.group('comp').lower()
                group = comp_groups.setdefault(base, {})
                group[comp] = a.name
                dom = getattr(a, "domain", "")
                group.setdefault('__domain__', dom)

            for base, grp in comp_groups.items():
                if all(k in grp for k in ('x', 'y', 'z')):
                    dom = grp.get('__domain__', '')
                    x_name = grp['x']
                    y_name = grp['y']
                    z_name = grp['z']
                    dom_ok = True
                    try:
                        if not (getattr(name_to_attr[x_name], 'domain', '') == getattr(name_to_attr[y_name], 'domain', '') == getattr(name_to_attr[z_name], 'domain', '')):
                            dom_ok = False
                    except Exception:
                        dom_ok = False
                    if not dom_ok:
                        continue
                    identifier = f"__COMP__:{x_name}|{y_name}|{z_name}"
                    label = f"{base} (components)"
                    items.append((identifier, label, f"Composite from {x_name}, {y_name}, {z_name}"))
    if not items:
        items = [("", "(no vector attributes)", "")]
    return items


class FiltersEmitterSettings(bpy.types.PropertyGroup):
    target_object: bpy.props.PointerProperty(type=bpy.types.Object)
    vector_attribute: bpy.props.EnumProperty(name="Vector Field", items=_vector_attr_items)

    emitter_type: bpy.props.EnumProperty(
        name="Emitter Type",
        description="How to emit streamlines from the emitter",
        items=(
            ('POINT', "Single Point", "Emit a single streamline from the emitter location"),
            ('MESH_FACES', "Mesh Faces", "Emit one streamline from each face center of the emitter mesh"),
        ),
        default='POINT',
    )

    integration_direction: bpy.props.EnumProperty(
        name="Direction",
        description="Integration direction for streamlines",
        items=(
            ('FORWARD', "Forward", "Integrate along the field direction"),
            ('BACKWARD', "Backward", "Integrate against the field direction"),
            ('BOTH', "Both", "Integrate in both directions and merge"),
        ),
        default='FORWARD',
    )

    # sampling & integrator settings
    step_size: bpy.props.FloatProperty(
        name="Step Size",
        description="Integration step size",
        default=0.1,
        min=1e-06,
        soft_max=10.0,
    )
    max_steps: bpy.props.IntProperty(
        name="Max Steps",
        description="Maximum number of integration steps",
        default=5000,
        min=1,
        soft_max=200000,
    )
    k_neighbors: bpy.props.IntProperty(
        name="k-Neighbors",
        description="Number of neighbors for IDW sampling",
        default=8,
        min=1,
        soft_max=64,
    )
    min_velocity: bpy.props.FloatProperty(
        name="Min Velocity",
        description="Stop when field magnitude falls below this (set 0 to disable)",
        default=0.0,
        min=0.0,
        soft_max=1.0,
    )
    field_scale: bpy.props.FloatProperty(
        name="Field Scale",
        description="Scale factor applied to the sampled vector field",
        default=1.0,
        min=0.0,
        soft_max=100.0,
    )
    max_length: bpy.props.FloatProperty(
        name="Max Length",
        description="Maximum streamline length (world units). 0 disables length limit",
        default=0.0,
        min=0.0,
        soft_max=100000.0,
    )

    normalize_field: bpy.props.BoolProperty(
        name="Normalize Field",
        description="Use direction-only vectors (unit length) before scaling",
        default=False,
    )
    stop_at_bounds: bpy.props.BoolProperty(
        name="Stop at Bounds",
        description="Stop integration when leaving domain bounding box",
        default=True,
    )
    bbox_margin: bpy.props.FloatProperty(
        name="Bounds Margin",
        description="Expand domain bounds by this fraction of the bbox size (per axis)",
        default=0.0,
        min=0.0,
        soft_max=1.0,
    )


def register():
    bpy.utils.register_class(FiltersEmitterSettings)


def unregister():
    bpy.utils.unregister_class(FiltersEmitterSettings) 