from __future__ import annotations

from typing import Iterable

from django.db import transaction

from .models import Storage, StorageBox


def row_index_to_label(index: int) -> str:
    """Return spreadsheet-style row label (1 -> A, 27 -> AA)."""
    label = ''
    current = index
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        label = chr(65 + remainder) + label
    return label or 'A'


def label_to_row_index(label: str) -> int:
    """Convert spreadsheet-style row label to index (A -> 1, AA -> 27)."""
    total = 0
    for ch in label.upper():
        if 'A' <= ch <= 'Z':
            total = total * 26 + (ord(ch) - 64)
        else:
            break
    return total


def ensure_storage_cells(box_id: str, rows: int, cols: int) -> int:
    """
    Make sure all cells for a storage box exist.

    Returns the number of cells created during the call.
    """
    if rows <= 0 or cols <= 0:
        return 0

    existing_cells = set(
        Storage.objects.filter(box_id=box_id).values_list('cell_id', flat=True)
    )

    cells_to_create = []
    for row_idx in range(1, rows + 1):
        row_label = row_index_to_label(row_idx)
        for col_idx in range(1, cols + 1):
            cell_id = f"{row_label}{col_idx}"
            if cell_id not in existing_cells:
                cells_to_create.append(Storage(box_id=box_id, cell_id=cell_id))

    if not cells_to_create:
        return 0

    with transaction.atomic():
        Storage.objects.bulk_create(
            cells_to_create,
            batch_size=1000,
            ignore_conflicts=True,
        )

    return len(cells_to_create)


def ensure_cells_for_boxes(boxes: Iterable[StorageBox]) -> int:
    """
    Ensure all boxes in the iterable have their cell grids generated.

    Returns the total number of cells created across all boxes.
    """
    created_total = 0
    for box in boxes:
        if not box.rows or not box.cols:
            continue
        created_total += ensure_storage_cells(box.box_id, box.rows, box.cols)
    return created_total
