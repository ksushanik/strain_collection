"""
Тесты для модуля sample_management
"""

import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.core.exceptions import ValidationError

from .models import Sample, SampleGrowthMedia, SamplePhoto
from strain_management.models import Strain
from reference_data.models import IndexLetter, Location, Source, IUKColor, AmylaseVariant, GrowthMedium
from storage_management.models import Storage


class SampleModelTests(TestCase):
    """Тесты модели Sample"""
    
    def setUp(self):
        # Создаем необходимые справочные данные
        self.index_letter = IndexLetter.objects.create(letter_value='S')
        self.location = Location.objects.create(name='Sample Location')
        self.source = Source.objects.create(organism_name='Test Organism', source_type='Laboratory', category='Research')
        self.iuk_color = IUKColor.objects.create(name='Purple')
        self.amylase_variant = AmylaseVariant.objects.create(name='Medium')
        self.growth_medium = GrowthMedium.objects.create(name='YPD')
        self.storage = Storage.objects.create(box_id='TEST_BOX', cell_id='A1')
        
        # Создаем штамм для образца
        self.strain = Strain.objects.create(
            short_code='TST001',
            identifier='TEST-001',
            rrna_taxonomy='Test Taxonomy',
            name_alt='Test Alternative Name',
            rcam_collection_id='RCAM001'
        )
    
    def test_sample_creation(self):
        """Тест создания образца"""
        sample = Sample.objects.create(
            original_sample_number='001',
            strain=self.strain,
            storage=self.storage,
            appendix_note='Test sample notes'
        )
        
        self.assertEqual(sample.original_sample_number, '001')
        self.assertEqual(sample.strain, self.strain)
        self.assertTrue('TST001' in str(sample))
    
    def test_sample_without_strain(self):
        """Тест создания образца без штамма"""
        sample = Sample.objects.create(
            original_sample_number='002',
            storage=self.storage,
            appendix_note='Sample without strain'
        )
        
        self.assertEqual(sample.original_sample_number, '002')
        self.assertIsNone(sample.strain)
        self.assertTrue('Без штамма' in str(sample))
    
    def test_sample_is_empty_cell_property(self):
        """Тест свойства is_empty_cell"""
        # Пустая ячейка
        empty_sample = Sample.objects.create(storage=self.storage)
        self.assertTrue(empty_sample.is_empty_cell)
        
        # Не пустая ячейка с штаммом
        sample_with_strain = Sample.objects.create(
            strain=self.strain,
            storage=self.storage
        )
        self.assertFalse(sample_with_strain.is_empty_cell)
        
        # Не пустая ячейка с номером образца
        sample_with_number = Sample.objects.create(
            original_sample_number='003',
            storage=self.storage
        )
        self.assertFalse(sample_with_number.is_empty_cell)
    
    def test_sample_boolean_fields(self):
        """Тест булевых полей образца"""
        sample = Sample.objects.create(
            original_sample_number='004',
            strain=self.strain,
            storage=self.storage,
            has_photo=True,
            is_identified=True,
            has_antibiotic_activity=True,
            has_genome=True,
            has_biochemistry=True,
            seq_status=True,
            mobilizes_phosphates=True,
            stains_medium=True,
            produces_siderophores=True
        )
        
        self.assertTrue(sample.has_photo)
        self.assertTrue(sample.is_identified)
        self.assertTrue(sample.has_antibiotic_activity)
        self.assertTrue(sample.has_genome)
        self.assertTrue(sample.has_biochemistry)
        self.assertTrue(sample.seq_status)
        self.assertTrue(sample.mobilizes_phosphates)
        self.assertTrue(sample.stains_medium)
        self.assertTrue(sample.produces_siderophores)


