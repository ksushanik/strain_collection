#!/usr/bin/env python
"""
Скрипт для импорта данных из CSV файлов в PostgreSQL базу данных
через модели Django с валидацией Pydantic
"""

import os
import sys
from pathlib import Path

import django
import pandas as pd
from django.conf import settings
from django.db import transaction
from pydantic import ValidationError

# Добавляем корень проекта (/app) в PYTHONPATH, чтобы Django нашел настройки
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / "backend"))

# Настройка Django
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "strain_tracker_project.settings"
)
django.setup()

from collection_manager.models import (AppendixNote, Comment,  # noqa: E402
                                       IndexLetter, Location, Sample, Source,
                                       Storage, Strain)
from collection_manager.schemas import (ImportAppendixNoteSchema,  # noqa: E402
                                        ImportCommentSchema,
                                        ImportIndexLetterSchema,
                                        ImportLocationSchema,
                                        ImportSampleSchema, ImportSourceSchema,
                                        ImportStorageSchema,
                                        ImportStrainSchema,
                                        validate_boolean_from_csv,
                                        validate_csv_row)


@transaction.atomic
def str_to_bool(value):
    """Конвертация строки в булево значение"""
    if pd.isna(value) or value == "":
        return False
    return str(value).lower() in ["true", "1", "yes", "да", "+"]


@transaction.atomic
def import_index_letters():
    """Импорт индексных букв с валидацией"""
    print("📝 Импорт индексных букв...")
    df = pd.read_csv(project_root / "data" / "IndexLetters_Table.csv")

    validated_count = 0
    for index, row in df.iterrows():
        try:
            # Валидация данных
            validated_data = validate_csv_row(
                ImportIndexLetterSchema,
                row.to_dict(),
                row_number=index
                + 2,  # +2 для учета заголовка и индексации с 1
            )

            IndexLetter.objects.get_or_create(
                id=validated_data.IndexLetterID,
                defaults={"letter_value": validated_data.IndexLetterValue},
            )
            validated_count += 1

        except (ValidationError, ValueError) as e:
            print(f"⚠️  Ошибка в строке {index + 2}: {e}")
            continue

    print(f"✅ Импортировано {validated_count} из {len(df)} индексных букв")


@transaction.atomic
def import_locations():
    """Импорт местоположений с валидацией"""
    print("🌍 Импорт местоположений...")
    df = pd.read_csv(project_root / "data" / "Locations_Table.csv")

    validated_count = 0
    for index, row in df.iterrows():
        try:
            validated_data = validate_csv_row(
                ImportLocationSchema, row.to_dict(), row_number=index + 2
            )

            Location.objects.get_or_create(
                id=validated_data.LocationID,
                defaults={"name": validated_data.LocationNameValue},
            )
            validated_count += 1

        except (ValidationError, ValueError) as e:
            print(f"⚠️  Ошибка в строке {index + 2}: {e}")
            continue

    print(f"✅ Импортировано {validated_count} из {len(df)} местоположений")


@transaction.atomic
def import_sources():
    """Импорт источников с валидацией"""
    print("🔬 Импорт источников...")
    df = pd.read_csv(project_root / "data" / "Sources_Table.csv")

    validated_count = 0
    for index, row in df.iterrows():
        try:
            validated_data = validate_csv_row(
                ImportSourceSchema, row.to_dict(), row_number=index + 2
            )

            Source.objects.get_or_create(
                id=validated_data.SourceID,
                defaults={
                    "organism_name": validated_data.SourceOrganismName,
                    "source_type": validated_data.SourceTypeName,
                    "category": validated_data.SourceCategoryName,
                },
            )
            validated_count += 1

        except (ValidationError, ValueError) as e:
            print(f"⚠️  Ошибка в строке {index + 2}: {e}")
            continue

    print(f"✅ Импортировано {validated_count} из {len(df)} источников")


@transaction.atomic
def import_comments():
    """Импорт комментариев с валидацией"""
    print("💬 Импорт комментариев...")
    df = pd.read_csv(project_root / "data" / "Comments_Table.csv")

    validated_count = 0
    for index, row in df.iterrows():
        try:
            validated_data = validate_csv_row(
                ImportCommentSchema, row.to_dict(), row_number=index + 2
            )

            Comment.objects.get_or_create(
                id=validated_data.CommentID,
                defaults={"text": validated_data.CommentTextValue},
            )
            validated_count += 1

        except (ValidationError, ValueError) as e:
            print(f"⚠️  Ошибка в строке {index + 2}: {e}")
            continue

    print(f"✅ Импортировано {validated_count} из {len(df)} комментариев")


@transaction.atomic
def import_appendix_notes():
    """Импорт примечаний с валидацией"""
    print("📋 Импорт примечаний...")
    df = pd.read_csv(project_root / "data" / "AppendixNotes_Table.csv")

    validated_count = 0
    for index, row in df.iterrows():
        try:
            validated_data = validate_csv_row(
                ImportAppendixNoteSchema, row.to_dict(), row_number=index + 2
            )

            AppendixNote.objects.get_or_create(
                id=validated_data.AppendixNoteID,
                defaults={"text": validated_data.AppendixNoteText},
            )
            validated_count += 1

        except (ValidationError, ValueError) as e:
            print(f"⚠️  Ошибка в строке {index + 2}: {e}")
            continue

    print(f"✅ Импортировано {validated_count} из {len(df)} примечаний")


