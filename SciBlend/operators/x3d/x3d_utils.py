import os
import bpy
import math
import xml.etree.ElementTree as ET
from typing import List, Tuple, Optional, Dict


def _parse_float_list(text: str) -> List[float]:
    """Parse a whitespace and comma separated float list."""
    if not text:
        return []
    text = text.replace(',', ' ')
    parts = [p for p in text.split() if p]
    return [float(p) for p in parts]


def _parse_int_list(text: str) -> List[int]:
    """Parse a whitespace and comma separated int list."""
    if not text:
        return []
    text = text.replace(',', ' ')
    parts = [p for p in text.split() if p]
    return [int(p) for p in parts]


def _endswith(tag: str, name: str) -> bool:
    """Return True if element tag localname matches name, ignoring namespace."""
    return tag.lower().endswith(name.lower())


def _split_indices(indices: List[int]) -> List[List[int]]:
    """Split lists on -1 separators."""
    groups: List[List[int]] = []
    acc: List[int] = []
    for v in indices:
        if v == -1:
            if acc:
                groups.append(acc)
                acc = []
        else:
            acc.append(v)
    if acc:
        groups.append(acc)
    return groups


def _parse_colors_from_node(node: ET.Element) -> List[Tuple[float, float, float, float]]:
    """Parse Color or ColorRGBA under the given node into RGBA list."""
    for el in node.iter():
        if _endswith(el.tag, 'Color') and el.get('color'):
            floats = _parse_float_list(el.get('color'))
            tuples = list(zip(*(iter(floats),) * 3))
            return [(float(r), float(g), float(b), 1.0) for r, g, b in tuples]
        if _endswith(el.tag, 'ColorRGBA') and el.get('color'):
            floats = _parse_float_list(el.get('color'))
            tuples = list(zip(*(iter(floats),) * 4))
            return [(float(r), float(g), float(b), float(a)) for r, g, b, a in tuples]
    return []


