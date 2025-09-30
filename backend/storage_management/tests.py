"""
Тесты для модуля storage_management
"""

import json
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Storage, StorageBox
from sample_management.models import Sample
from strain_management.models import Strain


class StorageModelTests(TestCase):
    """Тесты модели Storage (ячейки)"""
    
    def test_storage_creation(self):
        """Тест создания ячейки хранения"""
        storage = Storage.objects.create(
            box_id='BOX001',
            cell_id='A1'
        )
        
        self.assertEqual(storage.box_id, 'BOX001')
        self.assertEqual(storage.cell_id, 'A1')
        self.assertEqual(str(storage), 'Бокс BOX001, ячейка A1')
    
    def test_storage_cell_id_validation(self):
        """Тест валидации cell_id"""
        # Правильный формат
        storage = Storage.objects.create(
            box_id='BOX002',
            cell_id='B12'
        )
        self.assertEqual(storage.cell_id, 'B12')
        
        # Неправильный формат должен вызывать ошибку валидации
        with self.assertRaises(Exception):
            storage = Storage(
                box_id='BOX003',
                cell_id='invalid'
            )
            storage.full_clean()  # Вызывает валидацию
    
    def test_storage_unique_together(self):
        """Тест уникальности комбинации box_id + cell_id"""
        Storage.objects.create(
            box_id='BOX004',
            cell_id='C3'
        )
        
        # Попытка создать дубликат должна вызвать ошибку
        with self.assertRaises(Exception):
            Storage.objects.create(
                box_id='BOX004',
                cell_id='C3'
            )


class StorageBoxModelTests(TestCase):
    """Тесты модели StorageBox (боксы)"""
    
    def test_storage_box_creation(self):
        """Тест создания бокса"""
        box = StorageBox.objects.create(
            box_id='BOX001',
            rows=8,
            cols=12,
            description='Тестовый бокс'
        )
        
        self.assertEqual(box.box_id, 'BOX001')
        self.assertEqual(box.rows, 8)
        self.assertEqual(box.cols, 12)
        self.assertEqual(box.description, 'Тестовый бокс')
        self.assertEqual(str(box), 'Бокс BOX001 (8×12)')
    
    def test_storage_box_required_fields(self):
        """Тест обязательных полей бокса"""
        from django.core.exceptions import ValidationError
        from django.db import IntegrityError
        
        # Тест создания без box_id (должно вызвать ошибку)
        with self.assertRaises((ValidationError, IntegrityError)):
            box = StorageBox(
                # Пропускаем обязательное поле box_id
                rows=8,
                cols=12
            )
            box.full_clean()  # Вызываем валидацию
            box.save()
    
    def test_storage_box_unique_box_id(self):
        """Тест уникальности box_id"""
        StorageBox.objects.create(
            box_id='BOX002',
            rows=8,
            cols=12
        )
        
        # Попытка создать бокс с тем же box_id должна вызвать ошибку
        with self.assertRaises(Exception):
            StorageBox.objects.create(
                box_id='BOX002',
                rows=10,
                cols=10
            )



