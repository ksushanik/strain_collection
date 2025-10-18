from typing import List, Tuple

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from django.http import HttpRequest

from sample_management.models import Sample
from collection_manager.utils import (
    log_change,
    generate_batch_id,
    model_to_dict,
)
from storage_management.models import Storage, StorageBox
from storage_management.utils import ensure_storage_cells


class Command(BaseCommand):
    help = (
        "Авторазруливание конфликтов по Sample.storage: "
        "оставляет одного владельца ячейки, снимает storage у остальных."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Внести изменения в БД (по умолчанию только dry-run)",
        )
        parser.add_argument(
            "--prefer",
            choices=["with_strain", "created_at", "updated_at"],
            default="with_strain",
            help=(
                "Стратегия выбора сохраняемого образца: "
                "with_strain — приоритет у образца со штаммом/ориг. номером; "
                "created_at — самый ранний; updated_at — самый свежий"
            ),
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Обработать не более N групп-дубликатов",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Печать подробной информации по каждой группе",
        )
        parser.add_argument(
            "--reallocate",
            action="store_true",
            help="Автоматически перераспределять освобожденные образцы в свободные ячейки",
        )
        parser.add_argument(
            "--fallback",
            choices=["none", "any_box"],
            default="none",
            help=(
                "Если в исходном боксе нет свободных ячеек: none — оставить без storage; any_box — искать глобально"
            ),
        )

    def handle(self, *args, **options):
        execute: bool = options["execute"]
        prefer: str = options["prefer"]
        limit: int | None = options["limit"]
        verbose: bool = options["verbose"]
        reallocate: bool = options["reallocate"]
        fallback: str = options["fallback"]

        batch_id = generate_batch_id()
        fake_request = self._build_request()

        # Найти storage_id, где >1 образца ссылаются на одну и ту же ячейку
        dup_qs = (
            Sample.objects.exclude(storage__isnull=True)
            .values("storage_id")
            .annotate(c=Count("id"))
            .filter(c__gt=1)
            .order_by("-c")
        )

        if limit is not None:
            dup_qs = dup_qs[:limit]

        duplicate_groups = list(dup_qs)
        total_groups = len(duplicate_groups)
        processed_groups = 0
        released_samples = 0
        kept_samples = 0
        reallocated_samples = 0

        if total_groups == 0:
            self.stdout.write(self.style.SUCCESS("Дубликатов по Sample.storage не найдено."))
            return

        self.stdout.write(
            self.style.WARNING(
                f"Найдено групп-конфликтов: {total_groups}. Режим: {'EXECUTE' if execute else 'DRY-RUN'}. Стратегия: {prefer}."
            )
        )

        for group in duplicate_groups:
            storage_id = group["storage_id"]
            with transaction.atomic():
                samples = (
                    Sample.objects.select_for_update()
                    .filter(storage_id=storage_id)
                    .order_by("created_at")
                )
                samples = list(samples)
                winner, losers = self._select_winner_and_losers(samples, prefer)

                kept_samples += 1
                processed_groups += 1

                if verbose:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"storage_id={storage_id}: сохраняем sample_id={winner.id}, снимаем storage у {[s.id for s in losers]}"
                        )
                    )

                if execute:
                    for s in losers:
                        old_values = model_to_dict(s)
                        # Снять связь с ячейкой
                        s.storage = None
                        s.save(update_fields=["storage", "updated_at"])  # updated_at обновится автоматически
                        new_values = model_to_dict(s)

                        released_samples += 1

                        # Логирование как UPDATE
                        try:
                            log_change(
                                request=fake_request,
                                content_type="sample",
                                object_id=s.id,
                                action="UPDATE",
                                old_values=old_values,
                                new_values=new_values,
                                comment=(
                                    f"Авторазруливание конфликтов occupancy: снят storage, winner={winner.id}, storage_id={storage_id}"
                                ),
                                batch_id=batch_id,
                            )
                        except Exception as e:
                            # Не прерываем процесс из-за ошибок логирования
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Логирование не удалось для sample_id={s.id}: {e}"
                                )
                            )

                    # Автоперераспределение освобожденных образцов
                    if reallocate:
                        conf_cell = Storage.objects.filter(id=storage_id).first()
                        box_id = conf_cell.box_id if conf_cell else None
                        if box_id:
                            # Убедимся, что сетка ячеек создана
                            box = StorageBox.objects.filter(box_id=box_id).first()
                            if box:
                                ensure_storage_cells(box.box_id, box.rows, box.cols)

                            free_cells = self._find_free_cells_in_box(box_id, exclude_ids={storage_id})
                        else:
                            free_cells = []

                        assigned_ids = set()
                        free_idx = 0

                        for s in losers:
                            target_cell = None

                            # Выбираем следующую свободную ячейку в исходном боксе
                            while free_idx < len(free_cells):
                                candidate = free_cells[free_idx]
                                free_idx += 1
                                if candidate.id in assigned_ids:
                                    continue
                                # Дополнительная проверка занятости под блокировкой
                                locked_candidate = Storage.objects.select_for_update().get(id=candidate.id)
                                occupied = Sample.objects.select_for_update().filter(storage_id=locked_candidate.id).exists()
                                if not occupied:
                                    target_cell = locked_candidate
                                    break

                            # Если нет свободных ячеек, пробуем глобальный поиск (fallback)
                            if target_cell is None and fallback == "any_box":
                                global_free = self._find_global_free_cells(exclude_ids=assigned_ids | {storage_id})
                                for candidate in global_free:
                                    if candidate.id in assigned_ids:
                                        continue
                                    locked_candidate = Storage.objects.select_for_update().get(id=candidate.id)
                                    occupied = Sample.objects.select_for_update().filter(storage_id=locked_candidate.id).exists()
                                    if not occupied:
                                        target_cell = locked_candidate
                                        break

                            if target_cell is None:
                                # Свободных ячеек не нашлось — оставляем без storage
                                if verbose:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f"Не удалось найти свободную ячейку для sample_id={s.id}; образец остаётся без storage"
                                        )
                                    )
                                continue

                            # Назначаем storage
                            old_values2 = model_to_dict(s)
                            s.storage = target_cell
                            s.save(update_fields=["storage", "updated_at"])
                            new_values2 = model_to_dict(s)
                            reallocated_samples += 1
                            assigned_ids.add(target_cell.id)

                            # Логируем назначение
                            try:
                                log_change(
                                    request=fake_request,
                                    content_type="sample",
                                    object_id=s.id,
                                    action="UPDATE",
                                    old_values=old_values2,
                                    new_values=new_values2,
                                    comment=(
                                        f"Автоперераспределение: назначен storage {target_cell.box_id}-{target_cell.cell_id} (fallback={fallback})"
                                    ),
                                    batch_id=batch_id,
                                )
                            except Exception as e:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"Логирование перераспределения не удалось для sample_id={s.id}: {e}"
                                    )
                                )

        self.stdout.write(self.style.SUCCESS("Готово."))
        self.stdout.write(
            self.style.SUCCESS(
                f"Итог: обработано групп={processed_groups}, сохранено образцов={kept_samples}, снято storage у образцов={released_samples}, перераспределено образцов={reallocated_samples}."
            )
        )

    def _score(self, s: Sample) -> int:
        """Приоритизация образцов: наличие штамма и оригинального номера повышают приоритет."""
        score = 0
        if getattr(s, "strain_id", None):
            score += 10
        if getattr(s, "original_sample_number", None):
            score += 5
        return score

    def _select_winner_and_losers(
        self, samples: List[Sample], prefer: str
    ) -> Tuple[Sample, List[Sample]]:
        if prefer == "with_strain":
            # Сначала по приоритету, затем по created_at
            ordered = sorted(samples, key=lambda s: (-self._score(s), s.created_at))
        elif prefer == "updated_at":
            # Сначала по приоритету, затем по updated_at (свежий остаётся)
            ordered = sorted(samples, key=lambda s: (-self._score(s), -s.updated_at.timestamp()))
        else:  # created_at
            ordered = sorted(samples, key=lambda s: (-self._score(s), s.created_at))

        winner = ordered[0]
        losers = ordered[1:]
        return winner, losers

    def _build_request(self) -> HttpRequest:
        """Синтетический HttpRequest для корректной записи audit-логов из management-команды."""
        req = HttpRequest()
        req.META = {
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_USER_AGENT": "management-command/resolve_sample_storage_duplicates",
        }
        return req

    def _find_free_cells_in_box(self, box_id: str, exclude_ids: set[int] | None = None) -> List[Storage]:
        if exclude_ids is None:
            exclude_ids = set()
        occupied_ids = set(
            Sample.objects.filter(storage__box_id=box_id).values_list("storage_id", flat=True)
        )
        occupied_ids.discard(None)
        qs = (
            Storage.objects.filter(box_id=box_id)
            .exclude(id__in=occupied_ids)
            .exclude(id__in=list(exclude_ids))
            .order_by("cell_id")
        )
        return list(qs)

    def _find_global_free_cells(self, exclude_ids: set[int] | None = None) -> List[Storage]:
        if exclude_ids is None:
            exclude_ids = set()
        occupied_ids = set(
            Sample.objects.filter(storage_id__isnull=False).values_list("storage_id", flat=True)
        )
        qs = (
            Storage.objects.exclude(id__in=occupied_ids)
            .exclude(id__in=list(exclude_ids))
            .order_by("box_id", "cell_id")
        )
        return list(qs)