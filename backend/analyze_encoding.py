#!/usr/bin/env python
import os
import sys
import django
import pandas as pd

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strain_tracker_project.settings')
django.setup()

from sample_management.models import Sample

def analyze_encoding():
    print("🔍 Анализ кодировки символов")
    print("=" * 50)
    
    # Читаем из CSV
    csv_path = "../data/Samples_Table.csv"
    df = pd.read_csv(csv_path)
    sample_55_row = df[df['SampleRowID'] == 55].iloc[0]
    csv_value = sample_55_row['OriginalSampleNumber']
    
    # Читаем из БД
    sample = Sample.objects.get(id=55)
    db_value = sample.original_sample_number
    
    print(f"📄 Значение из CSV: '{csv_value}'")
    print(f"   Длина: {len(csv_value)}")
    print(f"   Байты: {csv_value.encode('utf-8')}")
    print(f"   Unicode коды: {[ord(c) for c in csv_value]}")
    print()
    
    print(f"🗄️ Значение из БД: '{db_value}'")
    print(f"   Длина: {len(db_value)}")
    print(f"   Байты: {db_value.encode('utf-8')}")
    print(f"   Unicode коды: {[ord(c) for c in db_value]}")
    print()
    
    print(f"🔍 Сравнение:")
    print(f"   Равны: {csv_value == db_value}")
    print(f"   Равны (нормализованные): {csv_value.strip() == db_value.strip()}")
    
    # Анализируем каждый символ
    print(f"\n📝 Посимвольный анализ:")
    for i, (c1, c2) in enumerate(zip(csv_value, db_value)):
        print(f"   Позиция {i}: CSV='{c1}' (U+{ord(c1):04X}) vs БД='{c2}' (U+{ord(c2):04X}) - {'✅' if c1 == c2 else '❌'}")
    
    # Проверим, есть ли в БД записи с латинской A
    latin_a_samples = Sample.objects.filter(original_sample_number='11A').count()
    cyrillic_a_samples = Sample.objects.filter(original_sample_number='11А').count()
    
    print(f"\n🔍 Поиск в БД:")
    print(f"   Образцы с '11A' (латинская A): {latin_a_samples}")
    print(f"   Образцы с '11А' (кириллическая А): {cyrillic_a_samples}")

if __name__ == "__main__":
    analyze_encoding()