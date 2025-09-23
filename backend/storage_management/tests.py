"""
Тесты для модуля storage_management
"""

import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date

from .models import Storage, Box
from sample_management.models import Sample
from strain_management.models import Strain
from reference_data.models import IndexLetter, Location, Source, IUKColor, AmylaseVariant, GrowthMedium


class StorageModelTests(TestCase):
    """Тесты модели Storage"""
    
    def test_storage_creation(self):
        """Тест создания хранилища"""
        storage = Storage.objects.create(
            name='Test Storage',
            description='Test storage description',
            temperature=-80,
            capacity=100
        )
        
        self.assertEqual(storage.name, 'Test Storage')
        self.assertEqual(storage.temperature, -80)
        self.assertEqual(storage.capacity, 100)
        self.assertEqual(str(storage), 'Test Storage')
    
    def test_storage_required_fields(self):
        """Тест обязательных полей хранилища"""
        with self.assertRaises(Exception):
            Storage.objects.create(
                # Пропускаем обязательное поле name
                description='Test description'
            )


class BoxModelTests(TestCase):
    """Тесты модели Box"""
    
    def setUp(self):
        self.storage = Storage.objects.create(
            name='Test Storage for Box',
            description='Storage for box testing',
            temperature=-20,
            capacity=50
        )
    
    def test_box_creation(self):
        """Тест создания коробки"""
        box = Box.objects.create(
            name='Test Box',
            storage=self.storage,
            position='A1',
            capacity=25,
            description='Test box description'
        )
        
        self.assertEqual(box.name, 'Test Box')
        self.assertEqual(box.storage, self.storage)
        self.assertEqual(box.position, 'A1')
        self.assertEqual(box.capacity, 25)
        self.assertEqual(str(box), 'Test Box (A1)')
    
    def test_box_storage_relationship(self):
        """Тест связи коробки с хранилищем"""
        box = Box.objects.create(
            name='Relationship Test Box',
            storage=self.storage,
            position='B2',
            capacity=30
        )
        
        self.assertEqual(box.storage.name, 'Test Storage for Box')
        self.assertEqual(box.storage.temperature, -20)


