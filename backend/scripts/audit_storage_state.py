"""
Utility script executed through `python manage.py shell < backend/scripts/audit_storage_state.py`
to provide a snapshot of storage box consistency.
"""

from __future__ import annotations

import json
import re
from collections import Counter

from storage_management.models import StorageBox, Storage
from storage_management.utils import label_to_row_index


def parse_cell_id(cell_id: str) -> tuple[int | None, int | None]:
    """Return (row_index, col_index) for spreadsheet-style IDs like A1, AA10."""
    match = re.match(r"^([A-Z]+)(\d+)$", cell_id or "")
    if not match:
        return None, None
    row_label, col_digits = match.groups()
    row_index = label_to_row_index(row_label)
    try:
        col_index = int(col_digits)
    except ValueError:
        return row_index, None
    return row_index, col_index


def main() -> None:
    print("storage_audit: start")
    box_meta = {box.box_id: box for box in StorageBox.objects.all()}
    box_ids_from_storage = set(
        Storage.objects.order_by().values_list("box_id", flat=True).distinct()
    )
    all_box_ids = sorted(set(box_meta) | box_ids_from_storage, key=lambda x: (len(str(x)), str(x)))

    report = []

    for box_id in all_box_ids:
        storage_qs = Storage.objects.filter(box_id=box_id).values_list("cell_id", flat=True)
        cell_ids = list(storage_qs)
        unique_cells = list(dict.fromkeys(cell_ids))  # preserve order, drop duplicates
        duplicates = Counter(cell_ids)
        duplicate_cells = sorted(
            [
                {"cell_id": cid, "count": count}
                for cid, count in duplicates.items()
                if count > 1
            ],
            key=lambda item: item["cell_id"],
        )

        max_row = 0
        max_col = 0
        parse_errors = 0
        for cid in unique_cells:
            row_idx, col_idx = parse_cell_id(cid)
            if row_idx is None or col_idx is None:
                parse_errors += 1
                continue
            max_row = max(max_row, row_idx)
            max_col = max(max_col, col_idx)

        inferred_total = max_row * max_col if max_row and max_col else None

        meta = box_meta.get(box_id)
        meta_rows = meta.rows if meta else None
        meta_cols = meta.cols if meta else None
        expected_by_meta = (
            (meta_rows or 0) * (meta_cols or 0) if meta_rows and meta_cols else None
        )

        actual_unique = len(unique_cells)
        duplicates_count = sum(count - 1 for count in duplicates.values())

        missing_cells_sample = []
        missing_cells_total = 0
        expected_total = expected_by_meta or inferred_total
        if expected_total and expected_total > actual_unique:
            missing_cells_total = expected_total - actual_unique
            limit = 10
            # Only attempt to list missing cells when we know the geometry
            target_rows = meta_rows or max_row
            target_cols = meta_cols or max_col
            seen = set(unique_cells)
            if target_rows and target_cols and target_rows * target_cols <= 1000:
                for r in range(1, target_rows + 1):
                    # convert index to label
                    label = ""
                    n = r
                    while n > 0:
                        n, rem = divmod(n - 1, 26)
                        label = chr(65 + rem) + label
                    for c in range(1, target_cols + 1):
                        cid = f"{label}{c}"
                        if cid not in seen:
                            missing_cells_sample.append(cid)
                            if len(missing_cells_sample) >= limit:
                                break
                    if len(missing_cells_sample) >= limit:
                        break

        record = {
            "box_id": box_id,
            "has_meta": bool(meta),
            "meta_rows": meta_rows,
            "meta_cols": meta_cols,
            "actual_entries": len(cell_ids),
            "actual_unique_cells": actual_unique,
            "expected_by_meta": expected_by_meta,
            "inferred_total": inferred_total,
            "duplicates": duplicate_cells,
            "duplicates_count": duplicates_count,
            "parse_errors": parse_errors,
            "missing_cells_total": missing_cells_total,
            "missing_cells_sample": missing_cells_sample,
        }
        report.append(record)

    totals = {
        "boxes_with_meta": sum(1 for item in report if item["has_meta"]),
        "boxes_without_meta": sum(1 for item in report if not item["has_meta"]),
        "total_storage_records": Storage.objects.count(),
        "total_unique_boxes": len(all_box_ids),
    }

    output = {
        "totals": totals,
        "boxes": report,
    }

    # Dump as pretty JSON for easier downstream processing
    print(json.dumps(output, ensure_ascii=False, indent=2))


main()
