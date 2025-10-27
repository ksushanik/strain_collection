from __future__ import annotations

import json
import re
from typing import Iterable, Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count

from storage_management.models import Storage, StorageBox
from storage_management.utils import ensure_storage_cells, label_to_row_index


CELL_ID_PATTERN = re.compile(r"^([A-Z]+)(\d+)$")


def parse_cell_id(cell_id: str) -> tuple[Optional[int], Optional[int]]:
    match = CELL_ID_PATTERN.match(cell_id or "")
    if not match:
        return None, None
    row_label, col_digits = match.groups()
    row_index = label_to_row_index(row_label)
    try:
        col_index = int(col_digits)
    except (TypeError, ValueError):
        return row_index, None
    return row_index, col_index


class Command(BaseCommand):
    help = (
        "Ensure that StorageBox metadata exists for every box present in Storage, "
        "update rows/cols if missing, remove duplicate cells and generate absent cells."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--box",
            action="append",
            dest="boxes",
            help="Limit processing to the given box_id (can be provided multiple times).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Do not mutate data; output the planned changes as JSON.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            dest="as_json",
            help="Output summary as JSON (useful for scripting).",
        )

    def handle(self, *args, **options):
        boxes_filter: Optional[list[str]] = options.get("boxes")
        dry_run: bool = options.get("dry_run", False)
        as_json: bool = options.get("as_json", False)

        box_ids = self._collect_box_ids(boxes_filter)
        if not box_ids:
            raise CommandError("No boxes found for the provided filters.")

        summary = []

        for box_id in box_ids:
            report = self._process_box(box_id, dry_run=dry_run)
            summary.append(report)

        output = {
            "dry_run": dry_run,
            "processed_boxes": len(summary),
            "changes": summary,
        }

        if as_json:
            self.stdout.write(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            for item in summary:
                status = "OK"
                if item["created_box"] or item["updated_box"] or item["duplicates_removed"] or item["cells_created"]:
                    status = "UPDATED"
                elif item["errors"]:
                    status = "ERROR"
                self.stdout.write(
                    f"[{status}] box={item['box_id']} "
                    f"created_box={item['created_box']} "
                    f"updated_box={item['updated_box']} "
                    f"duplicates_removed={item['duplicates_removed']} "
                    f"cells_created={item['cells_created']} "
                    f"errors={item['errors']}"
                )

    def _collect_box_ids(self, boxes_filter: Optional[Iterable[str]]) -> list[str]:
        storage_box_ids = Storage.objects.values_list("box_id", flat=True).distinct()
        meta_box_ids = StorageBox.objects.values_list("box_id", flat=True).distinct()

        combined = set(storage_box_ids) | set(meta_box_ids)

        if boxes_filter:
            combined = {box for box in combined if box in set(boxes_filter)}

        return sorted(combined, key=lambda x: (len(str(x)), str(x)))

    def _process_box(self, box_id: str, *, dry_run: bool) -> dict:
        existing_box = StorageBox.objects.filter(box_id=box_id).first()
        storages = list(Storage.objects.filter(box_id=box_id))

        report = {
            "box_id": box_id,
            "created_box": False,
            "updated_box": False,
            "duplicates_removed": 0,
            "cells_created": 0,
            "meta_rows": existing_box.rows if existing_box else None,
            "meta_cols": existing_box.cols if existing_box else None,
            "inferred_rows": None,
            "inferred_cols": None,
            "errors": [],
        }

        inferred_rows, inferred_cols = self._infer_geometry(storages)
        report["inferred_rows"] = inferred_rows
        report["inferred_cols"] = inferred_cols

        if existing_box is None and not storages:
            report["errors"].append("No storage entries and no metadata; nothing to do.")
            return report

        def apply_changes():
            if existing_box is None:
                if inferred_rows is None or inferred_cols is None:
                    raise CommandError(
                        f"Cannot create StorageBox {box_id}: unable to infer geometry from storage records."
                    )
                new_box = StorageBox.objects.create(
                    box_id=box_id,
                    rows=inferred_rows,
                    cols=inferred_cols,
                )
                report["created_box"] = True
                report["meta_rows"] = new_box.rows
                report["meta_cols"] = new_box.cols
            else:
                updates = {}
                current_rows = existing_box.rows or 0
                current_cols = existing_box.cols or 0
                if inferred_rows and inferred_rows > current_rows:
                    updates["rows"] = inferred_rows
                if inferred_cols and inferred_cols > current_cols:
                    updates["cols"] = inferred_cols
                if updates:
                    for key, value in updates.items():
                        setattr(existing_box, key, value)
                    existing_box.save(update_fields=list(updates.keys()))
                    report["updated_box"] = True
                    report["meta_rows"] = existing_box.rows
                    report["meta_cols"] = existing_box.cols

            duplicates_removed = self._remove_duplicates(box_id)
            report["duplicates_removed"] = duplicates_removed

            box = StorageBox.objects.filter(box_id=box_id).first()
            if box and box.rows and box.cols:
                created = ensure_storage_cells(box.box_id, box.rows, box.cols)
                report["cells_created"] = created

        if dry_run:
            with transaction.atomic():
                apply_changes()
                transaction.set_rollback(True)
        else:
            apply_changes()

        return report

    def _infer_geometry(self, storages: list[Storage]) -> tuple[Optional[int], Optional[int]]:
        max_row = 0
        max_col = 0
        for storage in storages:
            row_idx, col_idx = parse_cell_id(storage.cell_id)
            if row_idx is None or col_idx is None:
                continue
            max_row = max(max_row, row_idx)
            max_col = max(max_col, col_idx)
        inferred_rows = max_row or None
        inferred_cols = max_col or None
        return inferred_rows, inferred_cols

    def _remove_duplicates(self, box_id: str) -> int:
        duplicates = (
            Storage.objects.filter(box_id=box_id)
            .values("cell_id")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
        )

        removed = 0
        for dup in duplicates:
            cell_id = dup["cell_id"]
            entries = list(
                Storage.objects.filter(box_id=box_id, cell_id=cell_id).order_by("id")
            )
            if not entries:
                continue
            keeper = entries[0]
            to_delete_ids = [entry.id for entry in entries[1:]]
            if to_delete_ids:
                Storage.objects.filter(id__in=to_delete_ids).delete()
                removed += len(to_delete_ids)
                self.stdout.write(
                    f"Removed duplicates for box={box_id} cell={cell_id}; kept id={keeper.id}"
                )

        return removed