class StorageAPITests(TestCase):
    """Тесты API управления хранилищем"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Создаем тестовое хранилище
        self.storage = Storage.objects.create(
            name='API Test Storage',
            description='Storage for API testing',
            temperature=-80,
            capacity=200
        )
        
        # Создаем тестовую коробку
        self.box = Box.objects.create(
            name='API Test Box',
            storage=self.storage,
            position='C3',
            capacity=50,
            description='Box for API testing'
        )
    
    def test_get_storages_list(self):
        """Тест получения списка хранилищ"""
        response = self.client.get('/api/storage/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'API Test Storage')
    
    def test_get_storage_detail(self):
        """Тест получения детальной информации о хранилище"""
        response = self.client.get(f'/api/storage/{self.storage.id}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['name'], 'API Test Storage')
        self.assertEqual(data['temperature'], -80)
        self.assertEqual(data['capacity'], 200)
    
    def test_create_storage_api(self):
        """Тест создания хранилища через API"""
        storage_data = {
            'name': 'New API Storage',
            'description': 'New storage created via API',
            'temperature': -20,
            'capacity': 150
        }
        
        response = self.client.post('/api/storage/', storage_data, format='json')
        self.assertEqual(response.status_code, 201)
        
        # Проверяем, что хранилище создалось
        created_storage = Storage.objects.get(name='New API Storage')
        self.assertEqual(created_storage.temperature, -20)
    
    def test_get_boxes_list(self):
        """Тест получения списка коробок"""
        response = self.client.get('/api/storage/boxes/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'API Test Box')
    
    def test_get_box_detail(self):
        """Тест получения детальной информации о коробке"""
        response = self.client.get(f'/api/storage/boxes/{self.box.id}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['name'], 'API Test Box')
        self.assertEqual(data['position'], 'C3')
        self.assertEqual(data['capacity'], 50)
    
    def test_create_box_api(self):
        """Тест создания коробки через API"""
        box_data = {
            'name': 'New API Box',
            'storage': self.storage.id,
            'position': 'D4',
            'capacity': 40,
            'description': 'New box created via API'
        }
        
        response = self.client.post('/api/storage/boxes/', box_data, format='json')
        self.assertEqual(response.status_code, 201)
        
        # Проверяем, что коробка создалась
        created_box = Box.objects.get(name='New API Box')
        self.assertEqual(created_box.position, 'D4')
        self.assertEqual(created_box.storage, self.storage)
    
    def test_get_boxes_by_storage(self):
        """Тест получения коробок по хранилищу"""
        response = self.client.get(f'/api/storage/{self.storage.id}/boxes/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'API Test Box')
    
    def test_validate_storage_data(self):
        """Тест валидации данных хранилища"""
        response = self.client.post('/api/storage/validate/', {
            'name': 'API Test Storage',  # Уже существует
            'temperature': -80,
            'capacity': 100
        }, format='json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Проверяем, что валидация работает
        self.assertIn('is_valid', data)


@pytest.mark.unit
class TestStorageModels:
    """Pytest тесты для моделей хранилища"""
    
    def test_storage_str_representation(self, db):
        """Тест строкового представления хранилища"""
        storage = Storage.objects.create(
            name='Pytest Storage',
            description='Storage for pytest',
            temperature=-40,
            capacity=75
        )
        
        assert str(storage) == 'Pytest Storage'
    
    def test_box_str_representation(self, db):
        """Тест строкового представления коробки"""
        storage = Storage.objects.create(
            name='Pytest Storage for Box',
            description='Storage for box pytest',
            temperature=-60,
            capacity=100
        )
        
        box = Box.objects.create(
            name='Pytest Box',
            storage=storage,
            position='E5',
            capacity=20
        )
        
        assert str(box) == 'Pytest Box (E5)'
    
    def test_box_storage_relationship(self, db):
        """Тест связи коробки с хранилищем"""
        storage = Storage.objects.create(
            name='Relationship Storage',
            description='For relationship testing',
            temperature=-30,
            capacity=80
        )
        
        box = Box.objects.create(
            name='Relationship Box',
            storage=storage,
            position='F6',
            capacity=15
        )
        
        assert box.storage == storage
        assert box.storage.name == 'Relationship Storage'


@pytest.mark.api
class TestStorageAPI:
    """Pytest тесты для API хранилища"""
    
    @pytest.fixture
    def storage_data(self, db):
        """Фикстура для создания тестовых данных хранилища"""
        storage = Storage.objects.create(
            name='Pytest API Storage',
            description='Storage for pytest API testing',
            temperature=-70,
            capacity=120
        )
        
        box = Box.objects.create(
            name='Pytest API Box',
            storage=storage,
            position='G7',
            capacity=35,
            description='Box for pytest API testing'
        )
        
        return {
            'storage': storage,
            'box': box
        }
    
    def test_storages_list_endpoint(self, api_client, storage_data):
        """Тест endpoint списка хранилищ"""
        response = api_client.get('/api/storage/')
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['name'] == 'Pytest API Storage'
    
    def test_storage_detail_endpoint(self, api_client, storage_data):
        """Тест endpoint детальной информации о хранилище"""
        storage = storage_data['storage']
        response = api_client.get(f'/api/storage/{storage.id}/')
        assert response.status_code == 200
        
        data = response.json()
        assert data['name'] == 'Pytest API Storage'
        assert data['temperature'] == -70
        assert data['capacity'] == 120
    
    def test_boxes_list_endpoint(self, api_client, storage_data):
        """Тест endpoint списка коробок"""
        response = api_client.get('/api/storage/boxes/')
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['name'] == 'Pytest API Box'
    
    def test_box_detail_endpoint(self, api_client, storage_data):
        """Тест endpoint детальной информации о коробке"""
        box = storage_data['box']
        response = api_client.get(f'/api/storage/boxes/{box.id}/')
        assert response.status_code == 200
        
        data = response.json()
        assert data['name'] == 'Pytest API Box'
        assert data['position'] == 'G7'
        assert data['capacity'] == 35
    
    def test_boxes_by_storage_endpoint(self, api_client, storage_data):
        """Тест endpoint получения коробок по хранилищу"""
        storage = storage_data['storage']
        response = api_client.get(f'/api/storage/{storage.id}/boxes/')
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['name'] == 'Pytest API Box'
    
    def test_storage_validation_endpoint(self, api_client, storage_data):
        """Тест endpoint валидации хранилища"""
        response = api_client.post('/api/storage/validate/', {
            'name': 'New Storage Name',
            'temperature': -50,
            'capacity': 90
        }, format='json')
        
        assert response.status_code == 200
        data = response.json()
        assert 'is_valid' in data
