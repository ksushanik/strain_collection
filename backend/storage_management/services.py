from __future__ import annotations

from collections import OrderedDict
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from django.db import IntegrityError, transaction
from django.db.models import Prefetch

from collection_manager.utils import generate_batch_id
from sample_management.models import Sample, SampleStorageAllocation

from .models import Storage, StorageBox
from .utils import ensure_cells_for_boxes, label_to_row_index


@dataclass
class ServiceLogEntry:
    """Descriptor for a change that should be persisted via log_change on the API layer."""

    content_type: str
    object_id: int
    action: str
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]
    comment: str
    batch_id: Optional[str] = None

    def as_kwargs(self) -> Dict[str, Any]:
        data = {
            "content_type": self.content_type,
            "object_id": self.object_id,
            "action": self.action,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "comment": self.comment,
        }
        if self.batch_id:
            data["batch_id"] = self.batch_id
        return data


@dataclass
class ServiceResult:
    payload: Dict[str, Any]
    logs: List[ServiceLogEntry]


class StorageServiceError(Exception):
    """Domain level error that carries http status, code and payload details."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        code: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.extra = extra or {}

    def as_response(self) -> Dict[str, Any]:
        data = {"error": self.message}
        if self.code:
            data["error_code"] = self.code
        data.update(self.extra)
        return data


def _get_storage_cell_for_update(box_id: str, cell_id: str) -> Storage:
    try:
        return (
            Storage.objects.select_for_update()
            .select_related()
            .get(box_id=box_id, cell_id=cell_id)
        )
    except Storage.DoesNotExist as exc:
        raise StorageServiceError(
            message=f"Ячейка {cell_id} в боксе {box_id} не найдена",
            status_code=404,
            code="STORAGE_NOT_FOUND",
        ) from exc


def _get_sample_for_update(sample_id: int) -> Sample:
    try:
        return (
            Sample.objects.select_for_update()
            .get(id=sample_id)
        )
    except Sample.DoesNotExist as exc:
        raise StorageServiceError(
            message=f"Образец с ID {sample_id} не найден",
            status_code=404,
            code="SAMPLE_NOT_FOUND",
        ) from exc


def assign_primary_cell(
    *,
    sample_id: int,
    box_id: str,
    cell_id: str,
    batch_id: Optional[str] = None,
) -> ServiceResult:
    with transaction.atomic():
        storage_cell = _get_storage_cell_for_update(box_id, cell_id)
        sample = _get_sample_for_update(sample_id)

        existing_sample = (
            Sample.objects.select_for_update()
            .filter(storage=storage_cell)
            .order_by("id")
            .first()
        )
        if existing_sample:
            raise StorageServiceError(
                message=f"Ячейка {cell_id} уже занята образцом ID {existing_sample.id}",
                status_code=409,
                code="CELL_OCCUPIED_LEGACY",
                extra={
                    "occupied_by": {
                        "sample_id": existing_sample.id,
                        "strain_code": existing_sample.strain.short_code
                        if existing_sample.strain
                        else None,
                    },
                    "recommended_endpoint": f"/api/storage/boxes/{box_id}/cells/{cell_id}/clear/",
                    "recommended_method": "DELETE",
                },
            )

        existing_alloc = (
            SampleStorageAllocation.objects.select_for_update()
            .filter(storage=storage_cell)
            .order_by("id")
            .first()
        )
        if existing_alloc:
            sample_alloc = existing_alloc.sample
            raise StorageServiceError(
                message=f"Ячейка {cell_id} уже занята образцом ID {sample_alloc.id}",
                status_code=409,
                code="CELL_OCCUPIED_ALLOCATION",
                extra={
                    "occupied_by": {
                        "sample_id": sample_alloc.id,
                        "strain_code": sample_alloc.strain.short_code
                        if sample_alloc.strain
                        else None,
                    },
                    "recommended_endpoint": f"/api/storage/boxes/{box_id}/cells/{cell_id}/unallocate/",
                    "recommended_method": "DELETE",
                    "recommended_payload": {"sample_id": sample_alloc.id},
                },
            )

        if (
            SampleStorageAllocation.objects.select_for_update()
            .filter(sample=sample)
            .exists()
        ):
            raise StorageServiceError(
                message=(
                    f"Образец {sample.id} уже участвует в allocations. "
                    "Используйте allocate_cell с флагом is_primary, чтобы задать первичную ячейку."
                ),
                status_code=409,
                code="LEGACY_ASSIGN_BLOCKED",
                extra={
                    "recommended_endpoint": f"/api/storage/boxes/{box_id}/cells/{cell_id}/allocate/",
                    "recommended_method": "POST",
                    "recommended_payload": {"sample_id": sample.id, "is_primary": True},
                },
            )

        if sample.storage_id is not None:
            raise StorageServiceError(
                message=(
                    f"Образец уже размещен в ячейке {sample.storage.cell_id} "
                    f"бокса {sample.storage.box_id}"
                ),
                status_code=409,
                code="SAMPLE_ALREADY_PLACED",
                extra={
                    "current_location": {
                        "box_id": sample.storage.box_id,
                        "cell_id": sample.storage.cell_id,
                    },
                    "recommended_endpoint": f"/api/storage/boxes/{sample.storage.box_id}/cells/{sample.storage.cell_id}/clear/",
                    "recommended_method": "DELETE",
                },
            )

        old_storage = sample.storage
        try:
            sample.storage = storage_cell
            sample.save(update_fields=["storage"])
        except IntegrityError as exc:
            raise StorageServiceError(
                message=(
                    "Конфликт сохранения образца: выбранная ячейка уже занята или "
                    "образец закреплён за другой ячейкой."
                ),
                status_code=409,
                code="ASSIGN_CONFLICT",
                extra={
                    "details": str(exc),
                    "box_id": box_id,
                    "cell_id": cell_id,
                    "sample_id": sample.id,
                },
            ) from exc

        log_entry = ServiceLogEntry(
            content_type="sample",
            object_id=sample.id,
            action="UPDATE",
            old_values={
                "previous_box_id": old_storage.box_id if old_storage else None,
                "previous_cell_id": old_storage.cell_id if old_storage else None,
                "previous_storage_id": old_storage.id if old_storage else None,
            },
            new_values={
                "box_id": storage_cell.box_id,
                "cell_id": storage_cell.cell_id,
                "storage_id": storage_cell.id,
            },
            comment="Assign cell: sample placed into storage cell",
            batch_id=batch_id,
        )

        payload = {
            "assignment": {
                "sample_id": sample.id,
                "box_id": storage_cell.box_id,
                "cell_id": storage_cell.cell_id,
                "strain_code": sample.strain.short_code if sample.strain else None,
            }
        }
        return ServiceResult(payload=payload, logs=[log_entry])


def clear_storage_cell(
    *,
    box_id: str,
    cell_id: str,
    batch_id: Optional[str] = None,
) -> ServiceResult:
    with transaction.atomic():
        storage_cell = _get_storage_cell_for_update(box_id, cell_id)

        allocation = (
            SampleStorageAllocation.objects.select_for_update()
            .filter(storage=storage_cell)
            .order_by("id")
            .first()
        )

        if allocation:
            sample = allocation.sample
            was_primary = allocation.is_primary
            allocation.delete()

            if was_primary and sample.storage_id == storage_cell.id:
                sample.storage = None
                sample.save(update_fields=["storage"])

            log_entry = ServiceLogEntry(
                content_type="sample",
                object_id=sample.id,
                action="UPDATE",
                old_values={
                    "previous_box_id": storage_cell.box_id,
                    "previous_cell_id": storage_cell.cell_id,
                    "previous_storage_id": storage_cell.id,
                },
                new_values={
                    "box_id": None if was_primary else (sample.storage.box_id if sample.storage else None),
                    "cell_id": None if was_primary else (sample.storage.cell_id if sample.storage else None),
                    "storage_id": None if was_primary else (sample.storage.id if sample.storage else None),
                },
                comment="Clear cell: allocation removed from storage cell",
                batch_id=batch_id,
            )

            payload = {
                "freed_sample": {
                    "sample_id": sample.id,
                    "strain_code": sample.strain.short_code if sample.strain else None,
                }
            }
            return ServiceResult(payload=payload, logs=[log_entry])

        sample = (
            Sample.objects.select_for_update()
            .filter(storage=storage_cell)
            .order_by("id")
            .first()
        )

        if not sample:
            raise StorageServiceError(
                message=f"Ячейка {cell_id} уже свободна",
                status_code=409,
                code="CELL_ALREADY_FREE",
            )

        old_storage = sample.storage
        sample.storage = None
        sample.save(update_fields=["storage"])

        log_entry = ServiceLogEntry(
            content_type="sample",
            object_id=sample.id,
            action="UPDATE",
            old_values={
                "previous_box_id": old_storage.box_id if old_storage else None,
                "previous_cell_id": old_storage.cell_id if old_storage else None,
                "previous_storage_id": old_storage.id if old_storage else None,
            },
            new_values={
                "box_id": None,
                "cell_id": None,
                "storage_id": None,
            },
            comment="Clear cell: sample removed from storage cell",
            batch_id=batch_id,
        )

        payload = {
            "freed_sample": {
                "sample_id": sample.id,
                "strain_code": sample.strain.short_code if sample.strain else None,
            }
        }
        return ServiceResult(payload=payload, logs=[log_entry])


def allocate_sample_to_cell(
    *,
    sample_id: int,
    box_id: str,
    cell_id: str,
    is_primary: bool,
    batch_id: Optional[str] = None,
) -> ServiceResult:
    with transaction.atomic():
        storage_cell = _get_storage_cell_for_update(box_id, cell_id)
        sample = _get_sample_for_update(sample_id)

        legacy_occupied = (
            Sample.objects.select_for_update()
            .filter(storage=storage_cell)
            .order_by("id")
            .first()
        )
        if legacy_occupied and legacy_occupied.id != sample.id:
            raise StorageServiceError(
                message=(
                    f"Ячейка {cell_id} уже занята образцом ID {legacy_occupied.id} (legacy). "
                    "Очистите её перед добавлением allocation."
                ),
                status_code=409,
                code="LEGACY_CELL_OCCUPIED",
            )

        existing_alloc = (
            SampleStorageAllocation.objects.select_for_update()
            .filter(storage=storage_cell)
            .order_by("id")
            .first()
        )
        if existing_alloc and existing_alloc.sample_id != sample.id:
            raise StorageServiceError(
                message="Ячейка уже занята другим allocation",
                status_code=400,
                code="ALLOCATION_OCCUPIED",
                extra={"occupied_by": existing_alloc.sample_id},
            )

        alloc, created = SampleStorageAllocation.objects.get_or_create(
            sample=sample,
            storage=storage_cell,
            defaults={"is_primary": is_primary},
        )

        old_primary_storage_id = None
        if is_primary:
            previous_primary = (
                SampleStorageAllocation.objects.select_for_update()
                .filter(sample=sample, is_primary=True)
                .exclude(id=alloc.id)
            )
            if previous_primary.exists():
                old_primary_storage_id = previous_primary.first().storage_id
                previous_primary.update(is_primary=False)

        if not created and is_primary and not alloc.is_primary:
            alloc.is_primary = True
            alloc.save(update_fields=["is_primary"])

        old_storage = sample.storage if is_primary else None
        if is_primary:
            sample.storage = storage_cell
            sample.save(update_fields=["storage"])

        log_entry = ServiceLogEntry(
            content_type="sample",
            object_id=sample.id,
            action="UPDATE",
            old_values={
                "previous_primary_storage_id": old_primary_storage_id,
                "previous_storage_id": old_storage.id if old_storage else None,
            },
            new_values={
                "box_id": storage_cell.box_id,
                "cell_id": storage_cell.cell_id,
                "storage_id": storage_cell.id,
                "allocation_primary": alloc.is_primary,
            },
            comment="Allocate sample to cell (multi-cell support)",
            batch_id=batch_id,
        )

        payload = {
            "allocation": {
                "sample_id": sample.id,
                "box_id": storage_cell.box_id,
                "cell_id": storage_cell.cell_id,
                "storage_id": storage_cell.id,
                "is_primary": alloc.is_primary,
                "created": created,
            }
        }
        return ServiceResult(payload=payload, logs=[log_entry])


def unallocate_sample_from_cell(
    *,
    sample_id: int,
    box_id: str,
    cell_id: str,
    batch_id: Optional[str] = None,
) -> ServiceResult:
    with transaction.atomic():
        storage_cell = _get_storage_cell_for_update(box_id, cell_id)
        sample = _get_sample_for_update(sample_id)

        alloc = (
            SampleStorageAllocation.objects.select_for_update()
            .filter(sample=sample, storage=storage_cell)
            .order_by("id")
            .first()
        )
        if not alloc:
            raise StorageServiceError(
                message="Соответствующее allocation не найдено",
                status_code=404,
                code="ALLOCATION_NOT_FOUND",
            )

        was_primary = alloc.is_primary
        alloc.delete()

        old_storage_id = sample.storage_id
        if was_primary and sample.storage_id == storage_cell.id:
            sample.storage = None
            sample.save(update_fields=["storage"])

        log_entry = ServiceLogEntry(
            content_type="sample",
            object_id=sample.id,
            action="UPDATE",
            old_values={
                "previous_storage_id": old_storage_id,
            },
            new_values={
                "box_id": box_id,
                "cell_id": cell_id,
                "storage_id": None,
                "allocation_removed": True,
                "removed_was_primary": was_primary,
            },
            comment="Unallocate sample from cell (multi-cell support)",
            batch_id=batch_id,
        )

        payload = {
            "unallocation": {
                "sample_id": sample.id,
                "box_id": box_id,
                "cell_id": cell_id,
                "was_primary": was_primary,
            }
        }
        return ServiceResult(payload=payload, logs=[log_entry])


def build_storage_snapshot(box_ids: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    """Return ordered list of boxes with cell snapshots and aggregate totals."""
    normalized_ids: Optional[List[str]] = None
    if box_ids is not None:
        normalized = {str(box).strip().upper() for box in box_ids if str(box).strip()}
        normalized_ids = sorted(normalized)
        if not normalized_ids:
            return {
                "boxes": [],
                "box_map": {},
                "totals": {"total_boxes": 0, "total_cells": 0, "occupied_cells": 0, "free_cells": 0},
            }

    boxes_qs = StorageBox.objects.all()
    if normalized_ids is not None:
        boxes_qs = boxes_qs.filter(box_id__in=normalized_ids)

    meta_boxes = list(boxes_qs)
    meta_map = {box.box_id: box for box in meta_boxes}

    if meta_boxes:
        ensure_cells_for_boxes(meta_boxes)

    storages_qs = Storage.objects.all()
    if normalized_ids is not None:
        storages_qs = storages_qs.filter(box_id__in=normalized_ids)

    storages = list(
        storages_qs.prefetch_related(
            Prefetch("sample_set", queryset=Sample.objects.select_related("strain")),
            Prefetch("allocations", queryset=SampleStorageAllocation.objects.select_related("sample__strain")),
        )
    )

    box_map: Dict[str, Dict[str, Any]] = {}

    for storage in storages:
        box_state = box_map.setdefault(
            storage.box_id,
            {
                "box_id": storage.box_id,
                "rows": meta_map.get(storage.box_id).rows if storage.box_id in meta_map else None,
                "cols": meta_map.get(storage.box_id).cols if storage.box_id in meta_map else None,
                "description": meta_map.get(storage.box_id).description if storage.box_id in meta_map else None,
                "cells": OrderedDict(),
            },
        )
        cell_snapshot = _serialize_storage_cell(storage)
        existing = box_state["cells"].get(storage.cell_id)
        if existing is None:
            box_state["cells"][storage.cell_id] = cell_snapshot
        else:
            box_state["cells"][storage.cell_id] = _merge_cell_snapshots(existing, cell_snapshot)

    for box_id, meta_box in meta_map.items():
        box_state = box_map.setdefault(
            box_id,
            {
                "box_id": box_id,
                "rows": meta_box.rows,
                "cols": meta_box.cols,
                "description": meta_box.description,
                "cells": OrderedDict(),
            },
        )
        if box_state.get("rows") is None:
            box_state["rows"] = meta_box.rows
        if box_state.get("cols") is None:
            box_state["cols"] = meta_box.cols
        if box_state.get("description") is None:
            box_state["description"] = meta_box.description

    ordered_ids = sorted(box_map.keys(), key=_box_sort_key)
    totals = {"total_boxes": len(ordered_ids), "total_cells": 0, "occupied_cells": 0, "free_cells": 0}
    ordered_boxes: List[Dict[str, Any]] = []

    for box_id in ordered_ids:
        box_state = box_map[box_id]
        _finalize_box_state(box_state)
        stats = box_state["stats"]
        totals["total_cells"] += stats["total_cells"]
        totals["occupied_cells"] += stats["occupied_cells"]
        totals["free_cells"] += stats["free_cells"]
        ordered_boxes.append(box_state)

    return {"boxes": ordered_boxes, "box_map": box_map, "totals": totals}


def _serialize_storage_cell(storage: Storage) -> Dict[str, Any]:
    legacy_samples = list(storage.sample_set.all())
    allocations = list(storage.allocations.all())

    legacy_payload = [
        {
            "sample_id": sample.id,
            "strain_id": sample.strain.id if getattr(sample, "strain", None) else None,
            "strain_code": sample.strain.short_code if getattr(sample, "strain", None) else None,
            "comment": getattr(sample, "comment", None),
        }
        for sample in legacy_samples
    ]

    allocations_payload = []
    for alloc in allocations:
        sample = alloc.sample
        allocations_payload.append(
            {
                "allocation_id": alloc.id,
                "sample_id": sample.id if sample else None,
                "is_primary": alloc.is_primary,
                "allocated_at": alloc.allocated_at.isoformat() if getattr(alloc, "allocated_at", None) else None,
                "strain_id": sample.strain.id if sample and getattr(sample, "strain", None) else None,
                "strain_code": sample.strain.short_code if sample and getattr(sample, "strain", None) else None,
                "comment": getattr(sample, "comment", None) if sample else None,
            }
        )

    primary_sample_info = _select_primary_sample(allocations, legacy_samples)
    occupied = bool(primary_sample_info or allocations_payload or legacy_payload)
    sample_ids = {
        *(item["sample_id"] for item in legacy_payload if item.get("sample_id") is not None),
        *(item["sample_id"] for item in allocations_payload if item.get("sample_id") is not None),
    }

    return {
        "storage_id": storage.id,
        "cell_id": storage.cell_id,
        "occupied": occupied,
        "primary_sample": primary_sample_info,
        "allocations": allocations_payload,
        "legacy_samples": legacy_payload,
        "total_samples": len(sample_ids),
    }


def _select_primary_sample(
    allocations: List[SampleStorageAllocation],
    legacy_samples: List[Sample],
) -> Optional[Dict[str, Any]]:
    for alloc in allocations:
        if alloc.is_primary and alloc.sample:
            return _serialize_sample(alloc.sample, source="allocation_primary")
    for alloc in allocations:
        if alloc.sample:
            return _serialize_sample(alloc.sample, source="allocation")
    if legacy_samples:
        return _serialize_sample(legacy_samples[0], source="legacy")
    return None


def _serialize_sample(sample: Sample, *, source: str) -> Dict[str, Any]:
    strain = getattr(sample, "strain", None)
    return {
        "sample_id": sample.id,
        "strain_id": strain.id if strain else None,
        "strain_code": strain.short_code if strain else None,
        "comment": getattr(sample, "comment", None),
        "source": source,
    }


def _merge_cell_snapshots(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    if not existing.get("occupied") and incoming.get("occupied"):
        return incoming

    merged = {**existing}
    merged["allocations"] = _merge_payload_lists(
        existing.get("allocations", []),
        incoming.get("allocations", []),
        key=("allocation_id", "sample_id"),
    )
    merged["legacy_samples"] = _merge_payload_lists(
        existing.get("legacy_samples", []),
        incoming.get("legacy_samples", []),
        key=("sample_id",),
    )

    if merged.get("primary_sample") is None and incoming.get("primary_sample") is not None:
        merged["primary_sample"] = incoming["primary_sample"]

    merged["occupied"] = bool(
        merged.get("primary_sample") or merged["allocations"] or merged["legacy_samples"]
    )
    merged["total_samples"] = len(
        {
            *(item["sample_id"] for item in merged["legacy_samples"] if item.get("sample_id") is not None),
            *(item["sample_id"] for item in merged["allocations"] if item.get("sample_id") is not None),
        }
    )
    return merged


def _merge_payload_lists(
    first: List[Dict[str, Any]],
    second: List[Dict[str, Any]],
    *,
    key: Tuple[str, ...],
) -> List[Dict[str, Any]]:
    seen: Dict[Tuple[Any, ...], Dict[str, Any]] = {}

    def _register(items: List[Dict[str, Any]]) -> None:
        for item in items:
            identifier = tuple(item.get(part) for part in key)
            if identifier not in seen:
                seen[identifier] = item

    _register(first)
    _register(second)
    return list(seen.values())


def _finalize_box_state(box_state: Dict[str, Any]) -> None:
    cells = box_state.get("cells", {})
    rows = box_state.get("rows") or 0
    cols = box_state.get("cols") or 0

    if (rows == 0 or cols == 0) and cells:
        inferred_rows, inferred_cols = _infer_dimensions_from_cells(cells.keys())
        if rows == 0 and inferred_rows:
            rows = inferred_rows
            box_state["rows"] = rows
        if cols == 0 and inferred_cols:
            cols = inferred_cols
            box_state["cols"] = cols

    total_cells = rows * cols if rows and cols else len(cells)
    occupied_cells = sum(1 for cell in cells.values() if cell.get("occupied"))
    free_cells = max(total_cells - occupied_cells, 0)

    box_state["stats"] = {
        "total_cells": total_cells,
        "occupied_cells": occupied_cells,
        "free_cells": free_cells,
    }

    sorted_cells = sorted(cells.values(), key=lambda c: c.get("cell_id"))
    box_state["sorted_cells"] = sorted_cells
    box_state["free_cells_sorted"] = [cell for cell in sorted_cells if not cell.get("occupied")]


CELL_ID_PATTERN = re.compile(r"^([A-Z]+)(\d+)$")

def parse_cell_id(cell_id: str) -> Tuple[Optional[int], Optional[int]]:
    """Parse spreadsheet-style IDs like A1, AA10 into (row_index, col_index)."""
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

def _infer_dimensions_from_cells(cell_ids: Iterable[str]) -> Tuple[int, int]:
    max_row = 0
    max_col = 0
    for cell_id in cell_ids:
        row_idx, col_idx = parse_cell_id(cell_id)
        if row_idx:
            max_row = max(max_row, row_idx)
        if col_idx:
            max_col = max(max_col, col_idx)
    return max_row, max_col


def _box_sort_key(box_id: str) -> Tuple[int, str, str]:
    suffix = ""
    for ch in reversed(str(box_id)):
        if ch.isdigit():
            suffix = ch + suffix
        else:
            break
    if suffix:
        return (0, suffix.zfill(10), str(box_id))
    return (1, str(box_id), str(box_id))


def _format_bulk_assign_error(
    *,
    box_id: str,
    assignment: Dict[str, Any],
    error: StorageServiceError,
) -> str:
    cell_id = assignment["cell_id"]
    sample_id = assignment["sample_id"]
    if error.code == "CELL_OCCUPIED_LEGACY":
        return (
            f"Ячейка {cell_id} уже занята образцом ID {error.extra.get('occupied_by', {}).get('sample_id')}. "
            f"Освободите через DELETE /api/storage/boxes/{box_id}/cells/{cell_id}/clear/"
        )
    if error.code == "CELL_OCCUPIED_ALLOCATION":
        occupied = error.extra.get("occupied_by", {}).get("sample_id")
        return (
            f"Ячейка {cell_id} уже занята образцом ID {occupied}. "
            f"Освободите через POST /api/storage/boxes/{box_id}/cells/{cell_id}/unallocate/ "
            f"с payload {{\"sample_id\": {occupied}}}"
        )
    if error.code == "LEGACY_ASSIGN_BLOCKED":
        return (
            f"Образец {sample_id} уже участвует в allocations. "
            f"Используйте POST /api/storage/boxes/{box_id}/cells/{cell_id}/allocate/ "
            f"с payload {{\"sample_id\": {sample_id}, \"is_primary\": true}}"
        )
    if error.code == "SAMPLE_ALREADY_PLACED":
        current = error.extra.get("current_location", {})
        return (
            f"Образец {sample_id} уже размещен в ячейке {current.get('cell_id')} бокса {current.get('box_id')}. "
            f"Освободите текущую ячейку DELETE /api/storage/boxes/{current.get('box_id')}/cells/{current.get('cell_id')}/clear/"
        )
    if error.code == "ASSIGN_CONFLICT":
        return (
            f"Конфликт сохранения для ячейки {cell_id} и образца {sample_id}: "
            f"{error.extra.get('details')}"
        )
    if error.code == "STORAGE_NOT_FOUND":
        return f"Ячейка {cell_id} в боксе {box_id} не найдена"
    if error.code == "SAMPLE_NOT_FOUND":
        return f"Образец с ID {sample_id} не найден"
    return (
        f"Ошибка при размещении образца {sample_id} в ячейке {cell_id}: "
        f"{error.message}"
    )


def bulk_assign_primary(
    *,
    box_id: str,
    assignments: Iterable[Dict[str, Any]],
) -> ServiceResult:
    assignments = list(assignments)
    if not assignments:
        raise StorageServiceError(
            message="Список назначений не может быть пустым",
            status_code=400,
            code="EMPTY_ASSIGNMENTS",
        )

    batch_id = generate_batch_id()
    successful: List[Dict[str, Any]] = []
    errors: List[str] = []
    logs: List[ServiceLogEntry] = []

    for item in assignments:
        try:
            result = assign_primary_cell(
                sample_id=item["sample_id"],
                box_id=box_id,
                cell_id=item["cell_id"],
                batch_id=batch_id,
            )
        except StorageServiceError as exc:
            errors.append(
                _format_bulk_assign_error(
                    box_id=box_id,
                    assignment=item,
                    error=exc,
                )
            )
            continue

        successful.append(result.payload["assignment"])
        logs.extend(result.logs)

    payload = {
        "statistics": {
            "total_requested": len(assignments),
            "successful": len(successful),
            "failed": len(errors),
        },
        "successful_assignments": successful,
        "errors": errors,
    }
    return ServiceResult(payload=payload, logs=logs)


def _format_bulk_allocate_error(
    *,
    box_id: str,
    assignment: Dict[str, Any],
    error: StorageServiceError,
) -> str:
    cell_id = assignment["cell_id"]
    if error.code == "LEGACY_CELL_OCCUPIED":
        return (
            f"Ячейка {cell_id} уже занята legacy-образцом. "
            f"Очистите через /api/storage/boxes/{box_id}/cells/{cell_id}/clear/."
        )
    if error.code == "ALLOCATION_OCCUPIED":
        occupied = error.extra.get("occupied_by")
        return (
            f"Ячейка {cell_id} уже занята allocation для образца ID {occupied}. "
            f"Удалите allocation через /api/storage/boxes/{box_id}/cells/{cell_id}/unallocate/."
        )
    if error.code == "ALLOCATION_NOT_FOUND":
        return (
            f"Allocation для образца {assignment['sample_id']} в ячейке {cell_id} не найдено"
        )
    if error.code == "STORAGE_NOT_FOUND":
        return f"Ячейка {cell_id} в боксе {box_id} не найдена"
    if error.code == "SAMPLE_NOT_FOUND":
        return f"Образец с ID {assignment['sample_id']} не найден"
    return (
        f"Ошибка при добавлении allocation для образца {assignment['sample_id']} "
        f"в ячейку {cell_id}: {error.message}"
    )


def bulk_allocate_cells(
    *,
    box_id: str,
    assignments: Iterable[Dict[str, Any]],
) -> ServiceResult:
    assignments = list(assignments)
    if not assignments:
        raise StorageServiceError(
            message="Список назначений не может быть пустым",
            status_code=400,
            code="EMPTY_ASSIGNMENTS",
        )

    batch_id = generate_batch_id()
    successes: List[Dict[str, Any]] = []
    errors: List[str] = []
    logs: List[ServiceLogEntry] = []

    for item in assignments:
        try:
            result = allocate_sample_to_cell(
                sample_id=item["sample_id"],
                box_id=box_id,
                cell_id=item["cell_id"],
                is_primary=False,
                batch_id=batch_id,
            )
        except StorageServiceError as exc:
            errors.append(
                _format_bulk_allocate_error(
                    box_id=box_id,
                    assignment=item,
                    error=exc,
                )
            )
            continue

        allocation = result.payload["allocation"]
        successes.append(
            {
                "sample_id": allocation["sample_id"],
                "cell_id": allocation["cell_id"],
                "storage_id": allocation["storage_id"],
                "is_primary": allocation["is_primary"],
            }
        )
        logs.extend(result.logs)

    payload = {
        "statistics": {
            "total_requested": len(assignments),
            "successful": len(successes),
            "failed": len(errors),
        },
        "successful_allocations": successes,
        "errors": errors,
    }
    return ServiceResult(payload=payload, logs=logs)
