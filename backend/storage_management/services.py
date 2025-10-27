from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from django.db import IntegrityError, transaction

from collection_manager.utils import generate_batch_id
from sample_management.models import Sample, SampleStorageAllocation

from .models import Storage


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
            .select_related("strain", "storage")
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
            .select_related("strain")
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
            .select_related("sample__strain")
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
                    "recommended_method": "POST",
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
            .select_related("sample__strain")
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
            .select_related("strain")
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
            .select_related("strain")
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
