"""Offline KDS allergen-warning review gate; never certifies allergen safety."""
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class AllergenReview:
    venue_id: str
    ticket_id: str
    revision: int
    declared_allergens: tuple[str, ...]
    actor_id: str
    reviewed_at: str


def review_allergen_warning(*, venue_id: str, actor_venue_id: str, ticket_id: str,
                            revision: int, declared_allergens: tuple[str, ...],
                            actor_id: str, at: datetime) -> AllergenReview:
    """Require explicit human review of a ticket revision before KDS preparation.

    Caller must authenticate and authorize the staff member and persist the review
    with an atomic ticket-revision check. This is not an ingredient verification,
    cross-contact guarantee, or regulatory compliance certificate.
    """
    if not venue_id or venue_id != actor_venue_id:
        raise PermissionError("venue mismatch")
    if not ticket_id.strip() or not actor_id.strip():
        raise ValueError("ticket and actor required")
    if type(revision) is not int or revision < 0:
        raise ValueError("invalid ticket revision")
    if not isinstance(declared_allergens, tuple) or not declared_allergens or any(
        not isinstance(x, str) or not x.strip() for x in declared_allergens
    ):
        raise ValueError("explicit allergen warnings required")
    if len(set(declared_allergens)) != len(declared_allergens):
        raise ValueError("duplicate warnings")
    if not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("timezone-aware review timestamp required")
    return AllergenReview(venue_id, ticket_id, revision, declared_allergens,
                          actor_id, at.astimezone(timezone.utc).isoformat())


def review_matches_ticket(review: AllergenReview, *, venue_id: str, ticket_id: str,
                          revision: int, declared_allergens: tuple[str, ...]) -> bool:
    """Fail closed if a ticket is edited or its allergen warning set changes."""
    return (review.venue_id == venue_id and review.ticket_id == ticket_id
            and type(revision) is int and review.revision == revision
            and review.declared_allergens == declared_allergens)
