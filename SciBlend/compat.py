"""Centralized Blender cross-version compatibility helpers for SciBlend.

All version-dependent logic lives here so the rest of the addon can stay clean
and support Blender 4.5 (LTS) through 5.2 (LTS) from a single code path.

Prefer capability detection (``hasattr`` / ``try`` / ``except``) over version
checks. When a version gate is unavoidable, keep it in this module only.
"""

from __future__ import annotations

import bpy

IS_5_0_PLUS = bpy.app.version >= (5, 0, 0)
IS_5_1_PLUS = bpy.app.version >= (5, 1, 0)
IS_5_2_PLUS = bpy.app.version >= (5, 2, 0)


def eevee_engine_id() -> str:
    """Return the EEVEE render engine identifier for the running Blender.

    The engine id was renamed from ``BLENDER_EEVEE_NEXT`` (4.5) to
    ``BLENDER_EEVEE`` in Blender 5.0.
    """
    return "BLENDER_EEVEE" if IS_5_0_PLUS else "BLENDER_EEVEE_NEXT"


def get_scene_compositor_tree(scene, create: bool = False):
    """Return the scene's compositor node tree across Blender versions.

    Blender 5.0 removed ``scene.node_tree`` (and deprecated ``scene.use_nodes``)
    in favor of ``scene.compositing_node_group``. On 4.5, enabling
    ``scene.use_nodes`` creates ``scene.node_tree``.

    When ``create`` is True, the tree is created/assigned if it does not exist,
    mirroring the old ``scene.use_nodes = True`` behavior.
    """
    if hasattr(scene, "compositing_node_group"):
        tree = scene.compositing_node_group
        if tree is None and create:
            tree = bpy.data.node_groups.new("Compositor", "CompositorNodeTree")
            scene.compositing_node_group = tree
        return tree
    if create and not scene.use_nodes:
        scene.use_nodes = True
    return getattr(scene, "node_tree", None)


def _ensure_compositor_output_socket(tree):
    """Ensure the compositor node group exposes a single 'Image' Color output.

    On Blender 5.0+ the scene compositor is a node group and its final result is
    read from the first Color input of a Group Output node, which requires a
    matching output socket in ``tree.interface``.
    """
    for item in tree.interface.items_tree:
        if (getattr(item, "item_type", "") == "SOCKET"
                and getattr(item, "in_out", "") == "OUTPUT"
                and (item.name == "Image" or getattr(item, "socket_type", "") == "NodeSocketColor")):
            return item
    return tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")


def get_compositor_output_node(tree, create: bool = False):
    """Return ``(node, image_input_socket)`` for the compositor's final output.

    Blender 5.0 removed the ``CompositorNodeComposite`` node; the scene
    compositor output is now a Group Output node whose first Color input is the
    rendered result. This helper hides that difference so callers can link the
    final image into ``image_input_socket`` regardless of version. Returns
    ``(None, None)`` when the node does not exist and ``create`` is False.
    """
    if hasattr(bpy.types, "CompositorNodeComposite"):
        node = tree.nodes.get("Composite")
        if node is None and create:
            node = tree.nodes.new("CompositorNodeComposite")
        if node is None:
            return None, None
        return node, node.inputs["Image"]

    node = next((n for n in tree.nodes if n.bl_idname == "NodeGroupOutput"), None)
    if node is None and not create:
        return None, None
    _ensure_compositor_output_socket(tree)
    if node is None:
        node = tree.nodes.new("NodeGroupOutput")
    socket = node.inputs.get("Image") or (node.inputs[0] if len(node.inputs) else None)
    return node, socket


# Blender 5.0 turned the compositor Scale node options into input sockets and
# renamed the enum values to human-readable labels; 4.x used object attributes.
_SCALE_MODE_LEGACY = {"Relative": "RELATIVE", "Absolute": "ABSOLUTE",
                      "Scene Size": "SCENE_SIZE", "Render Size": "RENDER_SIZE"}
_FRAME_METHOD_LEGACY = {"Stretch": "STRETCH", "Fit": "FIT", "Crop": "CROP"}


def set_compositor_scale(node, mode=None, frame_method=None, x=None, y=None) -> None:
    """Configure a compositor Scale node across Blender versions.

    ``mode``/``frame_method`` use the Blender 5.x labels ('Relative',
    'Render Size', 'Fit', ...). On 5.0+ the options and X/Y factors are input
    sockets; on 4.x they were object attributes with UPPER_CASE enum values.
    """
    ins = node.inputs
    type_sock = ins.get("Type")
    if type_sock is not None:
        if mode is not None:
            try:
                type_sock.default_value = mode
            except Exception:
                pass
        if frame_method is not None:
            fs = ins.get("Frame Type")
            if fs is not None:
                try:
                    fs.default_value = frame_method
                except Exception:
                    pass
    else:
        if mode is not None and hasattr(node, "space"):
            try:
                node.space = _SCALE_MODE_LEGACY.get(mode, mode)
            except Exception:
                pass
        if frame_method is not None and hasattr(node, "frame_method"):
            try:
                node.frame_method = _FRAME_METHOD_LEGACY.get(frame_method, frame_method)
            except Exception:
                pass
    if x is not None:
        xs = ins.get("X")
        if xs is not None:
            xs.default_value = x
    if y is not None:
        ys = ins.get("Y")
        if ys is not None:
            ys.default_value = y


