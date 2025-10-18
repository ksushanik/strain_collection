"""
Базовые тесты для collection_manager приложения
"""

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status
from django.db import transaction
import json

from reference_data.models import IndexLetter, Location, Source, SourceType, SourceCategory, GrowthMedium
from storage_management.models import Storage
from strain_management.models import Strain
from sample_management.models import Sample, SampleGrowthMedia

from .api import create_sample, bulk_assign_cells
from audit_logging.models import ChangeLog
from .utils import log_change

class ModelTestCase(TestCase):
    """Тесты для моделей"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.index_letter = IndexLetter.objects.create(letter_value="A")
        self.location = Location.objects.create(name="Тестовое местоположение")
        self.source_type = SourceType.objects.create(name="Тестовый тип")
        self.source_category = SourceCategory.objects.create(name="Тестовая категория")
        self.source = Source.objects.create(
            organism_name="Тестовый организм",
            source_type=self.source_type,
            category=self.source_category
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
        self.assertEqual(self.source.source_type, self.source_type)
        self.assertEqual(self.source.category, self.source_category)
    
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
        """Тест получения списка образцов через collection_manager API"""
        response = self.client.get('/api/samples/')  # Это идет в sample_management
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # sample_management возвращает пагинированный ответ
        self.assertIn('results', data)
    

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


class QuickFixesTestCase(TestCase):
    """Тесты быстрых исправлений, добавленных после аудита."""

    def setUp(self):
        self.request_factory = RequestFactory()
        self.api_factory = APIRequestFactory()

    def test_log_change_normalizes_content_type(self):
        """Проверяем, что content_type приводится к нижнему регистру."""
        request = self.request_factory.get("/")
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        log_change(
            request=request,
            content_type="Sample",
            object_id=1,
            action="CREATE",
        )

        entry = ChangeLog.objects.latest("id")
        self.assertEqual(entry.content_type, "sample")

    def test_create_sample_adds_growth_media_once(self):
        """Убеждаемся, что связи SampleGrowthMedia не дублируются."""
        growth_medium = GrowthMedium.objects.create(name="Test Medium")

        request = self.api_factory.post(
            "/api/samples/create/",
            {"growth_media_ids": [growth_medium.id]},
            format="json",
        )

        response = create_sample(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        sample_id = response.data["id"]
        count = SampleGrowthMedia.objects.filter(
            sample_id=sample_id, growth_medium=growth_medium
        ).count()
        self.assertEqual(count, 1)

    def test_bulk_assign_cells_uses_transaction_and_logs_sample(self):
        """Проверяем, что массовое размещение назначает ячейку и пишет лог."""
        storage = Storage.objects.create(box_id="BOX1", cell_id="A1")
        sample = Sample.objects.create()

        request = self.api_factory.post(
            "/api/storage/boxes/BOX1/cells/bulk-assign/",
            {"assignments": [{"cell_id": "A1", "sample_id": sample.id}]},
            format="json",
        )

        response = bulk_assign_cells(request, box_id="BOX1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        sample.refresh_from_db()
        self.assertEqual(sample.storage_id, storage.id)
        entry = ChangeLog.objects.latest("id")
        self.assertEqual(entry.content_type, "sample")
