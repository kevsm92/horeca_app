# Legacy Tables UI visual consolidation (2026-11-13)

The three offline prototypes in `prototypes/tables` (navigation, fixed seating floor plan, service/layout studio) share a local `horeca-ui.css` based on the styles in `2026-11-13-reference-redesign.html`. The stylesheet adds scoped overrides for older markup. The new editor stays untouched.

Unified elements: violet storefront branding, white header, slate typography, purple selection controls, panels and cards, table appearance, keyboard focus, grid and responsive layouts. The older Studio Service/Design visibility bug is resolved using `[hidden]{display:none!important}`, and the presence of `aria-current` highlights its active mode.

The legacy JavaScript, physical table IDs and synthetic seating semantics are not changed. These remain independent offline mock pages, **not** one authenticated production app and not connected to live venue data.

Tests: `node --test tests/tables/legacy-ui-design-consistency.test.cjs`. Browser smoke: Chromium 1440×900 and 390×844, Tables tab, Seat, service/design toggle, template choice, inventory placement; check console errors and horizontal overflow.

Pending: integrate the actual Tables workflow with a single venue-scoped router and authorized backend. No deployment, billable services, real customers or transactions. Cost €0.
