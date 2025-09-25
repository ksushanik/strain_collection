#!/usr/bin/env python
import os
import sys
import django
import re

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strain_tracker_project.settings')
django.setup()

from sample_management.models import Sample
from scripts.normalize_text import normalize_cyrillic_to_latin

def find_encoding_issues():
    print("🔍 Поиск проблем с кодировкой в базе данных")
    print("=" * 60)
    
    # Получаем все образцы с непустым original_sample_number
    samples_with_numbers = Sample.objects.filter(
        original_sample_number__isnull=False
    ).exclude(original_sample_number='')
    
    print(f"📊 Всего образцов с номерами: {samples_with_numbers.count()}")
    print()
    
    issues_found = []
    
    for sample in samples_with_numbers:
        original_value = sample.original_sample_number
        normalized_value = normalize_cyrillic_to_latin(original_value)
        
        # Если значения отличаются, значит есть кириллические символы
        if original_value != normalized_value:
            issues_found.append({
                'id': sample.id,
                'original': original_value,
                'normalized': normalized_value,
                'original_codes': [ord(c) for c in original_value],
                'normalized_codes': [ord(c) for c in normalized_value]
            })
    
    print(f"🚨 Найдено проблем с кодировкой: {len(issues_found)}")
    print()
    
    if issues_found:
        print("📋 Детали проблем:")
        print("-" * 60)
        
        for issue in issues_found:
            print(f"🔸 Образец ID: {issue['id']}")
            print(f"   Текущее значение: '{issue['original']}'")
            print(f"   Unicode коды: {issue['original_codes']}")
            print(f"   Должно быть: '{issue['normalized']}'")
            print(f"   Unicode коды: {issue['normalized_codes']}")
            
            # Показываем, какие именно символы проблемные
            problem_chars = []
            for i, (orig_char, norm_char) in enumerate(zip(issue['original'], issue['normalized'])):
                if orig_char != norm_char:
                    problem_chars.append(f"позиция {i}: '{orig_char}' (U+{ord(orig_char):04X}) -> '{norm_char}' (U+{ord(norm_char):04X})")
            
            if problem_chars:
                print(f"   Проблемные символы: {', '.join(problem_chars)}")
            print()
    
    # Статистика по типам проблем
    if issues_found:
        print("📈 Статистика проблем:")
        print("-" * 30)
        
        cyrillic_chars_found = set()
        for issue in issues_found:
            for char in issue['original']:
                if char != normalize_cyrillic_to_latin(char):
                    cyrillic_chars_found.add(char)
        
        print(f"   Уникальные кириллические символы: {len(cyrillic_chars_found)}")
        for char in sorted(cyrillic_chars_found):
            latin_equivalent = normalize_cyrillic_to_latin(char)
            print(f"     '{char}' (U+{ord(char):04X}) -> '{latin_equivalent}' (U+{ord(latin_equivalent):04X})")
        print()
    
    return issues_found

def preview_fix():
    """Показывает, что будет исправлено"""
    issues = find_encoding_issues()
    
    if not issues:
        print("✅ Проблем с кодировкой не найдено!")
        return
    
    print("🔧 Предварительный просмотр исправлений:")
    print("=" * 50)
    
    for issue in issues:
        print(f"UPDATE sample_management_sample SET original_sample_number = '{issue['normalized']}' WHERE id = {issue['id']};")
    
    print()
    print(f"💡 Всего будет обновлено записей: {len(issues)}")

if __name__ == "__main__":
    preview_fix()