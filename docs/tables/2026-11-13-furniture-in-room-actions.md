# In-room furniture placement approval and removal — 2026-11-13

The floor-plan editor shows **clickable controls above each table**. Newly placed tables are a temporary preview: green **✓** approves/saves the placement and red **×** discards it without creating a revision. Saved tables show a red **×**, which directly removes that placement (and writes a new revision); it does not delete physical table inventory. The existing sidebar placement and removal flows remain available.

Draft coordinates stay separate from persisted `positions` until approval. Preview tables may be adjusted with arrow keys or pointer dragging, without saving. Approval checks the existing optimistic revision and preserves the pending preview if browser storage fails. A conflicting revision loads the latest layout rather than overriding it. Venue switches and incoming cross-tab storage events discard the unsaved preview. Toolbar actions are separate sibling buttons, never nested inside table buttons, and have accessible labels.

Run `node --test tests/tables/furniture-in-room-actions.test.cjs`. Test with synthetic tables only. There is no backend/table-service integration, and the UI does not prove real venue safety or seating capacity. €0 extra spending; no deployment.
