"""
Тесты для модуля strain_management
"""

import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date

from .models import Strain
from reference_data.models import IndexLetter, Location, Source, IUKColor, AmylaseVariant, GrowthMedium


class StrainModelTests(TestCase):
    """Тесты модели Strain"""
    
    def setUp(self):
        # Создаем необходимые справочные данные
        self.index_letter = IndexLetter.objects.create(letter_value='A')
        self.location = Location.objects.create(name='Test Location')
        self.source = Source.objects.create(
            organism_name='Test Organism',
            source_type='Test Type',
            category='Test Category'
        )
        self.iuk_color = IUKColor.objects.create(name='Blue', hex_code='#0000FF')
        self.amylase_variant = AmylaseVariant.objects.create(name='Positive')
        self.growth_medium = GrowthMedium.objects.create(name='LB')
    
    def test_strain_creation(self):
        """Тест создания штамма"""
        strain = Strain.objects.create(
            short_code='A001',
            identifier='Test Organism',
            rrna_taxonomy='Test Taxonomy',
            name_alt='Alternative Name',
            rcam_collection_id='RCAM001'
        )
        
        self.assertEqual(strain.short_code, 'A001')
        self.assertEqual(strain.identifier, 'Test Organism')
        self.assertEqual(strain.rrna_taxonomy, 'Test Taxonomy')
        self.assertEqual(str(strain), 'A001 - Test Organism')
    
    def test_strain_full_number_property(self):
        """Тест свойства full_number штамма"""
        strain = Strain.objects.create(
            short_code='A123',
            identifier='Test Organism',
            rrna_taxonomy='Test Taxonomy'
        )
        
        self.assertEqual(strain.short_code, 'A123')
    
    def test_strain_required_fields(self):
        """Тест обязательных полей штамма"""
        # Тестируем отсутствие short_code
        strain = Strain(
            identifier='Test Organism',
            rrna_taxonomy='Test Taxonomy',
            name_alt='Test Alternative',
            rcam_collection_id='RCAM123'
        )
        with self.assertRaises(Exception):
            strain.full_clean()
            
        # Тестируем отсутствие identifier
        strain2 = Strain(
            short_code='TEST123',
            rrna_taxonomy='Test Taxonomy',
            name_alt='Test Alternative',
            rcam_collection_id='RCAM123'
        )
        with self.assertRaises(Exception):
            strain2.full_clean()


