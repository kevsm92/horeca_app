"""Register venue-owned physical tables in the offline SQLite prototype.

The caller must authenticate and authorize the venue; this is not an API endpoint.
"""


def register_physical_table(db, venue_id, table_id, capacity):
    """Create exactly one physical table; never infer tables from floor-plan shapes.

    Database primary-key constraints reject duplicates within a venue, while
    identical table IDs in distinct venues remain independent.
    """
    for label, value in (("venue_id", venue_id), ("table_id", table_id)):
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise ValueError(f"{label} must be a nonempty trimmed string")
    if type(capacity) is not int or not 1 <= capacity <= 100:
        raise ValueError("capacity must be an integer from 1 to 100")
    with db:
        db.execute(
            "INSERT INTO physical_tables (venue_id, table_id, capacity) VALUES (?, ?, ?)",
            (venue_id, table_id, capacity),
        )
