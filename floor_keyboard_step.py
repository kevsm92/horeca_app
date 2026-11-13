"""Pure keyboard movement intent for a floor-plan editor (offline prototype).

This is not an authorization or persistence boundary. Coordinates are millimetres.
"""

DIRECTIONS = {'ArrowLeft': (-1, 0), 'ArrowRight': (1, 0),
              'ArrowUp': (0, -1), 'ArrowDown': (0, 1)}


def keyboard_move(x_mm, y_mm, width_mm, height_mm, floor_width_mm,
                  floor_height_mm, key, *, shift=False, step_mm=50):
    """Return bounded (x,y) for arrow key; reject invalid geometry or input.

    Shift moves 5 steps. A movement against a boundary is a no-op.
    """
    values = (x_mm, y_mm, width_mm, height_mm, floor_width_mm,
              floor_height_mm, step_mm)
    if any(type(value) is not int for value in values):
        raise ValueError('geometry and step must be strict integers')
    if (x_mm < 0 or y_mm < 0 or width_mm <= 0 or height_mm <= 0
            or floor_width_mm <= 0 or floor_height_mm <= 0 or step_mm <= 0
            or x_mm + width_mm > floor_width_mm
            or y_mm + height_mm > floor_height_mm):
        raise ValueError('invalid floor geometry')
    if type(shift) is not bool or key not in DIRECTIONS:
        raise ValueError('unsupported keyboard intent')
    dx, dy = DIRECTIONS[key]
    distance = step_mm * (5 if shift else 1)
    return (max(0, min(floor_width_mm - width_mm, x_mm + dx * distance)),
            max(0, min(floor_height_mm - height_mm, y_mm + dy * distance)))
