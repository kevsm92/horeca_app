# 2026-11-12 — Tables tab keyboard and status accessibility contract (increment 11)

Scope: offline, synthetic-data accessibility acceptance criteria for the existing `prototypes/tables/2026-11-12-floorplan.html`. This is a distinct keyboard/status review, not a claim of deployed UI or a new seating backend.

## Verified source observations
- Primary navigation contains separate Overview and Tables buttons; Tables content starts hidden.
- Each physical table is rendered as a native button with an occupancy-and-capacity accessible label and `aria-pressed` reflecting selection.
- Seat button and guest input are disabled until a table is selected; both are disabled for occupied tables.
- A `role=status`, `aria-live=polite` message reports the mock seat outcome.
- The prototype uses only in-memory fictional inventory; reload discards seating changes.

## Acceptance scenarios for future browser tests
1. From Overview, keyboard Tab to Tables, Enter: Tables heading, floor plan and seating panel become available; Overview content becomes hidden.
2. Tab to each floor-plan button: accessible name contains physical table ID, status and capacity. Enter selects it and updates selection details.
3. For occupied T3, the guest input and Seat button remain disabled. For available T1, max guest count is 2.
4. Type 0, 1.5, 3, blank and 2 in T1's guest field; only 2 may succeed among these inputs. After success, T1 is occupied and cannot be seated again.
5. Return to Overview and Tables: selected table remains selected during this in-memory session; the occupancy summary is consistent.
6. With screen-reader announcements, avoid relying on color alone; accessible labels and visible text must convey occupied/available state.

## Gaps and follow-ups
- **Not browser-verified**: focus return on tab changes, actual screen-reader announcements, high-zoom/mobile clipping, contrast, and keyboard ordering need real browser/assistive-technology checks.
- Current navigation is buttons with `aria-current`, not a full ARIA tablist. Preserve consistent page-navigation semantics or implement the complete tablist keyboard model; do not mix patterns.
- No authenticated venue-scoped backend exists in this HTML; never present the mock Seat action as a real seating operation.
- Nov 13: movement, persistence and revision checks are separate work; no position editing is implemented here.

No real guest data, external calls, hosting, payments, or spending.
