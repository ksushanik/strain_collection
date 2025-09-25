#!/usr/bin/env python3
"""
Скрипт для отладки импорта образца 55
Проверяет почему теряется значение OriginalSampleNumber
"""

import os
import sys
import django
import pandas as pd

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strain_tracker_project.settings')
django.setup()

from collection_manager.schemas import ImportSampleSchema
from scripts.import_data import validate_csv_row

def debug_sample_55():
    """Отладка импорта образца 55"""
    
    # Читаем CSV файл
    csv_file = "../data/Samples_Table.csv"
    df = pd.read_csv(csv_file)
    
    # Находим строку с образцом 55
    sample_55_row = df[df['SampleRowID'] == 55]
    
    if sample_55_row.empty:
        print("❌ Образец 55 не найден в CSV файле")
        return
    
    print("🔍 Отладка импорта образца 55")
    print("=" * 50)
    
    # Получаем данные строки
    row = sample_55_row.iloc[0]
    print(f"📄 Исходные данные из CSV:")
    print(f"   SampleRowID: {row['SampleRowID']}")
    print(f"   OriginalSampleNumber: '{row['OriginalSampleNumber']}'")
    print(f"   Тип: {type(row['OriginalSampleNumber'])}")
    print(f"   pd.isna(): {pd.isna(row['OriginalSampleNumber'])}")
    print(f"   == '': {row['OriginalSampleNumber'] == ''}")
    print()
    
    # Преобразуем в словарь как в оригинальном коде
    row_dict = row.to_dict()
    print(f"📋 После to_dict():")
    print(f"   OriginalSampleNumber: '{row_dict['OriginalSampleNumber']}'")
    print(f"   Тип: {type(row_dict['OriginalSampleNumber'])}")
    print()
    
    # Применяем логику обработки как в оригинальном коде
    original_value = row_dict['OriginalSampleNumber']
    for key, value in row_dict.items():
        if pd.isna(value) or value == "":
            row_dict[key] = (
                None
                if "_FK" in key or key == "OriginalSampleNumber"
                else ""
            )
            if key == "OriginalSampleNumber":
                print(f"🔄 Обработка OriginalSampleNumber:")
                print(f"   Исходное значение: '{original_value}'")
                print(f"   pd.isna(value): {pd.isna(value)}")
                print(f"   value == '': {value == ''}")
                print(f"   Результат: {row_dict[key]}")
                print()
        # Конвертация булевых значений в строки для валидации
        elif (
            key.startswith("Has")
            or key == "IsIdentified"
            or key == "SEQStatus"
        ):
            row_dict[key] = str(value).lower()
    
    print(f"📝 После обработки пустых значений:")
    print(f"   OriginalSampleNumber: {row_dict['OriginalSampleNumber']}")
    print()
    
    # Валидация
    try:
        validated_data = validate_csv_row(
            ImportSampleSchema, row_dict, row_number=56
        )
        print(f"✅ Валидация прошла успешно:")
        print(f"   validated_data.OriginalSampleNumber: {validated_data.OriginalSampleNumber}")
        print()
    except Exception as e:
        print(f"❌ Ошибка валидации: {e}")
        print()
    
    # Проверяем все значения в строке
    print("🔍 Все значения в строке:")
    for key, value in row_dict.items():
        print(f"   {key}: '{value}' (тип: {type(value)})")

if __name__ == "__main__":
    debug_sample_55()