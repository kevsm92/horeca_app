"""Offline collision-aware keyboard move for a floor-plan layout.

Not an authorization or persistence boundary. All geometry is integer mm.
"""
from floor_keyboard_step import keyboard_move
from floor_overlap_guard import validate_no_overlap
from floor_room_bounds import validate_room_footprints


def move_table_by_key(rectangles, table_id, room_width_mm, room_height_mm,
                      key, *, shift=False, step_mm=50):
    """Return a new tuple of footprints; reject collisions without partial edits."""
    validate_room_footprints(room_width_mm, room_height_mm, rectangles)
    validate_no_overlap(rectangles)
    if not isinstance(table_id, str) or sum(r[0] == table_id for r in rectangles) != 1:
        raise ValueError('table not found exactly once')
    original = next(r for r in rectangles if r[0] == table_id)
    _, x, y, width, height = original
    new_x, new_y = keyboard_move(x, y, width, height, room_width_mm,
                                 room_height_mm, key, shift=shift, step_mm=step_mm)
    result = tuple((name, new_x, new_y, w, h) if name == table_id
                   else (name, left, top, w, h)
                   for name, left, top, w, h in rectangles)
    validate_no_overlap(result)
    return result
