#!/usr/bin/env python
import os
import sys
import django
from collections import defaultdict

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strain_tracker_project.settings')
django.setup()

from sample_management.models import Sample

def detailed_duplicate_analysis():
    print("🔬 Детальный анализ дублирования номеров образцов")
    print("=" * 70)
    
    # Группируем образцы по номерам
    samples_by_number = defaultdict(list)
    
    samples = Sample.objects.filter(
        original_sample_number__isnull=False
    ).exclude(original_sample_number='').select_related('strain', 'storage')
    
    for sample in samples:
        samples_by_number[sample.original_sample_number].append(sample)
    
    # Анализируем только дубликаты
    duplicates = {number: samples for number, samples in samples_by_number.items() if len(samples) > 1}
    
    print(f"📊 Найдено {len(duplicates)} номеров с дубликатами")
    print()
    
    # Анализ паттернов дублирования
    print("🔍 Анализ паттернов дублирования:")
    print("-" * 50)
    
    patterns = {
        'same_strain_different_storage': 0,
        'different_strains_same_base': 0,
        'completely_different': 0,
        'strain_variations': 0
    }
    
    examples = {
        'same_strain_different_storage': [],
        'different_strains_same_base': [],
        'strain_variations': []
    }
    
    for number, sample_list in list(duplicates.items())[:20]:  # Анализируем первые 20
        strain_names = [str(sample.strain) if sample.strain else 'No strain' for sample in sample_list]
        unique_strains = set(strain_names)
        
        # Проверяем, есть ли один и тот же штамм в разных местах хранения
        if len(unique_strains) == 1 and len(sample_list) > 1:
            patterns['same_strain_different_storage'] += 1
            if len(examples['same_strain_different_storage']) < 3:
                examples['same_strain_different_storage'].append({
                    'number': number,
                    'samples': sample_list,
                    'strain': strain_names[0]
                })
        
        # Проверяем, есть ли вариации одного штамма (например, с суффиксами)
        elif len(unique_strains) > 1:
            base_names = set()
            for strain_name in unique_strains:
                # Извлекаем базовое имя штамма (до первого пробела или дефиса)
                base_name = strain_name.split(' ')[0].split('-')[0]
                base_names.add(base_name)
            
            if len(base_names) == 1:
                patterns['strain_variations'] += 1
                if len(examples['strain_variations']) < 3:
                    examples['strain_variations'].append({
                        'number': number,
                        'samples': sample_list,
                        'strains': list(unique_strains)
                    })
            else:
                patterns['different_strains_same_base'] += 1
                if len(examples['different_strains_same_base']) < 3:
                    examples['different_strains_same_base'].append({
                        'number': number,
                        'samples': sample_list,
                        'strains': list(unique_strains)
                    })
    
    # Выводим статистику паттернов
    print("📈 Паттерны дублирования:")
    print(f"   🔄 Один штамм в разных местах: {patterns['same_strain_different_storage']}")
    print(f"   🧬 Вариации одного штамма: {patterns['strain_variations']}")
    print(f"   🔀 Разные штаммы с одним номером: {patterns['different_strains_same_base']}")
    print()
    
    # Показываем примеры
    print("💡 Примеры паттернов:")
    print("-" * 40)
    
    if examples['same_strain_different_storage']:
        print("\n🔄 Один штамм в разных местах хранения:")
        for example in examples['same_strain_different_storage']:
            print(f"   Номер '{example['number']}' - {example['strain']}")
            for sample in example['samples']:
                storage_info = f"Box {sample.storage.box_id}, Cell {sample.storage.cell_id}" if sample.storage else "No storage"
                print(f"      ID {sample.id}: {storage_info}")
            print()
    
    if examples['strain_variations']:
        print("\n🧬 Вариации одного штамма:")
        for example in examples['strain_variations']:
            print(f"   Номер '{example['number']}':")
            for strain in example['strains']:
                print(f"      - {strain}")
            print()
    
    if examples['different_strains_same_base']:
        print("\n🔀 Разные штаммы с одним номером:")
        for example in examples['different_strains_same_base']:
            print(f"   Номер '{example['number']}':")
            for strain in example['strains']:
                print(f"      - {strain}")
            print()

def analyze_storage_distribution():
    """Анализируем распределение дубликатов по хранилищам"""
    print("\n📦 Анализ распределения по хранилищам:")
    print("=" * 50)
    
    # Берем несколько примеров с большим количеством дубликатов
    top_duplicates = Sample.objects.values('original_sample_number').annotate(
        count=django.db.models.Count('id')
    ).filter(count__gt=10).order_by('-count')[:3]
    
    for dup in top_duplicates:
        number = dup['original_sample_number']
        count = dup['count']
        
        print(f"\n📌 Номер '{number}' ({count} образцов):")
        
        samples = Sample.objects.filter(original_sample_number=number).select_related('storage')
        
        # Группируем по боксам
        boxes = defaultdict(list)
        for sample in samples:
            if sample.storage:
                box_key = f"Box {sample.storage.box_id}"
                boxes[box_key].append(sample)
        
        for box, box_samples in boxes.items():
            print(f"   {box}: {len(box_samples)} образцов")
            # Показываем первые несколько ячеек
            cells = [f"Cell {s.storage.cell_id}" for s in box_samples[:5]]
            if len(box_samples) > 5:
                cells.append(f"... и еще {len(box_samples) - 5}")
            print(f"      Ячейки: {', '.join(cells)}")

def suggest_solutions():
    """Предлагаем решения для проблемы дублирования"""
    print("\n💡 Рекомендации по решению проблемы дублирования:")
    print("=" * 60)
    
    print("1️⃣ Возможные причины дублирования:")
    print("   • Один образец хранится в нескольких экземплярах")
    print("   • Разные обработки одного образца (например, HS - heat shock)")
    print("   • Разные штаммы из одного источника")
    print("   • Ошибки в нумерации при импорте данных")
    print()
    
    print("2️⃣ Предлагаемые решения:")
    print("   • Добавить поле 'replica_number' или 'copy_number'")
    print("   • Создать составной ключ: original_sample_number + replica")
    print("   • Добавить поле 'sample_type' (original, replica, processed)")
    print("   • Улучшить систему нумерации для уникальности")
    print()
    
    print("3️⃣ Рекомендации для базы данных:")
    print("   • Рассмотреть создание уникального индекса на комбинацию полей")
    print("   • Добавить валидацию на уровне приложения")
    print("   • Создать отчеты для мониторинга дубликатов")

if __name__ == "__main__":
    detailed_duplicate_analysis()
    analyze_storage_distribution()
    suggest_solutions()