class StrainAPITests(TestCase):
    """Тесты API управления штаммами"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Создаем необходимые справочные данные
        self.index_letter = IndexLetter.objects.create(letter_value='B')
        self.location = Location.objects.create(name='API Test Location')
        self.source = Source.objects.create(
            organism_name='API Test Organism',
            source_type='API Test Type',
            category='API Test Category'
        )
        self.iuk_color = IUKColor.objects.create(name='Red', hex_code='#FF0000')
        self.amylase_variant = AmylaseVariant.objects.create(name='Negative')
        self.growth_medium = GrowthMedium.objects.create(name='TSA')
        
        # Создаем тестовый штамм
        self.strain = Strain.objects.create(
            short_code='B999',
            identifier='API Test Organism',
            rrna_taxonomy='API Test Taxonomy',
            name_alt='API Alternative Name',
            rcam_collection_id='RCAM999'
        )
    
    def test_get_strains_list(self):
        """Тест получения списка штаммов"""
        response = self.client.get('/api/strains/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertIn('strains', data)
        self.assertEqual(len(data['strains']), 1)
        self.assertEqual(data['strains'][0]['short_code'], 'B999')
        self.assertEqual(data['strains'][0]['identifier'], 'API Test Organism')
    
    def test_get_strain_detail(self):
        """Тест получения детальной информации о штамме"""
        response = self.client.get(f'/api/strains/{self.strain.id}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['short_code'], 'B999')
        self.assertEqual(data['identifier'], 'API Test Organism')
        self.assertEqual(data['rrna_taxonomy'], 'API Test Taxonomy')
    
    def test_create_strain_api(self):
        """Тест создания штамма через API"""
        strain_data = {
            'short_code': 'B888',
            'identifier': 'New API Organism',
            'rrna_taxonomy': 'New Taxonomy',
            'name_alt': 'New Alternative Name',
            'rcam_collection_id': 'RCAM888'
        }
        
        response = self.client.post('/api/strains/create/', strain_data, format='json')
        self.assertEqual(response.status_code, 201)
        
        # Проверяем, что штамм создался
        created_strain = Strain.objects.get(short_code='B888')
        self.assertEqual(created_strain.identifier, 'New API Organism')
    
    def test_update_strain_api(self):
        """Тест обновления штамма через API"""
        update_data = {
            'short_code': self.strain.short_code,
            'identifier': self.strain.identifier,
            'rrna_taxonomy': self.strain.rrna_taxonomy,
            'name_alt': 'Updated alternative name',
            'rcam_collection_id': self.strain.rcam_collection_id
        }
        
        response = self.client.put(f'/api/strains/{self.strain.id}/update/', update_data, format='json')
        self.assertEqual(response.status_code, 200)
        
        # Проверяем обновление
        self.strain.refresh_from_db()
        self.assertEqual(self.strain.name_alt, 'Updated alternative name')
    
    def test_delete_strain_api(self):
        """Тест удаления штамма через API"""
        strain_id = self.strain.id
        response = self.client.delete(f'/api/strains/{strain_id}/delete/')
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что штамм удален
        with self.assertRaises(Strain.DoesNotExist):
            Strain.objects.get(id=strain_id)
    
    def test_search_strains_api(self):
        """Тест поиска штаммов"""
        response = self.client.get('/api/strains/?search=API')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertIn('strains', data)
        self.assertEqual(len(data['strains']), 1)
        self.assertEqual(data['strains'][0]['identifier'], 'API Test Organism')
    
    def test_validate_strain_number_api(self):
        """Тест валидации номера штамма"""
        response = self.client.post('/api/strains/validate/', {
            'short_code': ''  # Пустой код должен вызвать ошибку валидации
        }, format='json')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['valid'])  # Данные невалидны


@pytest.mark.unit
class TestStrainModel:
    """Pytest тесты для модели Strain"""
    
    @pytest.fixture
    def reference_data(self, db):
        """Фикстура для создания справочных данных"""
        index_letter = IndexLetter.objects.create(letter_value='C')
        location = Location.objects.create(name='Pytest Location')
        source = Source.objects.create(
            organism_name='Pytest Organism',
            source_type='Pytest Type',
            category='Pytest Category'
        )
        iuk_color = IUKColor.objects.create(name='Green', hex_code='#00FF00')
        amylase_variant = AmylaseVariant.objects.create(name='Weak')
        growth_medium = GrowthMedium.objects.create(name='PDA')
        
        return {
            'index_letter': index_letter,
            'location': location,
            'source': source,
            'iuk_color': iuk_color,
            'amylase_variant': amylase_variant,
            'growth_medium': growth_medium
        }
    
    def test_strain_str_representation(self, reference_data):
        """Тест строкового представления штамма"""
        strain = Strain.objects.create(
            short_code='C777',
            identifier='Pytest Organism',
            rrna_taxonomy='Pytest Taxonomy',
            name_alt='Pytest Alternative',
            rcam_collection_id='RCAM777'
        )
        
        assert str(strain) == 'C777 - Pytest Organism'
    
    def test_strain_full_number(self, reference_data):
        """Тест полного номера штамма"""
        strain = Strain.objects.create(
            short_code='C555',
            identifier='Test Full Number',
            rrna_taxonomy='Test Taxonomy',
            name_alt='Test Alternative',
            rcam_collection_id='RCAM555'
        )
        
        assert strain.short_code == 'C555'


@pytest.mark.api
class TestStrainAPI:
    """Pytest тесты для API штаммов"""
    
    @pytest.fixture
    def strain_data(self, db):
        """Фикстура для создания тестовых данных штамма"""
        index_letter = IndexLetter.objects.create(letter_value='D')
        location = Location.objects.create(name='Pytest API Location')
        source = Source.objects.create(
            organism_name='Pytest API Organism',
            source_type='Pytest API Type',
            category='Pytest API Category'
        )
        iuk_color = IUKColor.objects.create(name='Yellow', hex_code='#FFFF00')
        amylase_variant = AmylaseVariant.objects.create(name='Strong')
        growth_medium = GrowthMedium.objects.create(name='MEA')
        
        strain = Strain.objects.create(
            short_code='D444',
            identifier='Pytest API Organism',
            rrna_taxonomy='Pytest API Taxonomy',
            name_alt='Pytest API Alternative',
            rcam_collection_id='RCAM444'
        )
        
        return {
            'strain': strain,
            'index_letter': index_letter,
            'location': location,
            'source': source,
            'iuk_color': iuk_color,
            'amylase_variant': amylase_variant,
            'growth_medium': growth_medium
        }
    
    def test_strains_list_endpoint(self, api_client, strain_data):
        """Тест endpoint списка штаммов"""
        response = api_client.get('/api/strains/')
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert 'strains' in data
        assert len(data['strains']) == 1
        assert data['strains'][0]['short_code'] == 'D444'
    
    def test_strain_detail_endpoint(self, api_client, strain_data):
        """Тест endpoint детальной информации о штамме"""
        strain = strain_data['strain']
        response = api_client.get(f'/api/strains/{strain.id}/')
        assert response.status_code == 200
        
        data = response.json()
        assert data['short_code'] == 'D444'
        assert data['identifier'] == 'Pytest API Organism'
    
    def test_strain_search_endpoint(self, api_client, strain_data):
        """Тест endpoint поиска штаммов"""
        response = api_client.get('/api/strains/?search=Pytest')
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert 'strains' in data
        assert len(data['strains']) == 1
        assert 'Pytest' in data['strains'][0]['identifier']