def get_compositor_scale_mode(node):
    """Return a Scale node's mode as a 5.x label ('Relative', 'Render Size', ...)."""
    type_sock = node.inputs.get("Type")
    if type_sock is not None:
        try:
            return type_sock.default_value
        except Exception:
            return None
    sp = getattr(node, "space", None)
    inverse = {v: k for k, v in _SCALE_MODE_LEGACY.items()}
    return inverse.get(sp, sp)


def set_translate_node(node, x=None, y=None) -> None:
    """Set a compositor Translate node's X/Y offsets by socket name (5.x safe)."""
    ins = node.inputs
    if x is not None:
        xs = ins.get("X") or (ins[1] if len(ins) > 1 else None)
        if xs is not None:
            xs.default_value = x
    if y is not None:
        ys = ins.get("Y") or (ins[2] if len(ins) > 2 else None)
        if ys is not None:
            ys.default_value = y


def alpha_over_sockets(node):
    """Return ``(background, foreground, factor)`` inputs of an Alpha Over node.

    Blender 5.0 reordered the Alpha Over inputs to
    ``(Background, Foreground, Factor)`` and turned the factor into a plain
    input; 4.x used ``(Fac, Image, Image)``. Returning the sockets by role keeps
    callers correct regardless of index ordering.
    """
    ins = node.inputs
    bg = ins.get("Background")
    if bg is not None:
        return bg, ins.get("Foreground"), ins.get("Factor")
    return ins[1], ins[2], ins[0]


def set_gn_modifier_input(modifier, identifier, value) -> None:
    """Set a Geometry Nodes modifier input by socket identifier.

    Blender 5.2 moved GN modifier input access from custom-property subscripting
    (``modifier['Socket_2']``) to RNA properties
    (``modifier.properties.inputs.<id>.value``). This helper picks the right
    path so callers work on 4.5 through 5.2.
    """
    props = getattr(modifier, "properties", None)
    inputs = getattr(props, "inputs", None) if props is not None else None
    if inputs is not None and hasattr(inputs, identifier):
        getattr(inputs, identifier).value = value
    else:
        modifier[identifier] = value


def get_gn_modifier_input(modifier, identifier):
    """Read a Geometry Nodes modifier input by socket identifier (see above)."""
    props = getattr(modifier, "properties", None)
    inputs = getattr(props, "inputs", None) if props is not None else None
    if inputs is not None and hasattr(inputs, identifier):
        return getattr(inputs, identifier).value
    return modifier[identifier]


def iter_action_fcurves(action, slot=None):
    """Yield every F-Curve of an ``Action`` across Blender versions.

    Blender 4.4 introduced "slotted" (layered) actions and Blender 5.0 removed
    the legacy ``Action.fcurves`` collection. F-Curves now live under
    ``action.layers[*].strips[*].channelbag(slot).fcurves``. This helper falls
    back to the legacy ``action.fcurves`` when present so callers work on 4.5
    through 5.2.

    When ``slot`` is given (e.g. ``obj.animation_data.action_slot``), only the
    channelbag for that slot is used; otherwise every channelbag is traversed.
    """
    if action is None:
        return
    legacy = getattr(action, "fcurves", None)
    if legacy is not None:
        yield from legacy
        return
    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            if getattr(strip, "type", None) != 'KEYFRAME':
                continue
            if slot is not None:
                bag = strip.channelbag(slot)
                if bag is not None:
                    yield from bag.fcurves
            else:
                for bag in getattr(strip, "channelbags", ()):
                    yield from bag.fcurves


def clear_action_fcurves(action, slot=None) -> None:
    """Remove every F-Curve from an ``Action`` across Blender versions.

    Legacy actions expose ``action.fcurves.clear()``; slotted actions (4.4+)
    keep F-Curves inside per-slot channelbags, so each one must be removed from
    its owning collection.
    """
    if action is None:
        return
    legacy = getattr(action, "fcurves", None)
    if legacy is not None:
        legacy.clear()
        return
    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            if getattr(strip, "type", None) != 'KEYFRAME':
                continue
            bags = ([strip.channelbag(slot)] if slot is not None
                    else list(getattr(strip, "channelbags", ())))
            for bag in bags:
                if bag is None:
                    continue
                for fcurve in list(bag.fcurves):
                    bag.fcurves.remove(fcurve)
