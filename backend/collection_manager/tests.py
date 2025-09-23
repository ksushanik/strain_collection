"""
Базовые тесты для collection_manager приложения
"""

from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.db import transaction
import json

from .models import (
    IndexLetter, Location, Source, Storage, Strain, Sample,
    StorageBox, IUKColor, AmylaseVariant, GrowthMedium
)


class ModelTestCase(TestCase):
    """Тесты для моделей"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.index_letter = IndexLetter.objects.create(letter_value="A")
        self.location = Location.objects.create(name="Тестовое местоположение")
        self.source = Source.objects.create(
            organism_name="Тестовый организм",
            source_type="Тестовый тип",
            category="Тестовая категория"
        )
        self.storage = Storage.objects.create(box_id="TEST_BOX", cell_id="A1")
        self.strain = Strain.objects.create(
            short_code="TEST001",
            identifier="Тестовый штамм",
            rrna_taxonomy="Тестовая таксономия"
        )
    
    def test_index_letter_creation(self):
        """Тест создания индексной буквы"""
        self.assertEqual(str(self.index_letter), "A")
        self.assertEqual(self.index_letter.letter_value, "A")
    
    def test_location_creation(self):
        """Тест создания местоположения"""
        self.assertEqual(str(self.location), "Тестовое местоположение")
    
    def test_source_creation(self):
        """Тест создания источника"""
        expected_str = "Тестовый организм (Тестовый тип)"
        self.assertEqual(str(self.source), expected_str)
    
    def test_storage_creation(self):
        """Тест создания хранилища"""
        expected_str = "Бокс TEST_BOX, ячейка A1"
        self.assertEqual(str(self.storage), expected_str)
    
    def test_strain_creation(self):
        """Тест создания штамма"""
        expected_str = "TEST001 - Тестовый штамм"
        self.assertEqual(str(self.strain), expected_str)
    
    def test_sample_creation(self):
        """Тест создания образца"""
        sample = Sample.objects.create(
            strain=self.strain,
            index_letter=self.index_letter,
            storage=self.storage,
            source=self.source,
            location=self.location,
            original_sample_number="001"
        )
        expected_str = "TEST001 (001)"
        self.assertEqual(str(sample), expected_str)
    
    def test_storage_box_creation(self):
        """Тест создания бокса"""
        box = StorageBox.objects.create(
            box_id="TEST_BOX_001",
            rows=8,
            cols=12,
            description="Тестовый бокс"
        )
        expected_str = "Бокс TEST_BOX_001 (8×12)"
        self.assertEqual(str(box), expected_str)


class APITestCase(APITestCase):
    """Тесты для API endpoints"""
    
    def setUp(self):
        """Настройка тестовых данных для API"""
        self.client = Client()
        
        # Создаем тестовые данные
        self.strain = Strain.objects.create(
            short_code="API_TEST001",
            identifier="API Тестовый штамм",
            rrna_taxonomy="API Тестовая таксономия"
        )
        
        self.storage = Storage.objects.create(box_id="API_BOX", cell_id="B2")
    
    def test_api_status(self):
        """Тест статуса API"""
        response = self.client.get('/api/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'OK')
        self.assertIn('endpoints', data)
    
    def test_strains_list(self):
        """Тест получения списка штаммов"""
        response = self.client.get('/api/strains/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('strains', data)
        self.assertGreater(len(data['strains']), 0)
    
    def test_samples_list(self):
        """Тест получения списка образцов"""
        response = self.client.get('/api/samples/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('samples', data)
    
    def test_storage_list(self):
        """Тест получения списка хранилищ"""
        response = self.client.get('/api/storage/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('boxes', data)
    
    def test_reference_data(self):
        """Тест получения справочных данных"""
        response = self.client.get('/api/reference-data/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('index_letters', data)
        self.assertIn('locations', data)
        self.assertIn('sources', data)


class IntegrationTestCase(TestCase):
    """Интеграционные тесты"""
    
    def setUp(self):
        """Настройка для интеграционных тестов"""
        self.client = Client()
    
    def test_strain_sample_workflow(self):
        """Тест полного workflow создания штамма и образца"""
        # 1. Создаем штамм через API
        strain_data = {
            "short_code": "WORKFLOW001",
            "identifier": "Workflow тестовый штамм",
            "rrna_taxonomy": "Workflow таксономия"
        }
        
        response = self.client.post(
            '/api/strains/create/',
            data=json.dumps(strain_data),
            content_type='application/json'
        )
        
        # Проверяем успешное создание штамма
        self.assertIn(response.status_code, [200, 201])
        
        # 2. Получаем список штаммов и проверяем наличие созданного
        response = self.client.get('/api/strains/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Ищем наш штамм в списке
        created_strain = None
        for strain in data['strains']:
            if strain['short_code'] == 'WORKFLOW001':
                created_strain = strain
                break
        
        self.assertIsNotNone(created_strain, "Созданный штамм не найден в списке")


class PerformanceTestCase(TestCase):
    """Тесты производительности"""
    
    def test_bulk_strain_creation(self):
        """Тест массового создания штаммов"""
        strains_data = []
        for i in range(100):
            strains_data.append(Strain(
                short_code=f"PERF{i:03d}",
                identifier=f"Performance штамм {i}",
                rrna_taxonomy=f"Performance таксономия {i}"
            ))
        
        # Измеряем время выполнения
        import time
        start_time = time.time()
        
        with transaction.atomic():
            Strain.objects.bulk_create(strains_data)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Проверяем, что операция выполнилась быстро (менее 1 секунды)
        self.assertLess(execution_time, 1.0, 
                       f"Bulk создание заняло слишком много времени: {execution_time:.2f}s")
        
        # Проверяем количество созданных записей
        created_count = Strain.objects.filter(short_code__startswith="PERF").count()
        self.assertEqual(created_count, 100)
    
    def test_api_response_time(self):
        """Тест времени ответа API"""
        import time
        
        # Создаем тестовые данные
        for i in range(50):
            Strain.objects.create(
                short_code=f"SPEED{i:03d}",
                identifier=f"Speed штамм {i}"
            )
        
        # Измеряем время ответа API
        start_time = time.time()
        response = self.client.get('/api/strains/')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Проверяем успешность запроса
        self.assertEqual(response.status_code, 200)
        
        # Проверяем время ответа (должно быть менее 0.5 секунды)
        self.assertLess(response_time, 0.5,
                       f"API ответил слишком медленно: {response_time:.3f}s")


class ValidationTestCase(TestCase):
    """Тесты валидации данных"""
    
    def test_storage_cell_validation(self):
        """Тест валидации формата ячейки хранения"""
        # Правильные форматы
        valid_cells = ["A1", "B12", "Z99"]
        for cell_id in valid_cells:
            storage = Storage(box_id="TEST", cell_id=cell_id)
            try:
                storage.full_clean()  # Вызывает валидацию
            except Exception as e:
                self.fail(f"Валидация не прошла для корректного cell_id '{cell_id}': {e}")
        
        # Неправильные форматы
        invalid_cells = ["1A", "AA1", "a1", "A100", ""]
        for cell_id in invalid_cells:
            storage = Storage(box_id="TEST", cell_id=cell_id)
            with self.assertRaises(Exception, 
                                 msg=f"Валидация должна была провалиться для '{cell_id}'"):
                storage.full_clean()
    
    def test_strain_uniqueness(self):
        """Тест уникальности штаммов"""
        # Создаем первый штамм
        Strain.objects.create(
            short_code="UNIQUE001",
            identifier="Уникальный штамм"
        )
        
        # Пытаемся создать штамм с тем же short_code
        # (если есть ограничение уникальности)
        duplicate_strain = Strain(
            short_code="UNIQUE001",
            identifier="Дублирующий штамм"
        )
        
        # Здесь можно добавить проверку уникальности, если она реализована
        # В текущей модели нет unique=True для short_code