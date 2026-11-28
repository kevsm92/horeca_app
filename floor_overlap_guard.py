"""Pure optional collision guard for synthetic floor-plan layouts.

Coordinates and dimensions are positive integer millimetres. Touching edges
are allowed; overlapping interiors are rejected. This is not a persistence,
authorization, accessibility-clearance, or physical fire-safety check.
"""


def validate_no_overlap(rectangles):
    """Validate (table_id, x, y, width, height) tuples; return True or raise.

    Input is bounded to avoid pathological quadratic checks. Does not mutate.
    """
    if not isinstance(rectangles, (tuple, list)) or len(rectangles) > 200:
        raise ValueError('expected at most 200 rectangles')
    seen = set()
    for rect in rectangles:
        if not isinstance(rect, (tuple, list)) or len(rect) != 5:
            raise ValueError('invalid rectangle')
        name, x, y, w, h = rect
        if not isinstance(name, str) or not name or name in seen:
            raise ValueError('invalid or duplicate table ID')
        seen.add(name)
        if any(type(v) is not int for v in (x, y, w, h)) or min(x, y) < 0 or min(w, h) <= 0:
            raise ValueError('invalid rectangle geometry')
    for i, (_, ax, ay, aw, ah) in enumerate(rectangles):
        for _, bx, by, bw, bh in rectangles[i + 1:]:
            if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                raise ValueError('overlapping table footprints')
    return True