def _extract_geometry_with_colors(root: ET.Element) -> Tuple[
    List[Tuple[float, float, float]],
    List[Tuple[int, int]],
    List[Tuple[int, ...]],
    Dict[str, List]
]:
    """Extract vertices, edges, faces and color data from IndexedLineSet/IndexedFaceSet."""
    vertices: List[Tuple[float, float, float]] = []
    edges: List[Tuple[int, int]] = []
    faces: List[Tuple[int, ...]] = []
    colors: Dict[str, List] = {}

    coord_points: List[Tuple[float, float, float]] = []
    for el in root.iter():
        if _endswith(el.tag, 'Coordinate') and el.get('point'):
            floats = _parse_float_list(el.get('point'))
            triplets = list(zip(*(iter(floats),) * 3))
            coord_points = [(float(x), float(y), float(z)) for x, y, z in triplets]
            break
    if coord_points:
        vertices = coord_points

    for el in root.iter():
        if _endswith(el.tag, 'IndexedLineSet') and el.get('coordIndex'):
            idx = _parse_int_list(el.get('coordIndex'))
            groups = _split_indices(idx)
            for group in groups:
                for a, b in zip(group, group[1:]):
                    if a >= 0 and b >= 0:
                        edges.append((a, b))
            line_colors = _parse_colors_from_node(el)
            if line_colors:
                color_per_vertex = el.get('colorPerVertex', 'true').lower() != 'false'
                color_index = _parse_int_list(el.get('colorIndex') or '')
                if color_per_vertex:
                    if color_index:
                        flat_ci = [ci for g in _split_indices(color_index) for ci in g]
                        vi_flat = [vi for g in groups for vi in g]
                        vertex_rgba = [(1.0, 1.0, 1.0, 1.0)] * len(vertices)
                        for ci, vi in zip(flat_ci, vi_flat):
                            if 0 <= ci < len(line_colors) and 0 <= vi < len(vertex_rgba):
                                vertex_rgba[vi] = line_colors[ci]
                        colors['vertex_rgba'] = vertex_rgba
                    else:
                        vi_flat = [vi for g in groups for vi in g]
                        if len(line_colors) == len(vi_flat):
                            vertex_rgba = [(1.0, 1.0, 1.0, 1.0)] * len(vertices)
                            for col, vi in zip(line_colors, vi_flat):
                                if 0 <= vi < len(vertex_rgba):
                                    vertex_rgba[vi] = col
                            colors['vertex_rgba'] = vertex_rgba
                        elif len(line_colors) == len(vertices):
                            colors['vertex_rgba'] = line_colors
                else:
                    vertex_rgba = [(1.0, 1.0, 1.0, 1.0)] * len(vertices)
                    if color_index:
                        ci_groups = _split_indices(color_index)
                        for gi, group in enumerate(groups):
                            ci = ci_groups[gi][0] if gi < len(ci_groups) and ci_groups[gi] else 0
                            col = line_colors[ci] if 0 <= ci < len(line_colors) else (1.0, 1.0, 1.0, 1.0)
                            for vi in group:
                                if 0 <= vi < len(vertex_rgba):
                                    vertex_rgba[vi] = col
                    else:
                        chosen = line_colors[0] if line_colors else (1.0, 1.0, 1.0, 1.0)
                        for group in groups:
                            for vi in group:
                                if 0 <= vi < len(vertex_rgba):
                                    vertex_rgba[vi] = chosen
                    colors['vertex_rgba'] = vertex_rgba

        if _endswith(el.tag, 'IndexedFaceSet') and el.get('coordIndex'):
            coord_index = _parse_int_list(el.get('coordIndex'))
            face_groups = _split_indices(coord_index)
            for group in face_groups:
                if len(group) >= 3:
                    faces.append(tuple(group))
            face_colors = _parse_colors_from_node(el)
            if face_colors:
                color_per_vertex = el.get('colorPerVertex', 'true').lower() != 'false'
                color_index = _parse_int_list(el.get('colorIndex') or '')
                if color_per_vertex:
                    if color_index:
                        corner_colors: List[Tuple[float, float, float, float]] = []
                        for group in _split_indices(color_index):
                            for ci in group:
                                if 0 <= ci < len(face_colors):
                                    corner_colors.append(face_colors[ci])
                        if corner_colors:
                            colors['corner_rgba'] = corner_colors
                    else:
                        total_corners = sum(len(g) for g in face_groups)
                        if len(face_colors) == total_corners:
                            corner_colors: List[Tuple[float, float, float, float]] = []
                            it = iter(face_colors)
                            for group in face_groups:
                                for _ in group:
                                    try:
                                        corner_colors.append(next(it))
                                    except StopIteration:
                                        corner_colors.append((1.0, 1.0, 1.0, 1.0))
                            if corner_colors:
                                colors['corner_rgba'] = corner_colors
                        elif len(face_colors) == len(vertices):
                            colors['vertex_rgba'] = face_colors
                else:
                    if color_index:
                        face_rgba: List[Tuple[float, float, float, float]] = []
                        idx_groups = _split_indices(color_index)
                        for gi, group in enumerate(face_groups):
                            if gi < len(idx_groups) and idx_groups[gi]:
                                ci = idx_groups[gi][0]
                                face_rgba.append(face_colors[ci] if 0 <= ci < len(face_colors) else (1.0, 1.0, 1.0, 1.0))
                            else:
                                face_rgba.append((1.0, 1.0, 1.0, 1.0))
                        colors['face_rgba'] = face_rgba
                    else:
                        if len(face_colors) == len(faces):
                            colors['face_rgba'] = face_colors

    return vertices, edges, faces, colors


def _ensure_color_attr(mesh: bpy.types.Mesh, name: str, domain: str):
    """Create or replace a color attribute in mesh.color_attributes."""
    try:
        existing = mesh.color_attributes.get(name)
        if existing and existing.domain == domain:
            return existing
        if existing:
            mesh.color_attributes.remove(existing)
        return mesh.color_attributes.new(name=name, type='FLOAT_COLOR', domain=domain)
    except Exception:
        attr = mesh.attributes.get(name)
        if attr and attr.domain == domain:
            return attr
        if attr:
            mesh.attributes.remove(attr)
        return mesh.attributes.new(name=name, type='FLOAT_COLOR', domain=domain)


