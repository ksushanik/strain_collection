#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strain_tracker_project.settings')
django.setup()

from sample_management.models import Sample
from storage_management.models import Storage

def check_sample_56():
    print("🔍 Проверка данных образца 56")
    print("=" * 50)
    
    try:
        sample = Sample.objects.get(id=56)
        print(f"✅ Образец найден: ID {sample.id}")
        print(f"📝 Номер образца: {sample.original_sample_number}")
        print(f"🧬 Штамм: {sample.strain}")
        
        if sample.storage:
            storage = sample.storage
            print(f"\n📦 Данные хранилища:")
            print(f"   ID хранилища: {storage.id}")
            print(f"   Бокс: {storage.box_id}")
            print(f"   Ячейка: {storage.cell_id}")
            print(f"   Полное описание: {storage}")
        else:
            print("\n❌ У образца НЕТ связанного хранилища!")
            
        # Проверим все поля образца
        print(f"\n📋 Все поля образца:")
        for field in sample._meta.fields:
            field_name = field.name
            field_value = getattr(sample, field_name)
            if field_value is not None:
                print(f"   {field_name}: {field_value}")
        
    except Sample.DoesNotExist:
        print("❌ Образец с ID 56 не найден!")
        return
    
    # Проверим доступные хранилища
    print(f"\n📊 Статистика хранилищ:")
    total_storages = Storage.objects.count()
    
    # Правильный способ найти занятые хранилища
    occupied_storage_ids = Sample.objects.filter(storage__isnull=False).values_list('storage_id', flat=True)
    occupied_storages = len(set(occupied_storage_ids))
    free_storages = total_storages - occupied_storages
    
    print(f"   Всего хранилищ: {total_storages}")
    print(f"   Занятых: {occupied_storages}")
    print(f"   Свободных: {free_storages}")
    
    # Покажем несколько примеров свободных хранилищ
    print(f"\n🆓 Примеры свободных хранилищ:")
    free_storage_examples = Storage.objects.exclude(id__in=occupied_storage_ids)[:5]
    for storage in free_storage_examples:
        print(f"   ID {storage.id}: Бокс {storage.box_id}, Ячейка {storage.cell_id}")

def check_storage_api_structure():
    """Проверяем структуру API для хранилищ"""
    print(f"\n🔧 Проверка структуры Storage модели:")
    print("=" * 40)
    
    # Получаем первое хранилище для примера
    storage = Storage.objects.first()
    if storage:
        print(f"Пример хранилища: {storage}")
        print(f"Поля модели Storage:")
        for field in storage._meta.fields:
            field_name = field.name
            field_value = getattr(storage, field_name)
            field_type = field.__class__.__name__
            print(f"   {field_name} ({field_type}): {field_value}")

if __name__ == "__main__":
    check_sample_56()
    check_storage_api_structure()