import os
from pathlib import Path

import pandas as pd
from reference_data.models import (AppendixNote, Comment, IndexLetter,
                                   Location, Source)
from storage_management.models import Storage
from strain_management.models import Strain
from sample_management.models import Sample
from collection_manager.schemas import (ImportSampleSchema,
                                        ImportStorageSchema,
                                        ImportStrainSchema)
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction


def validate_boolean_from_csv(value):
    """Преобразование CSV значений в булев тип"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ["true", "1", "yes", "on"]
    return bool(value)


class Command(BaseCommand):
    help = "Imports data from CSV files into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--table",
            type=str,
            choices=["all", "storage", "samples", "strains"],
            default="all",
            help="Какую таблицу импортировать",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Принудительно очистить таблицы перед импортом",
        )

    def handle(self, *args, **options):
        table_to_import = options["table"]
        force = options["force"]

        # Use absolute path from settings.BASE_DIR parent (корневая папка проекта)
        # В Docker контейнере данные находятся в /app/data
        if os.path.exists("/app/data"):
            data_dir = Path("/app/data")  # Docker путь
        else:
            data_dir = settings.BASE_DIR.parent / "data"  # Локальный путь

        self.stdout.write(self.style.SUCCESS("🚀 Запуск импорта данных..."))

        if table_to_import == "all":
            # 1) Storage → 2) Strains → 3) Samples
            self.import_storage_data(data_dir, force)
            self.import_strains_data(data_dir, force)
            self.import_samples_data(data_dir, force)

        else:
            # Импорт только указанных таблиц без изменения логики
            if table_to_import == "storage":
                self.import_storage_data(data_dir, force)
            elif table_to_import == "strains":
                self.import_strains_data(data_dir, force)
            elif table_to_import == "samples":
                self.import_samples_data(data_dir, force)

        self.stdout.write(self.style.SUCCESS("✅ Импорт завершен!"))

    @transaction.atomic
    def import_storage_data(self, data_dir, force):
        self.stdout.write(self.style.SUCCESS("📦 Импорт данных хранилища..."))
        file_path = data_dir / "Storage_Table.csv"

        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f"Файл не найден: {file_path}"))
            return

        if force:
            Storage.objects.all().delete()
            self.stdout.write("Очищена таблица Storage")

        df = pd.read_csv(file_path, dtype=str)
        df = df.where(pd.notna(df), None)

        storage_objects = []
        validated_count = 0

        for index, row in df.iterrows():
            try:
                storage_data = ImportStorageSchema.model_validate(
                    row.to_dict()
                )
                storage_objects.append(
                    Storage(
                        id=storage_data.StorageID,
                        box_id=storage_data.BoxIDValue,
                        cell_id=storage_data.CellIDValue,
                    )
                )
                validated_count += 1
            except Exception as e:
                self.stdout.write(f"❌ Ошибка в строке {index + 2}: {e}")
                return

        Storage.objects.bulk_create(storage_objects, batch_size=500)
        self.stdout.write(
            f"✅ Импортировано {validated_count} записей хранилища"
        )

    @transaction.atomic
    def import_samples_data(self, data_dir, force):
        self.stdout.write(self.style.SUCCESS("🧪 Импорт данных об образцах..."))
        file_path = data_dir / "Samples_Table.csv"

        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f"Файл не найден: {file_path}"))
            return

        if force:
            Sample.objects.all().delete()
            self.stdout.write("Очищена таблица Sample")

        df = pd.read_csv(file_path, dtype=str)
        df = df.where(pd.notna(df), None)

        validated_count = 0

        for index, row in df.iterrows():
            try:
                # Подготовка данных для валидации
                row_dict = row.to_dict()
                for key, value in row_dict.items():
                    if pd.isna(value) or value == "":
                        row_dict[key] = (
                            None
                            if "_FK" in key or key == "OriginalSampleNumber"
                            else ""
                        )
                    elif (
                        key.startswith("Has")
                        or key == "IsIdentified"
                        or key == "SEQStatus"
                    ):
                        row_dict[key] = str(value).lower()

                validated_data = ImportSampleSchema.model_validate(row_dict)

                # Получение связанных объектов
                def get_foreign_object(model_class, field_id):
                    if field_id is None:
                        return None
                    try:
                        return model_class.objects.get(id=field_id)
                    except model_class.DoesNotExist:
                        self.stdout.write(
                            f"⚠️ {model_class.__name__} с ID {field_id} не найден"
                        )
                        return None

                index_letter = get_foreign_object(
                    IndexLetter, validated_data.IndexLetterID_FK
                )
                strain = get_foreign_object(Strain, validated_data.StrainID_FK)
                storage = get_foreign_object(
                    Storage, validated_data.StorageID_FK
                )
                source = get_foreign_object(Source, validated_data.SourceID_FK)
                location = get_foreign_object(
                    Location, validated_data.LocationID_FK
                )
                appendix_note = get_foreign_object(
                    AppendixNote, validated_data.AppendixNoteID_FK
                )
                comment = get_foreign_object(
                    Comment, validated_data.CommentID_FK
                )

                Sample.objects.get_or_create(
                    id=validated_data.SampleRowID,
                    defaults={
                        "index_letter": index_letter,
                        "strain": strain,
                        "storage": storage,
                        "original_sample_number": validated_data.OriginalSampleNumber,
                        "source": source,
                        "location": location,
                        "appendix_note": appendix_note,
                        "comment": comment,
                        "has_photo": validate_boolean_from_csv(
                            validated_data.HasPhoto
                        ),
                        "is_identified": validate_boolean_from_csv(
                            validated_data.IsIdentified
                        ),
                        "has_antibiotic_activity": validate_boolean_from_csv(
                            validated_data.HasAntibioticActivity
                        ),
                        "has_genome": validate_boolean_from_csv(
                            validated_data.HasGenome
                        ),
                        "has_biochemistry": validate_boolean_from_csv(
                            validated_data.HasBiochemistry
                        ),
                        "seq_status": validate_boolean_from_csv(
                            validated_data.SEQStatus
                        ),
                    },
                )
                validated_count += 1

            except Exception as e:
                self.stdout.write(f"❌ Ошибка в строке {index + 2}: {e}")
                continue

        self.stdout.write(f"✅ Импортировано {validated_count} образцов")

    @transaction.atomic
    def import_strains_data(self, data_dir, force):
        self.stdout.write(self.style.SUCCESS("🧬 Импорт данных о штаммах..."))
        file_path = data_dir / "Strains_Table.csv"

        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f"Файл не найден: {file_path}"))
            return

        if force:
            Strain.objects.all().delete()
            self.stdout.write("Очищена таблица Strain")

        df = pd.read_csv(file_path, dtype=str)
        df = df.where(pd.notna(df), None)

        validated_count = 0

        for index, row in df.iterrows():
            try:
                row_dict = row.to_dict()
                for key, value in row_dict.items():
                    if pd.isna(value) or value == "":
                        row_dict[key] = None

                validated_data = ImportStrainSchema.model_validate(row_dict)

                Strain.objects.get_or_create(
                    id=validated_data.StrainID,
                    defaults={
                        "short_code": validated_data.ShortStrainCode,
                        "rrna_taxonomy": validated_data.RRNATaxonomy,
                        "identifier": validated_data.StrainIdentifierValue,
                        "name_alt": validated_data.StrainNameAlt,
                        "rcam_collection_id": validated_data.RCAMCollectionID,
                    },
                )
                validated_count += 1

            except Exception as e:
                self.stdout.write(f"❌ Ошибка в строке {index + 2}: {e}")
                continue

        self.stdout.write(f"✅ Импортировано {validated_count} штаммов")
