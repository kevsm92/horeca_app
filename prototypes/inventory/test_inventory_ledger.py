"""Expose embedded inventory ledger regressions to unittest discovery.

Run from repository root:
    python -m unittest discover -s prototypes/inventory -p 'test_*.py' -v

The ledger itself is intentionally import-safe and can still be run directly.
"""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    'inventory_ledger', Path(__file__).with_name('inventory_ledger.py')
)
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)

LedgerTests = ledger.LedgerTests
