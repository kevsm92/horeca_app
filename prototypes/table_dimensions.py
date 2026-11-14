"""Offline table geometry/capacity guard, synthetic-data reference implementation.

Visual width/height are centimetres, independent of physical seat inventory.
No persistence, API, or live venue integration is implied.

>>> resize_table(120, 80, 4, 2, 130, 90, 3, 4)
(130, 90, 3)
>>> resize_table(120, 80, 4, 3, 130, 90, 2, 4)
Traceback (most recent call last):
...
ValueError: seats below active guests
>>> resize_table(120, 80, 4, 0, 130, 90, 5, 4)
Traceback (most recent call last):
...
ValueError: seats exceed physical inventory
"""


def resize_table(width_cm: int, height_cm: int, seats: int,
                 active_guests: int, new_width_cm: int, new_height_cm: int,
                 new_seats: int, physical_seat_limit: int) -> tuple[int, int, int]:
    """Validate an atomic proposed resize; caller must enforce venue lock/revision."""
    values = (width_cm, height_cm, seats, active_guests, new_width_cm,
              new_height_cm, new_seats, physical_seat_limit)
    if any(type(value) is not int for value in values):
        raise ValueError("integer inputs required")
    if not (40 <= width_cm <= 500 and 40 <= height_cm <= 500
            and 40 <= new_width_cm <= 500 and 40 <= new_height_cm <= 500):
        raise ValueError("dimensions outside supported range")
    if seats < 0 or active_guests < 0 or physical_seat_limit < 0 or new_seats < 0:
        raise ValueError("negative inventory or occupancy")
    if seats > physical_seat_limit or active_guests > seats:
        raise ValueError("invalid existing inventory or occupancy")
    if new_seats < active_guests:
        raise ValueError("seats below active guests")
    if new_seats > physical_seat_limit:
        raise ValueError("seats exceed physical inventory")
    return new_width_cm, new_height_cm, new_seats


if __name__ == "__main__":
    import doctest
    result = doctest.testmod()
    if result.failed:
        raise SystemExit(1)
    print(f"PASS: {result.attempted} doctest assertions")
