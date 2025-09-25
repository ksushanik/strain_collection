#!/usr/bin/env python
import os
import sys
import django
from collections import Counter

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strain_tracker_project.settings')
django.setup()

from sample_management.models import Sample

def analyze_duplicate_sample_numbers():
    print("🔍 Анализ дублирования номеров образцов")
    print("=" * 60)
    
    # Получаем все образцы с непустыми номерами
    samples = Sample.objects.filter(
        original_sample_number__isnull=False
    ).exclude(original_sample_number='').values('id', 'original_sample_number')
    
    print(f"📊 Всего образцов с номерами: {len(samples)}")
    
    # Подсчитываем частоту каждого номера
    number_counts = Counter(sample['original_sample_number'] for sample in samples)
    
    # Находим дубликаты
    duplicates = {number: count for number, count in number_counts.items() if count > 1}
    
    print(f"🔢 Уникальных номеров: {len(number_counts)}")
    print(f"🚨 Номеров с дубликатами: {len(duplicates)}")
    print()
    
    if duplicates:
        print("📋 Топ-10 самых часто повторяющихся номеров:")
        print("-" * 50)
        
        # Сортируем по количеству повторений
        sorted_duplicates = sorted(duplicates.items(), key=lambda x: x[1], reverse=True)
        
        for i, (number, count) in enumerate(sorted_duplicates[:10], 1):
            print(f"{i:2d}. '{number}' - {count} раз")
        
        print()
        
        # Детальный анализ нескольких примеров
        print("🔍 Детальный анализ первых 3 дубликатов:")
        print("-" * 50)
        
        for number, count in sorted_duplicates[:3]:
            print(f"\n📌 Номер образца: '{number}' ({count} экземпляров)")
            
            # Получаем все образцы с этим номером
            duplicate_samples = Sample.objects.filter(original_sample_number=number)
            
            for sample in duplicate_samples:
                print(f"   🔸 ID: {sample.id}")
                if hasattr(sample, 'strain') and sample.strain:
                    print(f"      Штамм: {sample.strain}")
                if hasattr(sample, 'storage') and sample.storage:
                    print(f"      Хранилище: Box {sample.storage.box_id}, Cell {sample.storage.cell_id}")
                print()
    
    # Статистика
    print("📈 Статистика дублирования:")
    print("-" * 30)
    
    total_samples = len(samples)
    unique_numbers = len(number_counts)
    duplicate_samples = sum(count for count in duplicates.values())
    
    print(f"   Всего образцов: {total_samples}")
    print(f"   Уникальных номеров: {unique_numbers}")
    print(f"   Образцов с дублированными номерами: {duplicate_samples}")
    print(f"   Процент дублирования: {(duplicate_samples / total_samples * 100):.1f}%")
    
    # Распределение по количеству дубликатов
    duplicate_distribution = Counter(duplicates.values())
    print(f"\n📊 Распределение дубликатов:")
    for dup_count in sorted(duplicate_distribution.keys()):
        numbers_with_this_count = duplicate_distribution[dup_count]
        print(f"   {dup_count} дубликата: {numbers_with_this_count} номеров")

def check_business_logic():
    """Проверяем, есть ли бизнес-логика для дублирования номеров"""
    print("\n🤔 Анализ возможных причин дублирования:")
    print("=" * 50)
    
    # Проверяем, связаны ли дубликаты с разными штаммами
    duplicates = Sample.objects.values('original_sample_number').annotate(
        count=django.db.models.Count('id')
    ).filter(count__gt=1)
    
    strain_analysis = []
    
    for dup in duplicates[:5]:  # Анализируем первые 5 дубликатов
        number = dup['original_sample_number']
        samples = Sample.objects.filter(original_sample_number=number)
        
        strains = set()
        for sample in samples:
            if hasattr(sample, 'strain') and sample.strain:
                strains.add(str(sample.strain))
        
        strain_analysis.append({
            'number': number,
            'count': dup['count'],
            'unique_strains': len(strains),
            'strains': list(strains)
        })
    
    print("🧬 Связь дубликатов со штаммами:")
    for analysis in strain_analysis:
        print(f"   Номер '{analysis['number']}' ({analysis['count']} образцов):")
        print(f"      Уникальных штаммов: {analysis['unique_strains']}")
        if analysis['strains']:
            print(f"      Штаммы: {', '.join(analysis['strains'][:3])}{'...' if len(analysis['strains']) > 3 else ''}")
        print()

if __name__ == "__main__":
    analyze_duplicate_sample_numbers()
    check_business_logic()