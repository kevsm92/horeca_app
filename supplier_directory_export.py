"""Offline, tenant-scoped supplier SKU CSV preview; no network or purchasing."""
import csv
import io
from supplier_directory import list_skus

HEADERS = ('supplier_id', 'supplier_name', 'sku', 'unit', 'pack_quantity', 'price_cents', 'lead_days')


def export_supplier_skus_csv(db, venue_id, ingredient_id):
    """Export active suppliers for one venue/ingredient, neutralizing CSV formula cells."""
    if not isinstance(venue_id, str) or not venue_id.strip():
        raise ValueError('venue_id must be nonempty text')
    if not isinstance(ingredient_id, str) or not ingredient_id.strip():
        raise ValueError('ingredient_id must be nonempty text')
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\r\n')
    writer.writerow(HEADERS)
    for row in list_skus(db, venue_id, ingredient_id):
        writer.writerow([_safe_cell(value) for value in row])
    return output.getvalue()


def _safe_cell(value):
    if isinstance(value, str) and value.lstrip(' \t\r\n').startswith(('=', '+', '-', '@')):
        return "'" + value
    return value
