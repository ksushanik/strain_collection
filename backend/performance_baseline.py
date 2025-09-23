#!/usr/bin/env python
"""
Скрипт для определения baseline метрик производительности
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
from django.test.utils import setup_test_environment, teardown_test_environment
from django.test import Client
from django.db import connection, transaction

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strain_tracker_project.settings')
django.setup()

from collection_manager.models import (
    Strain, Sample, Storage, IndexLetter, Location, Source,
    StorageBox, IUKColor, AmylaseVariant, GrowthMedium
)


class PerformanceBaseline:
    """Класс для измерения baseline метрик производительности"""
    
    def __init__(self):
        self.client = Client()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'database_metrics': {},
            'api_metrics': {},
            'model_metrics': {},
            'memory_metrics': {},
            'summary': {}
        }
    
    def setup_test_data(self, num_strains: int = 1000, num_samples: int = 5000):
        """Создание тестовых данных"""
        print(f"Создание тестовых данных: {num_strains} штаммов, {num_samples} образцов...")
        
        start_time = time.time()
        
        with transaction.atomic():
            # Создаем базовые справочные данные
            index_letters = []
            for letter in 'ABCDEFGHIJ':
                index_letter, created = IndexLetter.objects.get_or_create(letter_value=letter)
                index_letters.append(index_letter)
            
            locations = []
            for i in range(10):
                location, created = Location.objects.get_or_create(name=f"Местоположение {i+1}")
                locations.append(location)
            
            sources = []
            for i in range(20):
                source, created = Source.objects.get_or_create(
                    organism_name=f"Организм {i+1}",
                    defaults={
                        'source_type': f"Тип {i+1}",
                        'category': f"Категория {i+1}"
                    }
                )
                sources.append(source)
            
            # Создаем боксы для хранения
            boxes = []
            for i in range(50):
                box, created = StorageBox.objects.get_or_create(
                    box_id=f"BOX_{i+1:03d}",
                    defaults={
                        'rows': 8,
                        'cols': 12,
                        'description': f"Тестовый бокс {i+1}"
                    }
                )
                boxes.append(box)
            
            # Создаем ячейки хранения
            storages = []
            for box in boxes[:10]:  # Используем первые 10 боксов
                for row in 'ABCDEFGH':
                    for col in range(1, 13):
                        storage, created = Storage.objects.get_or_create(
                            box_id=box.box_id,
                            cell_id=f"{row}{col}"
                        )
                        storages.append(storage)
            
            # Создаем штаммы
            strains = []
            for i in range(num_strains):
                strains.append(Strain(
                    short_code=f"BASELINE_{i+1:05d}",
                    identifier=f"Baseline штамм {i+1}",
                    rrna_taxonomy=f"Baseline таксономия {i+1}",
                    name_alt=f"Альтернативное название {i+1}" if i % 3 == 0 else None
                ))
            
            Strain.objects.bulk_create(strains)
            
            # Создаем образцы
            created_strains = list(Strain.objects.filter(short_code__startswith="BASELINE_"))
            samples = []
            
            for i in range(num_samples):
                strain = created_strains[i % len(created_strains)]
                index_letter = index_letters[i % len(index_letters)]
                location = locations[i % len(locations)]
                source = sources[i % len(sources)]
                storage = storages[i % len(storages)]
                
                samples.append(Sample(
                    strain=strain,
                    index_letter=index_letter,
                    location=location,
                    source=source,
                    storage=storage,
                    original_sample_number=f"{i+1:05d}",
                    is_identified=i % 2 == 0,
                    has_photo=i % 3 == 0
                ))
            
            Sample.objects.bulk_create(samples)
        
        setup_time = time.time() - start_time
        print(f"Тестовые данные созданы за {setup_time:.2f} секунд")
        
        return {
            'setup_time': setup_time,
            'strains_created': num_strains,
            'samples_created': num_samples
        }
    
    def measure_database_performance(self) -> Dict[str, Any]:
        """Измерение производительности базы данных"""
        print("Измерение производительности базы данных...")
        
        metrics = {}
        
        # Тест простых запросов
        queries = [
            ("count_strains", "SELECT COUNT(*) FROM collection_manager_strain"),
            ("count_samples", "SELECT COUNT(*) FROM collection_manager_sample"),
            ("count_storage", "SELECT COUNT(*) FROM collection_manager_storage"),
        ]
        
        for name, query in queries:
            times = []
            for _ in range(5):
                start_time = time.time()
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    cursor.fetchone()
                times.append(time.time() - start_time)
            
            metrics[name] = {
                'avg_time': statistics.mean(times),
                'min_time': min(times),
                'max_time': max(times),
                'std_dev': statistics.stdev(times) if len(times) > 1 else 0
            }
        
        # Тест сложных запросов с JOIN
        complex_queries = [
            ("samples_with_strains", """
                SELECT s.id, s.original_sample_number, st.short_code, st.identifier
                FROM collection_manager_sample s
                JOIN collection_manager_strain st ON s.strain_id = st.id
                LIMIT 100
            """),
            ("samples_full_info", """
                SELECT s.id, s.original_sample_number, st.short_code, 
                       l.name as location, src.organism_name, stor.box_id, stor.cell_id
                FROM collection_manager_sample s
                JOIN collection_manager_strain st ON s.strain_id = st.id
                JOIN collection_manager_location l ON s.location_id = l.id
                JOIN collection_manager_source src ON s.source_id = src.id
                JOIN collection_manager_storage stor ON s.storage_id = stor.id
                LIMIT 100
            """)
        ]
        
        for name, query in complex_queries:
            times = []
            for _ in range(3):
                start_time = time.time()
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    cursor.fetchall()
                times.append(time.time() - start_time)
            
            metrics[name] = {
                'avg_time': statistics.mean(times),
                'min_time': min(times),
                'max_time': max(times)
            }
        
        return metrics
    
    def measure_api_performance(self) -> Dict[str, Any]:
        """Измерение производительности API"""
        print("Измерение производительности API...")
        
        endpoints = [
            ('/api/', 'api_status'),
            ('/api/strains/', 'strains_list'),
            ('/api/samples/', 'samples_list'),
            ('/api/storage/', 'storage_list'),
            ('/api/reference-data/', 'reference_data'),
        ]
        
        metrics = {}
        
        for endpoint, name in endpoints:
            times = []
            status_codes = []
            
            for _ in range(10):
                start_time = time.time()
                response = self.client.get(endpoint)
                response_time = time.time() - start_time
                
                times.append(response_time)
                status_codes.append(response.status_code)
            
            metrics[name] = {
                'avg_response_time': statistics.mean(times),
                'min_response_time': min(times),
                'max_response_time': max(times),
                'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
                'success_rate': sum(1 for code in status_codes if code == 200) / len(status_codes),
                'status_codes': list(set(status_codes))
            }
        
        return metrics
    
    def measure_model_performance(self) -> Dict[str, Any]:
        """Измерение производительности моделей Django"""
        print("Измерение производительности моделей...")
        
        metrics = {}
        
        # Тест создания объектов
        start_time = time.time()
        test_strains = []
        for i in range(100):
            test_strains.append(Strain(
                short_code=f"PERF_TEST_{i:03d}",
                identifier=f"Performance test strain {i}"
            ))
        
        with transaction.atomic():
            Strain.objects.bulk_create(test_strains)
        
        metrics['bulk_create_100_strains'] = time.time() - start_time
        
        # Тест запросов ORM
        orm_tests = [
            ('all_strains', lambda: list(Strain.objects.all())),
            ('filter_strains', lambda: list(Strain.objects.filter(short_code__startswith="BASELINE_")[:100])),
            ('select_related', lambda: list(Sample.objects.select_related('strain', 'location', 'source')[:100])),
            ('prefetch_related', lambda: list(Strain.objects.prefetch_related('sample_set')[:50])),
        ]
        
        for name, query_func in orm_tests:
            times = []
            for _ in range(3):
                start_time = time.time()
                result = query_func()
                times.append(time.time() - start_time)
            
            metrics[name] = {
                'avg_time': statistics.mean(times),
                'min_time': min(times),
                'max_time': max(times)
            }
        
        # Очистка тестовых данных
        Strain.objects.filter(short_code__startswith="PERF_TEST_").delete()
        
        return metrics
    
    def measure_memory_usage(self) -> Dict[str, Any]:
        """Измерение использования памяти"""
        print("Измерение использования памяти...")
        
        try:
            import psutil
            process = psutil.Process()
            
            return {
                'memory_percent': process.memory_percent(),
                'memory_info': process.memory_info()._asdict(),
                'cpu_percent': process.cpu_percent(interval=1)
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Запуск всех тестов производительности"""
        print("Запуск baseline тестов производительности...")
        print("=" * 50)
        
        # Создание тестовых данных
        setup_results = self.setup_test_data()
        self.results['setup'] = setup_results
        
        # Измерение производительности
        self.results['database_metrics'] = self.measure_database_performance()
        self.results['api_metrics'] = self.measure_api_performance()
        self.results['model_metrics'] = self.measure_model_performance()
        self.results['memory_metrics'] = self.measure_memory_usage()
        
        # Создание сводки
        self.results['summary'] = {
            'total_strains': Strain.objects.count(),
            'total_samples': Sample.objects.count(),
            'avg_api_response_time': statistics.mean([
                metrics['avg_response_time'] 
                for metrics in self.results['api_metrics'].values()
                if 'avg_response_time' in metrics
            ]),
            'avg_db_query_time': statistics.mean([
                metrics['avg_time']
                for metrics in self.results['database_metrics'].values()
                if 'avg_time' in metrics
            ])
        }
        
        return self.results
    
    def save_results(self, filename: str = None):
        """Сохранение результатов в файл"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_baseline_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Результаты сохранены в {filename}")
    
    def print_summary(self):
        """Вывод краткой сводки результатов"""
        print("\n" + "=" * 50)
        print("СВОДКА РЕЗУЛЬТАТОВ BASELINE ТЕСТИРОВАНИЯ")
        print("=" * 50)
        
        summary = self.results['summary']
        print(f"Общее количество штаммов: {summary['total_strains']}")
        print(f"Общее количество образцов: {summary['total_samples']}")
        print(f"Среднее время ответа API: {summary['avg_api_response_time']:.3f}s")
        print(f"Среднее время запроса к БД: {summary['avg_db_query_time']:.3f}s")
        
        print("\nТоп медленных операций:")
        
        # API операции
        api_times = [(name, metrics['avg_response_time']) 
                    for name, metrics in self.results['api_metrics'].items()
                    if 'avg_response_time' in metrics]
        api_times.sort(key=lambda x: x[1], reverse=True)
        
        print("API endpoints:")
        for name, time_val in api_times[:3]:
            print(f"  {name}: {time_val:.3f}s")
        
        # DB операции
        db_times = [(name, metrics['avg_time'])
                   for name, metrics in self.results['database_metrics'].items()
                   if 'avg_time' in metrics]
        db_times.sort(key=lambda x: x[1], reverse=True)
        
        print("Database queries:")
        for name, time_val in db_times[:3]:
            print(f"  {name}: {time_val:.3f}s")


def main():
    """Главная функция"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Использование: python performance_baseline.py [--small|--medium|--large]")
        print("  --small:  1000 штаммов, 5000 образцов")
        print("  --medium: 5000 штаммов, 25000 образцов")
        print("  --large:  10000 штаммов, 50000 образцов")
        return
    
    # Определение размера тестовых данных
    if len(sys.argv) > 1:
        size = sys.argv[1]
        if size == '--small':
            num_strains, num_samples = 1000, 5000
        elif size == '--medium':
            num_strains, num_samples = 5000, 25000
        elif size == '--large':
            num_strains, num_samples = 10000, 50000
        else:
            num_strains, num_samples = 1000, 5000
    else:
        num_strains, num_samples = 1000, 5000
    
    baseline = PerformanceBaseline()
    
    try:
        # Очистка предыдущих тестовых данных
        print("Очистка предыдущих тестовых данных...")
        Sample.objects.filter(strain__short_code__startswith="BASELINE_").delete()
        Strain.objects.filter(short_code__startswith="BASELINE_").delete()
        
        # Запуск тестов
        baseline.setup_test_data(num_strains, num_samples)
        results = baseline.run_all_tests()
        
        # Сохранение и вывод результатов
        baseline.save_results()
        baseline.print_summary()
        
    except Exception as e:
        print(f"Ошибка при выполнении тестов: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Очистка тестовых данных
        print("\nОчистка тестовых данных...")
        try:
            Sample.objects.filter(strain__short_code__startswith="BASELINE_").delete()
            Strain.objects.filter(short_code__startswith="BASELINE_").delete()
            print("Тестовые данные очищены")
        except Exception as e:
            print(f"Ошибка при очистке: {e}")


if __name__ == "__main__":
    main()