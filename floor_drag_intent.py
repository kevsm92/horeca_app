"""Offline pointer-drag intent validator; no authorization or persistence.

Coordinates are integer millimetres. A UI must convert pointer pixels to mm,
then submit the resulting position through an authorized revision-checked write.
"""
from floor_overlap_guard import validate_no_overlap


def drag_table(rectangles, table_id, x_mm, y_mm, floor_width_mm, floor_height_mm):
    """Return a new tuple of rectangles after a bounded, collision-free drag.

    Each rectangle is (id, x, y, width, height). Does not mutate caller data.
    """
    if any(type(v) is not int for v in (x_mm, y_mm, floor_width_mm, floor_height_mm)):
        raise ValueError('coordinates and floor dimensions must be integers')
    if x_mm < 0 or y_mm < 0 or floor_width_mm <= 0 or floor_height_mm <= 0:
        raise ValueError('invalid floor bounds')
    validate_no_overlap(rectangles)
    if not isinstance(table_id, str) or not table_id:
        raise ValueError('invalid table ID')
    if sum(rect[0] == table_id for rect in rectangles) != 1:
        raise ValueError('table not present exactly once')
    if any(x + w > floor_width_mm or y + h > floor_height_mm
           for _, x, y, w, h in rectangles):
        raise ValueError('existing rectangle outside floor')
    result = tuple((name, x_mm, y_mm, w, h) if name == table_id
                   else (name, x, y, w, h) for name, x, y, w, h in rectangles)
    if any(x + w > floor_width_mm or y + h > floor_height_mm
           for _, x, y, w, h in result):
        raise ValueError('drag outside floor')
    validate_no_overlap(result)
    return result
