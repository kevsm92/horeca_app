"""Pure, offline floor-plan footprint containment validator.

All measurements are integer millimetres in the same room coordinate system.
This validates geometry only, not egress, fire safety, or authorization.
"""


def validate_room_footprints(room_width, room_height, footprints):
    """Reject tables outside the room; edges may touch the room boundary.

    Each footprint is (table_id, left, top, width, height). No mutation.
    """
    if any(type(v) is not int or v <= 0 for v in (room_width, room_height)):
        raise ValueError('room dimensions must be positive integer millimetres')
    if not isinstance(footprints, (list, tuple)) or len(footprints) > 200:
        raise ValueError('expected at most 200 footprints')
    seen = set()
    for item in footprints:
        if not isinstance(item, (tuple, list)) or len(item) != 5:
            raise ValueError('invalid footprint')
        table_id, left, top, width, height = item
        if not isinstance(table_id, str) or not table_id.strip() or table_id in seen:
            raise ValueError('invalid or duplicate table ID')
        seen.add(table_id)
        if any(type(v) is not int for v in (left, top, width, height)):
            raise ValueError('footprint dimensions must be integer millimetres')
        if left < 0 or top < 0 or width <= 0 or height <= 0:
            raise ValueError('invalid footprint geometry')
        if left + width > room_width or top + height > room_height:
            raise ValueError('table footprint exceeds room bounds')
    return True
