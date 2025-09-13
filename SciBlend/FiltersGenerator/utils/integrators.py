from mathutils import Vector


def rk4_step(pos: Vector, h: float, field_func, *args, **kwargs) -> Vector:
    k1 = field_func(pos, *args, **kwargs)
    k2 = field_func(pos + (h * 0.5) * k1, *args, **kwargs)
    k3 = field_func(pos + (h * 0.5) * k2, *args, **kwargs)
    k4 = field_func(pos + h * k3, *args, **kwargs)
    return pos + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def integrate_streamline(start: Vector, step_size: float, max_steps: int, min_vel: float,
                          max_length: float, field_func, inside_domain, *args, **kwargs):
    points = [start.copy()]
    length = 0.0
    pos = start.copy()
    for i in range(max_steps):
        v = field_func(pos, *args, **kwargs)
        speed = v.length
        if speed < min_vel:
            break
        next_pos = rk4_step(pos, step_size, field_func, *args, **kwargs)
        segment = (next_pos - pos)
        length += segment.length
        if max_length > 0.0 and length >= max_length:
            points.append(next_pos)
            break
        if not inside_domain(next_pos):
            points.append(next_pos)
            break
        points.append(next_pos)
        pos = next_pos
    return points 