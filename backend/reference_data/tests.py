"""
Тесты для модуля reference_data
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from .models import (
    IndexLetter,
    Location,
    Source,
    SourceType,
    SourceCategory,
    IUKColor,
    AmylaseVariant,
    GrowthMedium,
)


class ReferenceDataModelTests(TestCase):
    """Тесты моделей справочных данных"""
    
    def test_index_letter_creation(self):
        """Тест создания индексной буквы"""
        letter = IndexLetter.objects.create(letter_value='A')
        self.assertEqual(letter.letter_value, 'A')
        self.assertEqual(str(letter), 'A')
    
    def test_location_creation(self):
        """Тест создания местоположения"""
        location = Location.objects.create(
            name='Test Location'
        )
        
        self.assertEqual(location.name, 'Test Location')
        self.assertEqual(str(location), 'Test Location')
    
    def test_source_creation(self):
        """Тест создания источника"""
        source_type = SourceType.objects.create(name='Test Type')
        category = SourceCategory.objects.create(name='Test Category')
        source = Source.objects.create(
            organism_name='Test Organism',
            source_type=source_type,
            category=category
        )
        
        self.assertEqual(source.organism_name, 'Test Organism')
        self.assertEqual(source.source_type, source_type)
        self.assertEqual(source.category, category)
        self.assertEqual(str(source), 'Test Organism (Test Type)')
    
    def test_iuk_color_creation(self):
        """Тест создания цвета IUK"""
        color = IUKColor.objects.create(
            name='Blue',
            hex_code='#0000FF'
        )
        
        self.assertEqual(color.name, 'Blue')
        self.assertEqual(color.hex_code, '#0000FF')
        self.assertEqual(str(color), 'Blue')
    
    def test_amylase_variant_creation(self):
        """Тест создания варианта амилазы"""
        variant = AmylaseVariant.objects.create(
            name='Positive',
            description='Positive variant'
        )
        self.assertEqual(variant.name, 'Positive')
        self.assertEqual(str(variant), 'Positive')
    
    def test_growth_medium_creation(self):
        """Тест создания среды роста"""
        medium = GrowthMedium.objects.create(
            name='LB',
            description='Luria-Bertani medium'
        )
        self.assertEqual(medium.name, 'LB')
        self.assertEqual(str(medium), 'LB')
    
    def test_index_letter_unique_constraint(self):
        """Тест уникальности индексной буквы"""
        IndexLetter.objects.create(letter_value='A')
        
        with self.assertRaises(Exception):
            IndexLetter.objects.create(letter_value='A')
    
    def test_location_unique_constraint(self):
        """Тест уникальности местоположения"""
        Location.objects.create(name='Unique Location')
        
        with self.assertRaises(Exception):
            Location.objects.create(name='Unique Location')
    
    def test_iuk_color_unique_constraint(self):
        """Тест уникальности цвета IUK"""
        IUKColor.objects.create(name='Unique Blue', hex_code='#0000FF')
        
        with self.assertRaises(Exception):
            IUKColor.objects.create(name='Unique Blue', hex_code='#FF0000')
    
    def test_amylase_variant_unique_constraint(self):
        """Тест уникальности варианта амилазы"""
        AmylaseVariant.objects.create(name='Unique Variant')
        
        with self.assertRaises(Exception):
            AmylaseVariant.objects.create(name='Unique Variant')
    
    def test_growth_medium_unique_constraint(self):
        """Тест уникальности среды роста"""
        GrowthMedium.objects.create(name='Unique Medium')
        
        with self.assertRaises(Exception):
            GrowthMedium.objects.create(name='Unique Medium')
    
    def test_model_required_fields(self):
        """Тест обязательных полей моделей"""
        # IndexLetter
        with self.assertRaises(Exception):
            letter = IndexLetter()
            letter.full_clean()
        
        # Location
        with self.assertRaises(Exception):
            location = Location()
            location.full_clean()
        
        # Source
        with self.assertRaises(Exception):
            source = Source()
            source.full_clean()
        
        # IUKColor
        with self.assertRaises(Exception):
            color = IUKColor()
            color.full_clean()
        
        # AmylaseVariant
        with self.assertRaises(Exception):
            variant = AmylaseVariant()
            variant.full_clean()
        
        # GrowthMedium
        with self.assertRaises(Exception):
            medium = GrowthMedium()
            medium.full_clean()


class ReferenceDataAPITests(TestCase):
    """Тесты API справочных данных"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Создаем тестовые данные
        self.index_letter = IndexLetter.objects.create(letter_value='T')
        self.location = Location.objects.create(name='Test Location')
        self.source_type = SourceType.objects.create(name='Test Type')
        self.source_category = SourceCategory.objects.create(name='Test Category')
        self.source = Source.objects.create(
            organism_name='Test Organism',
            source_type=self.source_type,
            category=self.source_category
        )
        self.iuk_color = IUKColor.objects.create(
            name='Test Blue',
            hex_code='#0000FF'
        )
        self.amylase_variant = AmylaseVariant.objects.create(
            name='Test Positive',
            description='Test positive variant'
        )
        self.growth_medium = GrowthMedium.objects.create(
            name='Test LB',
            description='Test Luria-Bertani medium'
        )
    
    def test_get_reference_data_api(self):
        """Тест API получения справочных данных"""
        response = self.client.get('/api/reference/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('index_letters', data)
        self.assertIn('locations', data)
        self.assertIn('sources', data)
        self.assertIn('source_types', data)
        self.assertIn('source_categories', data)
        self.assertIn('iuk_colors', data)
        self.assertIn('amylase_variants', data)
        self.assertIn('growth_media', data)
        
        # Проверяем наличие созданных данных
        self.assertEqual(len(data['index_letters']), 1)
        self.assertEqual(data['index_letters'][0]['letter_value'], 'T')
        
        self.assertEqual(len(data['locations']), 1)
        self.assertEqual(data['locations'][0]['name'], 'Test Location')
    
    def test_get_source_types_api(self):
        """Тест API получения типов источников"""
        response = self.client.get('/api/reference/source-types/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        names = {item['name'] for item in data}
        self.assertIn('Test Type', names)
    
    def test_get_organism_names_api(self):
        """Тест API получения названий организмов"""
        response = self.client.get('/api/reference/organism-names/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], 'Test Organism')
    
    def test_get_organism_names_api_empty(self):
        """Тест API получения названий организмов (пустой список)"""
        # Удаляем тестовые данные
        Source.objects.all().delete()
        
        response = self.client.get('/api/reference/organism-names/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data), 0)


@pytest.mark.unit
class TestReferenceDataModels:
    """Pytest тесты для моделей справочных данных"""
    
    def test_index_letter_str_representation(self, db):
        """Тест строкового представления IndexLetter"""
        letter = IndexLetter.objects.create(letter_value='Z')
        assert str(letter) == 'Z'
    
    def test_location_str_representation(self, db):
        """Тест строкового представления Location"""
        location = Location.objects.create(name='Pytest Location')
        assert str(location) == 'Pytest Location'
    
    def test_source_str_representation(self, db):
        """Тест строкового представления Source"""
        source_type = SourceType.objects.create(name='Pytest Type')
        category = SourceCategory.objects.create(name='Pytest Category')
        source = Source.objects.create(
            organism_name='Pytest Organism',
            source_type=source_type,
            category=category
        )
        assert str(source) == 'Pytest Organism (Pytest Type)'


@pytest.mark.api
class TestReferenceDataAPI:
    """Pytest тесты для API справочных данных"""
    
    def test_reference_data_endpoint_structure(self, api_client):
        """Тест структуры ответа API справочных данных"""
        response = api_client.get('/api/reference/')
        assert response.status_code == 200
        
        data = response.json()
        required_keys = [
            'index_letters', 'locations', 'sources',
            'source_types', 'source_categories',
            'iuk_colors', 'amylase_variants', 'growth_media'
        ]
        
        for key in required_keys:
            assert key in data, f"Missing key: {key}"
            assert isinstance(data[key], list), f"Key {key} should be a list"
    
    @pytest.fixture
    def reference_data(self, db):
        """Фикстура для создания тестовых справочных данных"""
        index_letter = IndexLetter.objects.create(letter_value='T')
        location = Location.objects.create(name='Pytest Test Location')
        source_type = SourceType.objects.create(name='Test Type')
        source_category = SourceCategory.objects.create(name='Test Category')
        source = Source.objects.create(
            organism_name='Pytest Test Organism',
            source_type=source_type,
            category=source_category
        )
        iuk_color = IUKColor.objects.create(name='Pytest Blue', hex_code='#0000FF')
        amylase_variant = AmylaseVariant.objects.create(name='Pytest Variant A', description='Test variant')
        growth_medium = GrowthMedium.objects.create(name='Pytest Medium', description='Test medium')
        
        return {
            'index_letter': index_letter,
            'location': location,
            'source_type': source_type,
            'source_category': source_category,
            'source': source,
            'iuk_color': iuk_color,
            'amylase_variant': amylase_variant,
            'growth_medium': growth_medium
        }

    def test_source_types_endpoint(self, api_client, db):
        """Тест endpoint получения типов источников"""
        type1 = SourceType.objects.create(name='Type1')
        type2 = SourceType.objects.create(name='Type2')
        category1 = SourceCategory.objects.create(name='Category1')
        category2 = SourceCategory.objects.create(name='Category2')
        Source.objects.create(
            organism_name='Source1 Organism',
            source_type=type1,
            category=category1
        )
        Source.objects.create(
            organism_name='Source2 Organism',
            source_type=type2,
            category=category2
        )

        response = api_client.get('/api/reference/source-types/')
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        names = {item['name'] for item in data}
        assert names == {'Type1', 'Type2'}
        ids = {item['id'] for item in data}
        assert ids == {type1.id, type2.id}
    
    def test_organism_names_endpoint(self, api_client, db):
        """Тест endpoint получения названий организмов"""
        type_a = SourceType.objects.create(name='Type A')
        type_b = SourceType.objects.create(name='Type B')
        category_a = SourceCategory.objects.create(name='Category A')
        category_b = SourceCategory.objects.create(name='Category B')
        Source.objects.create(
            organism_name='Organism A',
            source_type=type_a,
            category=category_a
        )
        Source.objects.create(
            organism_name='Organism B',
            source_type=type_b,
            category=category_b
        )

        response = api_client.get('/api/reference/organism-names/')
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert 'Organism A' in data
        assert 'Organism B' in data
    
    def test_organism_names_endpoint_empty(self, api_client, db):
        """Тест endpoint получения названий организмов (пустой список)"""
        response = api_client.get('/api/reference/organism-names/')
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 0
    
    def test_reference_data_endpoint_with_data(self, api_client, reference_data):
        """Тест endpoint получения всех справочных данных с тестовыми данными"""
        response = api_client.get('/api/reference/')
        assert response.status_code == 200
        
        data = response.json()
        
        # Проверяем наличие данных в каждой категории
        assert len(data['index_letters']) == 1
        assert data['index_letters'][0]['letter_value'] == 'T'
        
        assert len(data['locations']) == 1
        assert data['locations'][0]['name'] == 'Pytest Test Location'
        
        assert len(data['sources']) == 1
        assert data['sources'][0]['organism_name'] == 'Pytest Test Organism'
        assert data['sources'][0]['source_type'] == 'Test Type'
        assert data['sources'][0]['category'] == 'Test Category'

        assert len(data['source_types']) == 1
        assert data['source_types'][0]['name'] == 'Test Type'

        assert len(data['source_categories']) == 1
        assert data['source_categories'][0]['name'] == 'Test Category'

        assert len(data['iuk_colors']) == 1
        assert data['iuk_colors'][0]['name'] == 'Pytest Blue'
        assert data['iuk_colors'][0]['hex_code'] == '#0000FF'
        
        assert len(data['amylase_variants']) == 1
        assert data['amylase_variants'][0]['name'] == 'Pytest Variant A'
        
        assert len(data['growth_media']) == 1
        assert data['growth_media'][0]['name'] == 'Pytest Medium'
    
    def test_api_error_handling(self, api_client, db, monkeypatch):
        """Тест обработки ошибок в API"""
        # Мокаем ошибку в базе данных
        def mock_all():
            raise Exception("Database error")
        
        monkeypatch.setattr(IndexLetter.objects, 'all', mock_all)
        
        response = api_client.get('/api/reference/')
        assert response.status_code == 500
        
        data = response.json()
        assert 'error' in data
        assert 'Database error' in data['error']