class StorageAPITests(TestCase):
    """API coverage for storage box operations."""

    def setUp(self):
        self.client = APIClient()

        self.storage_box = StorageBox.objects.create(
            box_id='API_BOX001',
            rows=8,
            cols=12,
            description='API test box'
        )

        self.storage1 = Storage.objects.create(box_id='API_BOX001', cell_id='A1')
        self.storage2 = Storage.objects.create(box_id='API_BOX001', cell_id='A2')

        self.strain = Strain.objects.create(short_code='API_STR001', identifier='API Test Strain')
        self.sample = Sample.objects.create(storage=self.storage1, strain=self.strain)

    def test_list_storages_endpoint(self):
        response = self.client.get('/api/storage/storages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)

    def test_create_storage_endpoint(self):
        data = {'box_id': 'API_BOX002', 'cell_id': 'B1'}
        response = self.client.post('/api/storage/storages/create/', json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Storage.objects.filter(box_id='API_BOX002', cell_id='B1').exists())

    def test_list_storage_boxes_endpoint(self):
        response = self.client.get('/api/storage/boxes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(response.data['count'], 1)

    def test_create_storage_box_generates_identifier(self):
        payload = {'rows': 2, 'cols': 3}
        response = self.client.post('/api/storage/boxes/create/', json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        box_data = response.data['box']
        self.assertTrue(box_data['generated_id'])
        self.assertEqual(box_data['cells_created'], 6)
        self.assertTrue(StorageBox.objects.filter(box_id=box_data['box_id']).exists())

    def test_create_storage_box_with_custom_identifier(self):
        payload = {'box_id': 'API_CUSTOM', 'rows': 3, 'cols': 3}
        response = self.client.post('/api/storage/boxes/create/', json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        box_data = response.data['box']
        self.assertFalse(box_data['generated_id'])
        self.assertEqual(box_data['box_id'], 'API_CUSTOM')

    def test_get_storage_box_endpoint(self):
        response = self.client.get(f"/api/storage/boxes/{self.storage_box.box_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('statistics', response.data)
        self.assertEqual(response.data['box_id'], self.storage_box.box_id)

    def test_update_storage_box_endpoint(self):
        payload = {'description': 'Updated description'}
        response = self.client.put(
            f"/api/storage/boxes/{self.storage_box.box_id}/update/",
            json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.storage_box.refresh_from_db()
        self.assertEqual(self.storage_box.description, 'Updated description')

    def test_delete_storage_box_requires_force(self):
        response = self.client.delete(f"/api/storage/boxes/{self.storage_box.box_id}/delete/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('can_force_delete', response.data)
        self.assertTrue(StorageBox.objects.filter(box_id=self.storage_box.box_id).exists())

    def test_delete_storage_box_force(self):
        response = self.client.delete(f"/api/storage/boxes/{self.storage_box.box_id}/delete/?force=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(StorageBox.objects.filter(box_id=self.storage_box.box_id).exists())
        self.assertFalse(Storage.objects.filter(box_id=self.storage_box.box_id).exists())
        self.sample.refresh_from_db()
        self.assertIsNone(self.sample.storage)

    def test_storage_overview_endpoint(self):
        response = self.client.get('/api/storage/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('boxes', response.data)
        first_box = response.data['boxes'][0]
        self.assertIn('total_cells', first_box)
        self.assertIn('free_cells', first_box)

    def test_storage_summary_endpoint(self):
        response = self.client.get('/api/storage/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('free_cells', response.data)
        self.assertIn('boxes', response.data)

    def test_storage_box_details_endpoint(self):
        response = self.client.get(f"/api/storage/boxes/{self.storage_box.box_id}/detail/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cells_grid', response.data)
        self.assertEqual(response.data['occupied_cells'], 1)
        self.assertGreater(len(response.data['cells_grid']), 0)
class StorageIntegrationTests(TestCase):
    """Интеграционные тесты для storage_management"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_box_and_storage_relationship(self):
        """Тест связи между боксами и ячейками"""
        # Создаем бокс
        box = StorageBox.objects.create(
            box_id='INT_BOX001',
            rows=5,
            cols=5,
            description='Интеграционный тест'
        )
        
        # Создаем ячейки для этого бокса
        storage1 = Storage.objects.create(
            box_id='INT_BOX001',
            cell_id='A1'
        )
        storage2 = Storage.objects.create(
            box_id='INT_BOX001',
            cell_id='A2'
        )
        
        # Проверяем, что ячейки связаны с боксом
        box_storages = Storage.objects.filter(box_id='INT_BOX001')
        self.assertEqual(box_storages.count(), 2)
        self.assertIn(storage1, box_storages)
        self.assertIn(storage2, box_storages)
    
    def test_storage_search_and_filtering(self):
        """Тест поиска и фильтрации ячеек"""
        # Создаем тестовые данные
        StorageBox.objects.create(
            box_id='SEARCH_BOX001',
            rows=8,
            cols=12
        )
        
        Storage.objects.create(
            box_id='SEARCH_BOX001',
            cell_id='A1'
        )
        Storage.objects.create(
            box_id='SEARCH_BOX001',
            cell_id='B2'
        )
        Storage.objects.create(
            box_id='OTHER_BOX',
            cell_id='A1'
        )
        
        # Тестируем фильтрацию по box_id
        search_results = Storage.objects.filter(box_id='SEARCH_BOX001')
        self.assertEqual(search_results.count(), 2)
        
        # Тестируем фильтрацию по cell_id
        a1_results = Storage.objects.filter(cell_id='A1')
        self.assertEqual(a1_results.count(), 2)  # A1 есть в двух разных боксах