class SampleGrowthMediaTests(TestCase):
    """Тесты модели SampleGrowthMedia"""
    
    def setUp(self):
        self.storage = Storage.objects.create(box_id='TEST_BOX2', cell_id='B2')
        self.growth_medium = GrowthMedium.objects.create(name='Test Medium')
        self.sample = Sample.objects.create(
            original_sample_number='GM001',
            storage=self.storage
        )
    
    def test_sample_growth_media_creation(self):
        """Тест создания связи образца со средой роста"""
        sgm = SampleGrowthMedia.objects.create(
            sample=self.sample,
            growth_medium=self.growth_medium
        )
        
        self.assertEqual(sgm.sample, self.sample)
        self.assertEqual(sgm.growth_medium, self.growth_medium)
        self.assertTrue('GM001' in str(sgm))
        self.assertTrue('Test Medium' in str(sgm))
    
    def test_sample_growth_media_unique_constraint(self):
        """Тест уникальности связи образца со средой роста"""
        SampleGrowthMedia.objects.create(
            sample=self.sample,
            growth_medium=self.growth_medium
        )
        
        # Попытка создать дублирующую связь
        with self.assertRaises(Exception):
            SampleGrowthMedia.objects.create(
                sample=self.sample,
                growth_medium=self.growth_medium
            )


