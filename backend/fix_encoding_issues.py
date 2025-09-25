#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strain_tracker_project.settings')
django.setup()

from sample_management.models import Sample
from scripts.normalize_text import normalize_cyrillic_to_latin
from django.db import transaction

def fix_encoding_issues():
    print("🔧 Исправление проблем с кодировкой в базе данных")
    print("=" * 60)
    
    # Получаем все образцы с непустым original_sample_number
    samples_with_numbers = Sample.objects.filter(
        original_sample_number__isnull=False
    ).exclude(original_sample_number='')
    
    print(f"📊 Всего образцов с номерами: {samples_with_numbers.count()}")
    
    issues_to_fix = []
    
    for sample in samples_with_numbers:
        original_value = sample.original_sample_number
        normalized_value = normalize_cyrillic_to_latin(original_value)
        
        # Если значения отличаются, значит есть кириллические символы
        if original_value != normalized_value:
            issues_to_fix.append({
                'sample': sample,
                'original': original_value,
                'normalized': normalized_value
            })
    
    print(f"🚨 Найдено проблем для исправления: {len(issues_to_fix)}")
    
    if not issues_to_fix:
        print("✅ Проблем с кодировкой не найдено!")
        return
    
    print("\n📋 Будут исправлены следующие записи:")
    print("-" * 60)
    
    for issue in issues_to_fix:
        print(f"🔸 Образец ID: {issue['sample'].id}")
        print(f"   '{issue['original']}' -> '{issue['normalized']}'")
    
    # Подтверждение
    print(f"\n❓ Исправить {len(issues_to_fix)} записей? (y/N): ", end="")
    confirmation = input().strip().lower()
    
    if confirmation not in ['y', 'yes', 'да', 'д']:
        print("❌ Операция отменена")
        return
    
    # Исправление в транзакции
    try:
        with transaction.atomic():
            fixed_count = 0
            
            for issue in issues_to_fix:
                old_value = issue['sample'].original_sample_number
                new_value = issue['normalized']
                
                # Обновляем значение
                issue['sample'].original_sample_number = new_value
                issue['sample'].save(update_fields=['original_sample_number'])
                
                print(f"✅ Образец ID {issue['sample'].id}: '{old_value}' -> '{new_value}'")
                fixed_count += 1
            
            print(f"\n🎉 Успешно исправлено записей: {fixed_count}")
            
    except Exception as e:
        print(f"❌ Ошибка при исправлении: {e}")
        return
    
    # Проверяем результат
    print("\n🔍 Проверка результата...")
    remaining_issues = []
    
    for sample in Sample.objects.filter(original_sample_number__isnull=False).exclude(original_sample_number=''):
        original_value = sample.original_sample_number
        normalized_value = normalize_cyrillic_to_latin(original_value)
        
        if original_value != normalized_value:
            remaining_issues.append(sample)
    
    if remaining_issues:
        print(f"⚠️  Остались проблемы: {len(remaining_issues)}")
    else:
        print("✅ Все проблемы с кодировкой исправлены!")

def verify_sample_55():
    """Специальная проверка для образца 55"""
    print("\n🔍 Специальная проверка образца 55:")
    print("-" * 40)
    
    try:
        sample_55 = Sample.objects.get(id=55)
        print(f"📋 Образец ID 55:")
        print(f"   original_sample_number: '{sample_55.original_sample_number}'")
        print(f"   Unicode коды: {[ord(c) for c in sample_55.original_sample_number]}")
        
        # Проверяем, можем ли найти по латинскому варианту
        latin_samples = Sample.objects.filter(original_sample_number='11A')
        print(f"   Найдено образцов с '11A': {latin_samples.count()}")
        
        if latin_samples.exists():
            print("✅ Образец теперь можно найти по латинскому номеру!")
        else:
            print("❌ Образец все еще не найден по латинскому номеру")
            
    except Sample.DoesNotExist:
        print("❌ Образец с ID 55 не найден")

if __name__ == "__main__":
    fix_encoding_issues()
    verify_sample_55()