# Floor-plan keyboard cancellation — 2026-11-13, 23:00 Europe/Brussels

Escape on a focused, unapproved furniture preview discards it without saving a revision and returns focus to another selected table when available. Delete/Backspace retain their existing removal action. This supplements the previously implemented green checkmark and red cross; sidebar controls remain unchanged.

Verified: JavaScript syntax compiled, and four isolated keyboard checks passed (Escape pending, Escape saved, unrelated key, Delete). Browser DOM interaction and cross-tab behaviour have not been tested in a browser. Synthetic data only; no deployment or paid services.

Next dependency: browser keyboard/pointer accessibility checks; then November 14 numeric visual dimensions and physical seating limits.