class SampleAPITests(TestCase):
    """Тесты API для образцов"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Создаем необходимые справочные данные
        self.index_letter = IndexLetter.objects.create(letter_value='S')
        self.location = Location.objects.create(name='API Test Location')
        self.source = Source.objects.create(organism_name='API Test Organism', source_type='Laboratory', category='Testing')
        self.iuk_color = IUKColor.objects.create(name='Blue')
        self.amylase_variant = AmylaseVariant.objects.create(name='Strong')
        self.growth_medium = GrowthMedium.objects.create(name='LB')
        self.storage = Storage.objects.create(box_id='API_BOX', cell_id='C3')
        
        # Создаем штамм
        self.strain = Strain.objects.create(
            short_code='API001',
            identifier='API-001',
            rrna_taxonomy='API Test Taxonomy',
            name_alt='API Test Alternative Name',
            rcam_collection_id='RCAM-API001'
        )
        
        # Создаем образец для тестов
        self.sample = Sample.objects.create(
            original_sample_number='API001',
            strain=self.strain,
            storage=self.storage,
            appendix_note='API test sample',
            is_identified=True
        )
    
    def test_list_samples(self):
        """Тест получения списка образцов"""
        response = self.client.get('/api/samples/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        
        # Проверяем структуру ответа
        sample_data = response.data['results'][0]
        self.assertIn('id', sample_data)
        self.assertIn('original_sample_number', sample_data)
        self.assertIn('strain', sample_data)
        self.assertIn('storage', sample_data)
    
    def test_list_samples_with_search(self):
        """Тест поиска образцов"""
        response = self.client.get('/api/samples/?search=API')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_list_samples_with_filters(self):
        """Тест фильтрации образцов"""
        # Фильтр по штамму
        response = self.client.get(f'/api/samples/?strain_id={self.strain.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Фильтр по хранилищу
        response = self.client.get(f'/api/samples/?storage_id={self.storage.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Фильтр по идентификации
        response = self.client.get('/api/samples/?is_identified=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_sample(self):
        """Тест получения конкретного образца"""
        response = self.client.get(f'/api/samples/{self.sample.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['original_sample_number'], 'API001')
        self.assertIn('strain', response.data)
        self.assertIn('storage', response.data)
        self.assertIn('growth_media', response.data)
    
    def test_get_nonexistent_sample(self):
        """Тест получения несуществующего образца"""
        response = self.client.get('/api/samples/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_sample_with_strain(self):
        """Тест создания образца со штаммом"""
        data = {
            'original_sample_number': 'NEW001',
            'strain_id': self.strain.id,
            'storage_id': self.storage.id,
            'appendix_note': 'New test sample',
            'is_identified': True,
            'growth_media_ids': [self.growth_medium.id]
        }
        response = self.client.post('/api/samples/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['original_sample_number'], 'NEW001')
        self.assertEqual(response.data['strain']['id'], self.strain.id)
        self.assertEqual(len(response.data['growth_media']), 1)
    
    def test_create_sample_without_strain(self):
        """Тест создания образца без штамма"""
        data = {
            'original_sample_number': 'NOSTRAIN001',
            'storage_id': self.storage.id,
            'appendix_note': 'Sample without strain'
        }
        response = self.client.post('/api/samples/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['original_sample_number'], 'NOSTRAIN001')
        self.assertIsNone(response.data['strain'])
    
    def test_create_sample_invalid_data(self):
        """Тест создания образца с невалидными данными"""
        data = {
            'strain_id': 99999,  # Несуществующий штамм
            'storage_id': self.storage.id
        }
        response = self.client.post('/api/samples/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_sample(self):
        """Тест обновления образца"""
        data = {
            'original_sample_number': 'UPDATED001',
            'strain_id': self.strain.id,
            'storage_id': self.storage.id,
            'appendix_note': 'Updated test sample',
            'is_identified': False,
            'has_photo': True
        }
        response = self.client.put(f'/api/samples/{self.sample.id}/update/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['original_sample_number'], 'UPDATED001')
        self.assertFalse(response.data['is_identified'])
        self.assertTrue(response.data['has_photo'])
    
    def test_update_nonexistent_sample(self):
        """Тест обновления несуществующего образца"""
        data = {
            'original_sample_number': 'NOTFOUND001',
            'storage_id': self.storage.id
        }
        response = self.client.put('/api/samples/99999/update/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_delete_sample(self):
        """Тест удаления образца"""
        sample_id = self.sample.id
        response = self.client.delete(f'/api/samples/{sample_id}/delete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Проверяем, что образец действительно удален
        with self.assertRaises(Sample.DoesNotExist):
            Sample.objects.get(id=sample_id)
    
    def test_delete_nonexistent_sample(self):
        """Тест удаления несуществующего образца"""
        response = self.client.delete('/api/samples/99999/delete/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_validate_sample_valid_data(self):
        """Тест валидации корректных данных образца"""
        data = {
            'original_sample_number': 'VALID001',
            'storage_id': self.storage.id,
            'strain_id': self.strain.id
        }
        response = self.client.post('/api/samples/validate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        self.assertEqual(response.data['errors'], {})
    
    def test_validate_sample_invalid_data(self):
        """Тест валидации некорректных данных образца"""
        data = {
            'strain_id': 'invalid_string',  # Неверный тип данных
            'storage_id': -1,  # Отрицательное значение
            'original_sample_number': ''  # Пустая строка после валидации
        }
        response = self.client.post('/api/samples/validate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['valid'])
        self.assertIn('errors', response.data)


# Pytest тесты

@pytest.fixture
def api_client():
    """Фикстура для API клиента"""
    return APIClient()


@pytest.fixture
def sample_test_data():
    """Фикстура с тестовыми данными для образцов"""
    # Создаем справочные данные
    index_letter = IndexLetter.objects.create(letter_value='P')
    location = Location.objects.create(name='Pytest Location')
    source = Source.objects.create(organism_name='Pytest Organism', source_type='Laboratory', category='Testing')
    iuk_color = IUKColor.objects.create(name='Green')
    amylase_variant = AmylaseVariant.objects.create(name='Low')
    growth_medium = GrowthMedium.objects.create(name='TSA')
    storage = Storage.objects.create(box_id='PYTEST_BOX', cell_id='D4')
    
    # Создаем штамм
    strain = Strain.objects.create(
        short_code='PYT001',
        identifier='PYT-001',
        rrna_taxonomy='Pytest Taxonomy',
        name_alt='Pytest Alternative Name',
        rcam_collection_id='RCAM-PYT001'
    )
    
    # Создаем образец
    sample = Sample.objects.create(
        original_sample_number='PYT001',
        strain=strain,
        storage=storage,
        appendix_note='Pytest test sample',
        is_identified=True,
        has_photo=False
    )
    
    return {
        'sample': sample,
        'strain': strain,
        'storage': storage,
        'index_letter': index_letter,
        'location': location,
        'source': source,
        'iuk_color': iuk_color,
        'amylase_variant': amylase_variant,
        'growth_medium': growth_medium
    }


@pytest.mark.unit
class TestSampleModel:
    """Pytest тесты для модели Sample"""
    
    @pytest.mark.django_db
    def test_sample_str_representation_with_strain(self, sample_test_data):
        """Тест строкового представления образца со штаммом"""
        sample = sample_test_data['sample']
        assert 'PYT001' in str(sample)
        assert sample.strain.organism_name in str(sample)
    
    @pytest.mark.django_db
    def test_sample_str_representation_without_strain(self, sample_test_data):
        """Тест строкового представления образца без штамма"""
        storage = sample_test_data['storage']
        sample = Sample.objects.create(
            original_sample_number='NOSTRAIN001',
            storage=storage
        )
        assert 'Без штамма' in str(sample)
    
    @pytest.mark.django_db
    def test_sample_strain_relationship(self, sample_test_data):
        """Тест связи образца со штаммом"""
        sample = sample_test_data['sample']
        strain = sample_test_data['strain']
        
        assert sample.strain == strain
        assert sample.strain.short_code == 'PYT001'
        assert sample.strain.organism_name == 'Pytest Test Organism'
    
    @pytest.mark.django_db
    def test_sample_is_empty_cell_property(self, sample_test_data):
        """Тест свойства is_empty_cell"""
        storage = sample_test_data['storage']
        
        # Пустая ячейка
        empty_sample = Sample.objects.create(storage=storage)
        assert empty_sample.is_empty_cell is True
        
        # Не пустая ячейка
        non_empty_sample = Sample.objects.create(
            original_sample_number='NONEMPTY001',
            storage=storage
        )
        assert non_empty_sample.is_empty_cell is False
    
    @pytest.mark.django_db
    def test_sample_growth_media_relationship(self, sample_test_data):
        """Тест связи образца со средами роста"""
        sample = sample_test_data['sample']
        growth_medium = sample_test_data['growth_medium']
        
        # Создаем связь
        SampleGrowthMedia.objects.create(
            sample=sample,
            growth_medium=growth_medium
        )
        
        # Проверяем связь
        sample_growth_media = SampleGrowthMedia.objects.filter(sample=sample)
        assert sample_growth_media.count() == 1
        assert sample_growth_media.first().growth_medium == growth_medium


@pytest.mark.api
class TestSampleAPI:
    """Pytest тесты для API образцов"""
    
    @pytest.mark.django_db
    def test_list_samples_api(self, api_client, sample_test_data):
        """Тест получения списка образцов через API"""
        response = api_client.get('/api/samples/')
        
        assert response.status_code == 200
        data = response.json()
        assert 'results' in data
        assert len(data['results']) >= 1
        
        # Проверяем структуру ответа
        sample_data = data['results'][0]
        assert 'id' in sample_data
        assert 'original_sample_number' in sample_data
        assert 'strain' in sample_data
        assert 'storage' in sample_data
    
    @pytest.mark.django_db
    def test_get_sample_detail_api(self, api_client, sample_test_data):
        """Тест получения детальной информации об образце через API"""
        sample = sample_test_data['sample']
        response = api_client.get(f'/api/samples/{sample.id}/')
        
        assert response.status_code == 200
        data = response.json()
        assert data['original_sample_number'] == 'PYT001'
        assert data['strain']['id'] == sample.strain.id
        assert data['storage']['id'] == sample.storage.id
    
    @pytest.mark.django_db
    def test_search_samples_api(self, api_client, sample_test_data):
        """Тест поиска образцов через API"""
        response = api_client.get('/api/samples/?search=PYT')
        
        assert response.status_code == 200
        data = response.json()
        assert 'results' in data
        # Должен найти наш тестовый образец
        found_sample = any(
            'PYT' in result.get('original_sample_number', '') 
            for result in data['results']
        )
        assert found_sample
    
    @pytest.mark.django_db
    def test_filter_samples_by_strain_api(self, api_client, sample_test_data):
        """Тест фильтрации образцов по штамму через API"""
        strain = sample_test_data['strain']
        response = api_client.get(f'/api/samples/?strain_id={strain.id}')
        
        assert response.status_code == 200
        data = response.json()
        assert 'results' in data
        assert len(data['results']) >= 1
        assert data['results'][0]['strain']['id'] == strain.id
    
    @pytest.mark.django_db
    def test_filter_samples_by_storage_api(self, api_client, sample_test_data):
        """Тест фильтрации образцов по хранилищу через API"""
        storage = sample_test_data['storage']
        response = api_client.get(f'/api/samples/?storage_id={storage.id}')
        
        assert response.status_code == 200
        data = response.json()
        assert 'results' in data
        assert len(data['results']) >= 1
        assert data['results'][0]['storage']['id'] == storage.id
    
    @pytest.mark.django_db
    def test_create_sample_api(self, api_client, sample_test_data):
        """Тест создания образца через API"""
        strain = sample_test_data['strain']
        storage = sample_test_data['storage']
        growth_medium = sample_test_data['growth_medium']
        
        data = {
            'original_sample_number': 'NEWPYT001',
            'strain_id': strain.id,
            'storage_id': storage.id,
            'appendix_note': 'New pytest sample',
            'is_identified': True,
            'growth_media_ids': [growth_medium.id]
        }
        
        response = api_client.post('/api/samples/', data, format='json')
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data['original_sample_number'] == 'NEWPYT001'
        assert response_data['strain']['id'] == strain.id
        assert len(response_data['growth_media']) == 1
    
    @pytest.mark.django_db
    def test_update_sample_api(self, api_client, sample_test_data):
        """Тест обновления образца через API"""
        sample = sample_test_data['sample']
        storage = sample_test_data['storage']
        
        data = {
            'original_sample_number': 'UPDATEDPYT001',
            'storage_id': storage.id,
            'appendix_note': 'Updated pytest sample',
            'is_identified': False
        }
        
        response = api_client.put(f'/api/samples/{sample.id}/', data, format='json')
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['original_sample_number'] == 'UPDATEDPYT001'
        assert response_data['is_identified'] is False
    
    @pytest.mark.django_db
    def test_delete_sample_api(self, api_client, sample_test_data):
        """Тест удаления образца через API"""
        sample = sample_test_data['sample']
        sample_id = sample.id
        
        response = api_client.delete(f'/api/samples/{sample_id}/')
        
        assert response.status_code == 200
        assert 'message' in response.json()
        
        # Проверяем, что образец удален
        assert not Sample.objects.filter(id=sample_id).exists()
    
    @pytest.mark.django_db
    def test_validate_sample_api(self, api_client, sample_test_data):
        """Тест валидации данных образца через API"""
        storage = sample_test_data['storage']
        
        # Валидные данные
        valid_data = {
            'original_sample_number': 'VALIDPYT001',
            'storage_id': storage.id
        }
        
        response = api_client.post('/api/samples/validate/', valid_data, format='json')
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['valid'] is True
        assert response_data['errors'] == {}
    
    @pytest.mark.django_db
    def test_validate_sample_invalid_data_api(self, api_client):
        """Тест валидации невалидных данных образца через API"""
        invalid_data = {
            'strain_id': 99999,  # Несуществующий штамм
            'storage_id': 99999  # Несуществующее хранилище
        }
        
        response = api_client.post('/api/samples/validate/', invalid_data, format='json')
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['valid'] is False
        assert 'errors' in response_data
    
    @pytest.mark.django_db
    def test_api_error_handling(self, api_client):
        """Тест обработки ошибок в API"""
        # Попытка получить несуществующий образец
        response = api_client.get('/api/samples/99999/')
        assert response.status_code == 404
        
        # Попытка удалить несуществующий образец
        response = api_client.delete('/api/samples/99999/')
        assert response.status_code == 404
        
        # Попытка обновить несуществующий образец
        response = api_client.put('/api/samples/99999/', {}, format='json')
        assert response.status_code == 404
