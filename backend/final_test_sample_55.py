#!/usr/bin/env python
import os
import sys
import django
import csv

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strain_tracker_project.settings')
django.setup()

from sample_management.models import Sample
from scripts.normalize_text import normalize_cyrillic_to_latin

def test_sample_55_final():
    print("🧪 Финальный тест образца 55")
    print("=" * 50)
    
    # 1. Проверяем текущее состояние в БД
    print("1️⃣ Текущее состояние в базе данных:")
    try:
        sample_55 = Sample.objects.get(id=55)
        print(f"   ✅ Образец ID 55 найден")
        print(f"   📋 original_sample_number: '{sample_55.original_sample_number}'")
        print(f"   🔤 Unicode коды: {[ord(c) for c in sample_55.original_sample_number]}")
    except Sample.DoesNotExist:
        print("   ❌ Образец ID 55 не найден")
        return
    
    # 2. Читаем данные из CSV
    print("\n2️⃣ Чтение данных из CSV:")
    csv_path = '../data/Samples_Table.csv'
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            
            # Находим строку 55 (индекс 54)
            if len(rows) > 54:
                row_55 = rows[54]
                csv_original_number = row_55.get('OriginalSampleNumber', '')
                print(f"   ✅ Строка 55 найдена в CSV")
                print(f"   📋 OriginalSampleNumber: '{csv_original_number}'")
                print(f"   🔤 Unicode коды: {[ord(c) for c in csv_original_number]}")
                
                # Применяем нормализацию
                normalized_number = normalize_cyrillic_to_latin(csv_original_number)
                print(f"   🔄 После нормализации: '{normalized_number}'")
                print(f"   🔤 Unicode коды: {[ord(c) for c in normalized_number]}")
            else:
                print("   ❌ Строка 55 не найдена в CSV")
                return
                
    except FileNotFoundError:
        print(f"   ❌ Файл {csv_path} не найден")
        return
    
    # 3. Проверяем поиск по номеру
    print("\n3️⃣ Проверка поиска по номеру:")
    
    # Поиск по латинскому варианту
    latin_samples = Sample.objects.filter(original_sample_number='11A')
    print(f"   🔍 Поиск по '11A': найдено {latin_samples.count()} образцов")
    
    # Поиск по кириллическому варианту
    cyrillic_samples = Sample.objects.filter(original_sample_number='11А')
    print(f"   🔍 Поиск по '11А': найдено {cyrillic_samples.count()} образцов")
    
    # 4. Проверяем совпадение
    print("\n4️⃣ Проверка совпадения:")
    db_value = sample_55.original_sample_number
    csv_value = normalized_number
    
    if db_value == csv_value:
        print(f"   ✅ СОВПАДЕНИЕ: БД '{db_value}' == CSV '{csv_value}'")
        print("   🎉 Проблема с OriginalSampleNumber решена!")
    else:
        print(f"   ❌ НЕ СОВПАДАЕТ: БД '{db_value}' != CSV '{csv_value}'")
        print("   🚨 Проблема все еще существует")
    
    # 5. Тест импорта (симуляция)
    print("\n5️⃣ Симуляция импорта:")
    print(f"   📥 CSV данные: OriginalSampleNumber = '{csv_original_number}'")
    print(f"   🔄 После нормализации: '{normalized_number}'")
    print(f"   🔍 Поиск в БД по '{normalized_number}':")
    
    existing_samples = Sample.objects.filter(original_sample_number=normalized_number)
    if existing_samples.exists():
        print(f"   ✅ Найден существующий образец: ID {existing_samples.first().id}")
        print("   📝 Будет выполнено обновление существующей записи")
    else:
        print("   ❌ Существующий образец не найден")
        print("   📝 Будет создана новая запись")
    
    print("\n" + "=" * 50)
    if db_value == csv_value and existing_samples.exists():
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Проблема с OriginalSampleNumber полностью решена")
    else:
        print("❌ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("🚨 Требуется дополнительное исследование")

if __name__ == "__main__":
    test_sample_55_final()