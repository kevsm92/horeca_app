"""Offline SQLite persistence for approved ingredient density revisions.

The caller supplies the server-authorized venue, never an HTTP body venue.
"""
def initialize_density_store(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS ingredient_density_revisions (
      venue_id TEXT NOT NULL CHECK(length(trim(venue_id)) > 0),
      ingredient_id TEXT NOT NULL CHECK(length(trim(ingredient_id)) > 0),
      revision INTEGER NOT NULL CHECK(revision > 0),
      status TEXT NOT NULL CHECK(status IN ('approved', 'revoked')),
      mg_per_ml_numerator INTEGER NOT NULL CHECK(mg_per_ml_numerator > 0),
      mg_per_ml_denominator INTEGER NOT NULL CHECK(mg_per_ml_denominator > 0),
      PRIMARY KEY(venue_id, ingredient_id, revision)
    );
    CREATE TRIGGER IF NOT EXISTS density_no_update BEFORE UPDATE ON ingredient_density_revisions
    BEGIN SELECT RAISE(ABORT, 'density revisions immutable'); END;
    CREATE TRIGGER IF NOT EXISTS density_no_delete BEFORE DELETE ON ingredient_density_revisions
    BEGIN SELECT RAISE(ABORT, 'density revisions immutable'); END;
    """)


def append_density_revision(db, *, authorized_venue, ingredient_id, revision,
                            status, mg_per_ml_numerator, mg_per_ml_denominator):
    if not isinstance(authorized_venue, str) or not authorized_venue.strip():
        raise ValueError('trusted venue required')
    if not isinstance(ingredient_id, str) or not ingredient_id.strip():
        raise ValueError('ingredient required')
    if type(revision) is not int or revision < 1:
        raise ValueError('positive integer revision required')
    if status not in ('approved', 'revoked'):
        raise ValueError('invalid approval status')
    for value in (mg_per_ml_numerator, mg_per_ml_denominator):
        if type(value) is not int or value <= 0:
            raise ValueError('positive integer ratio required')
    with db:
        current = db.execute("""SELECT MAX(revision) FROM ingredient_density_revisions
                                WHERE venue_id=? AND ingredient_id=?""",
                             (authorized_venue, ingredient_id)).fetchone()[0]
        if revision != (current or 0) + 1:
            raise ValueError('revision must be consecutive')
        db.execute('INSERT INTO ingredient_density_revisions VALUES (?,?,?,?,?,?)',
                   (authorized_venue, ingredient_id, revision, status,
                    mg_per_ml_numerator, mg_per_ml_denominator))


def latest_approved_density(db, *, authorized_venue, ingredient_id):
    if not isinstance(authorized_venue, str) or not authorized_venue.strip():
        raise ValueError('trusted venue required')
    if not isinstance(ingredient_id, str) or not ingredient_id.strip():
        raise ValueError('ingredient required')
    row = db.execute("""SELECT revision,status,mg_per_ml_numerator,mg_per_ml_denominator
                        FROM ingredient_density_revisions
                        WHERE venue_id=? AND ingredient_id=?
                        ORDER BY revision DESC LIMIT 1""",
                     (authorized_venue, ingredient_id)).fetchone()
    if row is None or row[1] != 'approved':
        return None
    return dict(venue_id=authorized_venue, ingredient_id=ingredient_id,
                revision=row[0], status=row[1], mg_per_ml_numerator=row[2],
                mg_per_ml_denominator=row[3])