def _apply_colors(mesh: bpy.types.Mesh, colors: Dict[str, List]) -> None:
    """Create a POINT color attribute named 'Col' and assign values.

    If colors are provided per-corner or per-face, they are averaged onto vertices
    so that the final attribute is always POINT-domain for shader compatibility.
    """
    if not colors:
        return

    attr = _ensure_color_attr(mesh, 'Col', 'POINT')
    vertex_count = len(mesh.vertices)
    if vertex_count == 0:
        return

    accum: List[Tuple[float, float, float, float]] = [(0.0, 0.0, 0.0, 0.0) for _ in range(vertex_count)]
    counts: List[int] = [0 for _ in range(vertex_count)]

    # Case 1: direct vertex colors
    if 'vertex_rgba' in colors:
        data = colors['vertex_rgba']
        max_len = min(len(attr.data), min(len(data), vertex_count))
        for i in range(max_len):
            attr.data[i].color = data[i]
        try:
            mesh.color_attributes.active_color = attr
            mesh.color_attributes.render_color = attr
        except Exception:
            pass
        mesh.update()
        return

    # Case 2: corner colors -> accumulate to vertices via loops
    if 'corner_rgba' in colors and mesh.loops:
        data = colors['corner_rgba']
        loop_len = min(len(mesh.loops), len(data))
        for li in range(loop_len):
            vi = mesh.loops[li].vertex_index
            r, g, b, a = accum[vi]
            cr, cg, cb, ca = data[li]
            accum[vi] = (r + cr, g + cg, b + cb, a + ca)
            counts[vi] += 1
        # Average and assign
        for i in range(vertex_count):
            if counts[i] > 0:
                r, g, b, a = accum[i]
                attr.data[i].color = (r / counts[i], g / counts[i], b / counts[i], a / counts[i])
            else:
                attr.data[i].color = (1.0, 1.0, 1.0, 1.0)
        try:
            mesh.color_attributes.active_color = attr
            mesh.color_attributes.render_color = attr
        except Exception:
            pass
        mesh.update()
        return

    # Case 3: face colors -> accumulate to vertices via polygon loops
    if 'face_rgba' in colors and mesh.polygons:
        data = colors['face_rgba']
        poly_len = min(len(mesh.polygons), len(data))
        for pi in range(poly_len):
            col = data[pi]
            for li in mesh.polygons[pi].loop_indices:
                vi = mesh.loops[li].vertex_index
                r, g, b, a = accum[vi]
                cr, cg, cb, ca = col
                accum[vi] = (r + cr, g + cg, b + cb, a + ca)
                counts[vi] += 1
        for i in range(vertex_count):
            if counts[i] > 0:
                r, g, b, a = accum[i]
                attr.data[i].color = (r / counts[i], g / counts[i], b / counts[i], a / counts[i])
            else:
                attr.data[i].color = (1.0, 1.0, 1.0, 1.0)
        try:
            mesh.color_attributes.active_color = attr
            mesh.color_attributes.render_color = attr
        except Exception:
            pass
        mesh.update()
        return

    # Default: leave white
    for i in range(vertex_count):
        attr.data[i].color = (1.0, 1.0, 1.0, 1.0)
    try:
        mesh.color_attributes.active_color = attr
        mesh.color_attributes.render_color = attr
    except Exception:
        pass
    mesh.update()


def import_x3d_minimal(filepath: str, name: str, scale: float = 1.0, collection: Optional[bpy.types.Collection] = None) -> bpy.types.Object:
    """Import an X3D file without relying on the built-in X3D add-on.

    Supports IndexedFaceSet and IndexedLineSet with inline Coordinate point arrays
    and Color/ColorRGBA mapping. Returns the created object.

    If 'collection' is provided, the created object will be linked to that collection;
    otherwise it will be linked to the active scene collection.
    """
    tree = ET.parse(filepath)
    root = tree.getroot()
    vertices, edges, faces, colors = _extract_geometry_with_colors(root)
    if not vertices and not edges and not faces:
        raise ValueError("No geometry found in X3D file")

    if scale != 1.0 and vertices:
        scaled = []
        for x, y, z in vertices:
            scaled.append((x * scale, y * scale, z * scale))
        vertices = scaled

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, edges, faces)
    mesh.update()

    _apply_colors(mesh, colors)

    obj = bpy.data.objects.new(name, mesh)
    target_collection = collection or bpy.context.scene.collection
    target_collection.objects.link(obj)
    return obj 