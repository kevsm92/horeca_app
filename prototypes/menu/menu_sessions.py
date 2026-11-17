"""Server-owned opaque-session resolver for the unhosted menu WSGI API.

Authentication and provisioning are out of scope. Never accept a client-supplied
venue or role. Only token SHA-256 digests are persisted, not raw session tokens.
"""
import hashlib
import time
from http.cookies import SimpleCookie, CookieError

SCHEMA = """
CREATE TABLE IF NOT EXISTS menu_sessions (
 token_digest TEXT PRIMARY KEY CHECK(length(token_digest)=64),
 venue_id TEXT NOT NULL CHECK(length(trim(venue_id))>0),
 expires_at INTEGER NOT NULL,
 revoked_at INTEGER,
 can_read_menu INTEGER NOT NULL CHECK(can_read_menu IN (0,1))
);
"""

def initialize_sessions(db):
    db.executescript(SCHEMA)

def resolve_menu_session(db, environ, *, now=None):
    """Resolve a preexisting authenticated session; fail closed on malformed cookies."""
    raw = environ.get('HTTP_COOKIE', '')
    if not isinstance(raw, str) or len(raw) > 4096:
        return None
    try:
        cookies = SimpleCookie()
        cookies.load(raw)
        morsel = cookies.get('horeca_session')
        if morsel is None:
            return None
        token = morsel.value
    except (CookieError, ValueError, TypeError):
        return None
    # A future login service must issue 32 cryptographically random bytes as hex.
    if len(token) != 64 or any(c not in '0123456789abcdef' for c in token):
        return None
    digest = hashlib.sha256(bytes.fromhex(token)).hexdigest()
    row = db.execute('SELECT venue_id, expires_at, revoked_at, can_read_menu '
                     'FROM menu_sessions WHERE token_digest=?', (digest,)).fetchone()
    if row is None:
        return None
    current = int(time.time()) if now is None else int(now)
    if row[2] is not None or row[1] <= current:
        return None
    venue = row[0]
    if not isinstance(venue, str) or not venue.strip():
        return None
    return {'venue_id': venue, 'permissions': {'menu:read'} if row[3] == 1 else set()}

def provision_test_session(db, *, token_hex, venue_id, expires_at, can_read_menu=True):
    """TEST FIXTURE ONLY. Never expose as a web endpoint or production login."""
    if len(token_hex) != 64 or any(c not in '0123456789abcdef' for c in token_hex):
        raise ValueError('invalid fixture token')
    digest = hashlib.sha256(bytes.fromhex(token_hex)).hexdigest()
    with db:
        db.execute('INSERT INTO menu_sessions VALUES (?,?,?,?,?)',
                   (digest, venue_id, expires_at, None, int(can_read_menu)))
