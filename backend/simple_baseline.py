#!/usr/bin/env python
"""
Простой скрипт для определения baseline метрик производительности
"""

import os
import sys
import time
import json
import statistics
from datetime import datetime
from typing import Dict, List, Any

import django
from django.conf import settings
from django.test import Client
from django.db import connection

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strain_tracker_project.settings')
django.setup()

from collection_manager.models import Strain, Sample, Storage, StorageBox


def measure_api_performance():
    """Измерение производительности API"""
    print("Измерение производительности API...")
    
    client = Client()
    endpoints = [
        ('/api/', 'api_status'),
        ('/api/strains/', 'strains_list'),
        ('/api/samples/', 'samples_list'),
        ('/api/storage/', 'storage_list'),
        ('/api/reference-data/', 'reference_data'),
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        times = []
        status_codes = []
        
        print(f"  Тестирование {endpoint}...")
        
        for i in range(5):
            start_time = time.time()
            try:
                response = client.get(endpoint)
                response_time = time.time() - start_time
                
                times.append(response_time)
                status_codes.append(response.status_code)
                
                print(f"    Попытка {i+1}: {response_time:.3f}s (статус: {response.status_code})")
            except Exception as e:
                print(f"    Ошибка в попытке {i+1}: {e}")
                continue
        
        if times:
            results[name] = {
                'avg_response_time': statistics.mean(times),
                'min_response_time': min(times),
                'max_response_time': max(times),
                'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
                'success_rate': sum(1 for code in status_codes if code == 200) / len(status_codes),
                'status_codes': list(set(status_codes))
            }
    
    return results


def measure_database_performance():
    """Измерение производительности базы данных"""
    print("Измерение производительности базы данных...")
    
    queries = [
        ("count_strains", "SELECT COUNT(*) FROM collection_manager_strain"),
        ("count_samples", "SELECT COUNT(*) FROM collection_manager_sample"),
        ("count_storage", "SELECT COUNT(*) FROM collection_manager_storage"),
        ("count_boxes", "SELECT COUNT(*) FROM collection_manager_storagebox"),
    ]
    
    results = {}
    
    for name, query in queries:
        times = []
        print(f"  Тестирование {name}...")
        
        for i in range(3):
            start_time = time.time()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    query_time = time.time() - start_time
                    times.append(query_time)
                    print(f"    Попытка {i+1}: {query_time:.3f}s (результат: {result[0]})")
            except Exception as e:
                print(f"    Ошибка в попытке {i+1}: {e}")
                continue
        
        if times:
            results[name] = {
                'avg_time': statistics.mean(times),
                'min_time': min(times),
                'max_time': max(times)
            }
    
    return results


def get_current_data_stats():
    """Получение статистики по текущим данным"""
    print("Получение статистики по текущим данным...")
    
    try:
        stats = {
            'strains_count': Strain.objects.count(),
            'samples_count': Sample.objects.count(),
            'storage_count': Storage.objects.count(),
            'boxes_count': StorageBox.objects.count(),
        }
        
        print(f"  Штаммы: {stats['strains_count']}")
        print(f"  Образцы: {stats['samples_count']}")
        print(f"  Ячейки хранения: {stats['storage_count']}")
        print(f"  Боксы: {stats['boxes_count']}")
        
        return stats
    except Exception as e:
        print(f"  Ошибка при получении статистики: {e}")
        return {}


def main():
    """Главная функция"""
    print("Запуск простого baseline теста производительности")
    print("=" * 60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'data_stats': {},
        'database_metrics': {},
        'api_metrics': {},
    }
    
    try:
        # Получение статистики данных
        results['data_stats'] = get_current_data_stats()
        
        # Измерение производительности БД
        results['database_metrics'] = measure_database_performance()
        
        # Измерение производительности API
        results['api_metrics'] = measure_api_performance()
        
        # Сохранение результатов
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simple_baseline_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\nРезультаты сохранены в {filename}")
        
        # Вывод сводки
        print("\n" + "=" * 60)
        print("СВОДКА РЕЗУЛЬТАТОВ")
        print("=" * 60)
        
        if results['data_stats']:
            print(f"Данные в системе:")
            for key, value in results['data_stats'].items():
                print(f"  {key}: {value}")
        
        if results['api_metrics']:
            print(f"\nПроизводительность API:")
            api_times = [(name, metrics.get('avg_response_time', 0)) 
                        for name, metrics in results['api_metrics'].items()]
            api_times.sort(key=lambda x: x[1], reverse=True)
            
            for name, time_val in api_times:
                print(f"  {name}: {time_val:.3f}s")
        
        if results['database_metrics']:
            print(f"\nПроизводительность БД:")
            db_times = [(name, metrics.get('avg_time', 0))
                       for name, metrics in results['database_metrics'].items()]
            db_times.sort(key=lambda x: x[1], reverse=True)
            
            for name, time_val in db_times:
                print(f"  {name}: {time_val:.3f}s")
        
        print("\nBaseline тест завершён успешно!")
        
    except Exception as e:
        print(f"Ошибка при выполнении тестов: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()