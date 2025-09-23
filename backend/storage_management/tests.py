"""
Тесты для модуля storage_management
"""

import json
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Storage, StorageBox


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
    """Тесты API управления хранилищем"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Создаем тестовый бокс
        self.storage_box = StorageBox.objects.create(
            box_id='API_BOX001',
            rows=8,
            cols=12,
            description='Тестовый бокс для API'
        )
        
        # Создаем тестовые ячейки
        self.storage1 = Storage.objects.create(
            box_id='API_BOX001',
            cell_id='A1'
        )
        self.storage2 = Storage.objects.create(
            box_id='API_BOX001',
            cell_id='A2'
        )
    
    def test_list_storages_endpoint(self):
        """Тест получения списка ячеек"""
        response = self.client.get('/api/storage/storages/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_create_storage_endpoint(self):
        """Тест создания ячейки через API"""
        data = {
            'box_id': 'API_BOX002',
            'cell_id': 'B1'
        }
        
        response = self.client.post('/api/storage/storages/create/', json.dumps(data), content_type='application/json')
        
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Storage.objects.filter(box_id='API_BOX002', cell_id='B1').exists())
    
    def test_list_storage_boxes_endpoint(self):
        """Тест получения списка боксов"""
        response = self.client.get('/api/storage/boxes/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_storage_box_endpoint(self):
        """Тест создания бокса через API"""
        data = {
            'box_id': 'API_BOX003',
            'rows': 10,
            'cols': 10,
            'description': 'Новый тестовый бокс'
        }
        
        response = self.client.post('/api/storage/boxes/create/', json.dumps(data), content_type='application/json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(StorageBox.objects.filter(box_id='API_BOX003').exists())
        
        # Проверяем, что бокс создался с правильными данными
        created_box = StorageBox.objects.get(box_id='API_BOX003')
        self.assertEqual(created_box.rows, 10)
        self.assertEqual(created_box.cols, 10)
        self.assertEqual(created_box.description, 'Новый тестовый бокс')


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