@transaction.atomic
def import_storage_data():
    file_path = os.path.join(
        settings.BASE_DIR, "..", "data", "Storage_Table.csv"
    )
    try:
        # Указываем dtype=str, чтобы pandas читал все колонки как строки и не было ошибок валидации
        df = pd.read_csv(file_path, sep=",", header=0, dtype=str)
        df = df.where(pd.notna(df), None)

        print("📦 Импорт данных о хранении...")

        storage_objects = []
        validated_count = 0
        error_count = 0

        for index, row in df.iterrows():
            try:
                # Используем .model_dump() вместо .dict() для Pydantic v2
                storage_data = ImportStorageSchema.model_validate(
                    row.to_dict()
                )
                # Правильное маппинг полей из схемы в модель
                storage_objects.append(Storage(
                    box_id=storage_data.BoxIDValue,
                    cell_id=storage_data.CellIDValue
                ))
                validated_count += 1
            except ValidationError as e:
                print(f"  [!] Ошибка валидации для строки {index + 2}: {e}")
                error_count += 1

        if error_count == 0:
            Storage.objects.bulk_create(storage_objects, batch_size=500)
            print(
                f"✅ Импортировано {validated_count} из {len(df)} записей о хранении"
            )
        else:
            print(
                f"❌ Импорт хранения отменен из-за {error_count} ошибок валидации."
            )

    except FileNotFoundError:
        print(f"  [!] Файл не найден: {file_path}")
    except Exception as e:
        print(f"  [!] Непредвиденная ошибка при импорте хранения: {e}")


@transaction.atomic
def import_strains():
    """Импорт штаммов с валидацией"""
    print("🦠 Импорт штаммов...")
    df = pd.read_csv(project_root / "data" / "Strains_Table.csv")

    validated_count = 0
    for index, row in df.iterrows():
        try:
            # Предварительная обработка пустых значений для валидации
            row_dict = row.to_dict()
            for key, value in row_dict.items():
                if pd.isna(value) or value == "":
                    row_dict[key] = None

            validated_data = validate_csv_row(
                ImportStrainSchema, row_dict, row_number=index + 2
            )

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

        except (ValidationError, ValueError) as e:
            print(f"⚠️  Ошибка в строке {index + 2}: {e}")
            continue

    print(f"✅ Импортировано {validated_count} из {len(df)} штаммов")


@transaction.atomic
def import_samples():
    """Импорт образцов с валидацией"""
    print("🧪 Импорт образцов...")
    df = pd.read_csv(project_root / "data" / "Samples_Table.csv")

    validated_count = 0
    for index, row in df.iterrows():
        try:
            # Предварительная обработка пустых значений для валидации
            row_dict = row.to_dict()
            for key, value in row_dict.items():
                if pd.isna(value) or value == "":
                    row_dict[key] = (
                        None
                        if "_FK" in key or key == "OriginalSampleNumber"
                        else ""
                    )
                # Конвертация булевых значений в строки для валидации
                elif (
                    key.startswith("Has")
                    or key == "IsIdentified"
                    or key == "SEQStatus"
                ):
                    row_dict[key] = str(value).lower()

            validated_data = validate_csv_row(
                ImportSampleSchema, row_dict, row_number=index + 2
            )

            # Получение связанных объектов (может быть None для пустых ячеек)
            def get_foreign_object(model_class, field_id):
                if field_id is None:
                    return None
                try:
                    return model_class.objects.get(id=field_id)
                except model_class.DoesNotExist:
                    print(
                        f"⚠️  {model_class.__name__} с ID {field_id} не найден"
                    )
                    return None

            index_letter = get_foreign_object(
                IndexLetter, validated_data.IndexLetterID_FK
            )
            strain = get_foreign_object(Strain, validated_data.StrainID_FK)
            storage = get_foreign_object(Storage, validated_data.StorageID_FK)
            source = get_foreign_object(Source, validated_data.SourceID_FK)
            location = get_foreign_object(
                Location, validated_data.LocationID_FK
            )
            appendix_note_obj = get_foreign_object(
                AppendixNote, validated_data.AppendixNoteID_FK
            )
            comment_obj = get_foreign_object(Comment, validated_data.CommentID_FK)
            
            # Получаем текст из объектов
            appendix_note_text = appendix_note_obj.text if appendix_note_obj else None
            comment_text = comment_obj.text if comment_obj else None

            Sample.objects.update_or_create(
                id=validated_data.SampleRowID,
                defaults={
                    "index_letter": index_letter,
                    "strain": strain,
                    "storage": storage,
                    "original_sample_number": validated_data.OriginalSampleNumber,
                    "source": source,
                    "location": location,
                    "appendix_note": appendix_note_text,
                    "comment": comment_text,
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

        except (ValidationError, ValueError) as e:
            print(f"⚠️  Ошибка в строке {index + 2}: {e}")
            continue

    print(f"✅ Импортировано {validated_count} из {len(df)} образцов")


def main():
    """Основная функция для запуска импорта"""
    print("==================================================")
    print("🚀 Запуск импорта данных в базу...")

    import_index_letters()
    import_locations()
    import_sources()
    import_comments()
    import_appendix_notes()
    import_storage_data()
    import_strains()
    import_samples()

    print("==================================================")
    print("🎉 Импорт данных завершен успешно!")
    print("")


if __name__ == "__main__":
    main()
