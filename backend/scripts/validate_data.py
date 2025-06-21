#!/usr/bin/env python3
"""
Скрипт для валидации существующих данных в базе с помощью Pydantic
"""

import os
import sys
import django
from pathlib import Path
from pydantic import ValidationError

# Добавляем путь к Django проекту
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / 'backend'))

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strain_tracker_project.settings')
django.setup()

from collection_manager.models import Strain, Sample, Storage
from collection_manager.schemas import StrainSchema, SampleSchema, StorageSchema


def validate_strains(limit=100):
    """Валидация штаммов"""
    print(f"🦠 Валидация штаммов (первые {limit})...")
    strains = Strain.objects.all()[:limit]
    errors = 0
    
    for strain in strains:
        try:
            StrainSchema.model_validate({
                'id': strain.id,
                'short_code': strain.short_code,
                'rrna_taxonomy': strain.rrna_taxonomy,
                'identifier': strain.identifier,
                'name_alt': strain.name_alt,
                'rcam_collection_id': strain.rcam_collection_id,
            })
        except ValidationError as e:
            errors += 1
            if errors <= 3:  # Показываем первые 3 ошибки
                print(f"❌ Ошибка в штамме {strain.id}: {e}")
    
    print(f"✅ Результат: {errors} ошибок из {len(strains)} штаммов")
    return errors


def validate_samples(limit=100):
    """Валидация образцов"""
    print(f"\n🧪 Валидация образцов (первые {limit})...")
    samples = Sample.objects.all()[:limit]
    errors = 0
    
    for sample in samples:
        try:
            SampleSchema.model_validate({
                'id': sample.id,
                'index_letter_id': sample.index_letter.id if sample.index_letter else None,
                'strain_id': sample.strain.id if sample.strain else None,
                'storage_id': sample.storage.id if sample.storage else None,
                'original_sample_number': sample.original_sample_number,
                'source_id': sample.source.id if sample.source else None,
                'location_id': sample.location.id if sample.location else None,
                'appendix_note_id': sample.appendix_note.id if sample.appendix_note else None,
                'comment_id': sample.comment.id if sample.comment else None,
                'has_photo': sample.has_photo,
                'is_identified': sample.is_identified,
                'has_antibiotic_activity': sample.has_antibiotic_activity,
                'has_genome': sample.has_genome,
                'has_biochemistry': sample.has_biochemistry,
                'seq_status': sample.seq_status,
            })
        except ValidationError as e:
            errors += 1
            if errors <= 3:  # Показываем первые 3 ошибки
                print(f"❌ Ошибка в образце {sample.id}: {e}")
    
    print(f"✅ Результат: {errors} ошибок из {len(samples)} образцов")
    return errors


def validate_storage(limit=100):
    """Валидация хранилищ"""
    print(f"\n📦 Валидация хранилищ (первые {limit})...")
    storages = Storage.objects.all()[:limit]
    errors = 0
    
    for storage in storages:
        try:
            StorageSchema.model_validate({
                'id': storage.id,
                'box_id': storage.box_id,
                'cell_id': storage.cell_id,
            })
        except ValidationError as e:
            errors += 1
            if errors <= 3:  # Показываем первые 3 ошибки
                print(f"❌ Ошибка в хранилище {storage.id}: {e}")
    
    print(f"✅ Результат: {errors} ошибок из {len(storages)} хранилищ")
    return errors


def main():
    """Основная функция валидации"""
    print("🔍 Валидация данных в базе с помощью Pydantic...")
    print("=" * 50)
    
    total_errors = 0
    
    # Валидация данных
    total_errors += validate_strains(50)
    total_errors += validate_samples(50)
    total_errors += validate_storage(50)
    
    print("\n" + "=" * 50)
    if total_errors == 0:
        print("🎉 Все данные прошли валидацию успешно!")
    else:
        print(f"⚠️  Обнаружено {total_errors} ошибок валидации")
        print("💡 Это может указывать на некорректные данные в базе")
    
    # Общая статистика
    print(f"\n📊 Общая статистика:")
    print(f"- Штаммы в базе: {Strain.objects.count()}")
    print(f"- Образцы в базе: {Sample.objects.count()}")
    print(f"- Хранилища в базе: {Storage.objects.count()}")


if __name__ == "__main__":
    main() 