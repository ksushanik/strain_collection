"""
Тесты для новых функций системы учета штаммов
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Sample, Strain, Source, Location, GrowthMedium, Comment, AppendixNote
from .schemas import SampleSchema, GrowthMediumSchema


class SampleModelTests(TestCase):
    """Тесты модели Sample"""

    def setUp(self):
        """Создание тестовых данных"""
        self.strain = Strain.objects.create(
            short_code="TEST001",
            identifier="Test Strain 001",
            rrna_taxonomy="Test Taxonomy"
        )
        self.source = Source.objects.create(
            organism_name="Test Organism",
            source_type="Soil",
            category="Environmental"
        )
        self.location = Location.objects.create(name="Test Location")

    def test_sample_creation_with_new_fields(self):
        """Тест создания образца с новыми полями"""
        sample = Sample.objects.create(
            strain=self.strain,
            comment_text="Custom comment text",
            appendix_note_text="Custom note text",
            mobilizes_phosphates=True,
            stains_medium=True,
            produces_siderophores=True,
            produces_iuk=True,
            produces_amylase=True,
            iuk_color="Pink",
            amylase_variant="α-amylase"
        )

        self.assertEqual(sample.comment_text, "Custom comment text")
        self.assertEqual(sample.appendix_note_text, "Custom note text")
        self.assertTrue(sample.mobilizes_phosphates)
        self.assertTrue(sample.stains_medium)
        self.assertTrue(sample.produces_siderophores)
        self.assertTrue(sample.produces_iuk)
        self.assertTrue(sample.produces_amylase)
        self.assertEqual(sample.iuk_color, "Pink")
        self.assertEqual(sample.amylase_variant, "α-amylase")

    def test_growth_media_relationship(self):
        """Тест связи многие-ко-многим со средами роста"""
        medium1 = GrowthMedium.objects.create(name="LB Agar", description="Luria-Bertani agar")
        medium2 = GrowthMedium.objects.create(name="TSB", description="Tryptic Soy Broth")

        sample = Sample.objects.create(strain=self.strain)
        sample.growth_media_ids.add(medium1, medium2)

        self.assertEqual(sample.growth_media_ids.count(), 2)
        self.assertIn(medium1, sample.growth_media_ids.all())
        self.assertIn(medium2, sample.growth_media_ids.all())


class GrowthMediumModelTests(TestCase):
    """Тесты модели GrowthMedium"""

    def test_growth_medium_creation(self):
        """Тест создания среды роста"""
        medium = GrowthMedium.objects.create(
            name="Nutrient Agar",
            description="Standard nutrient agar for bacterial growth"
        )

        self.assertEqual(medium.name, "Nutrient Agar")
        self.assertEqual(medium.description, "Standard nutrient agar for bacterial growth")

    def test_growth_medium_unique_name(self):
        """Тест уникальности названия среды роста"""
        GrowthMedium.objects.create(name="Test Medium")

        with self.assertRaises(Exception):
            GrowthMedium.objects.create(name="Test Medium")


class APITests(APITestCase):
    """Тесты API endpoints"""

    def setUp(self):
        """Создание тестовых данных"""
        self.strain = Strain.objects.create(
            short_code="APITEST",
            identifier="API Test Strain"
        )
        self.source = Source.objects.create(
            organism_name="API Test Organism",
            source_type="Water",
            category="Aquatic"
        )
        self.location = Location.objects.create(name="API Test Location")

    def test_list_samples_sorting_by_date(self):
        """Тест сортировки образцов по дате создания"""
        # Создаем несколько образцов
        sample1 = Sample.objects.create(
            strain=self.strain,
            original_sample_number='001'
        )
        sample2 = Sample.objects.create(
            strain=self.strain,
            original_sample_number='002'
        )

        # Тест сортировки по created_at по возрастанию
        url = reverse('list_samples')
        response = self.client.get(url, {'sort_by': 'created_at', 'sort_order': 'asc'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('sorting', data)
        self.assertEqual(data['sorting']['sort_by'], 'created_at')
        self.assertEqual(data['sorting']['sort_order'], 'asc')

        # Тест сортировки по created_at по убыванию
        response = self.client.get(url, {'sort_by': 'created_at', 'sort_order': 'desc'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['sorting']['sort_by'], 'created_at')
        self.assertEqual(data['sorting']['sort_order'], 'desc')

        # Проверяем, что даты присутствуют в ответе
        self.assertTrue(len(data['samples']) > 0)
        for sample in data['samples']:
            self.assertIn('created_at', sample)
            self.assertIn('updated_at', sample)

        # Очистка
        sample2.delete()
        sample1.delete()

    def test_create_sample_with_new_fields(self):
        """Тест создания образца через API с новыми полями"""
        url = reverse('create_sample')
        data = {
            "strain_id": self.strain.id,
            "source_id": self.source.id,
            "location_id": self.location.id,
            "comment_text": "API test comment",
            "appendix_note_text": "API test note",
            "mobilizes_phosphates": True,
            "stains_medium": False,
            "produces_siderophores": True,
            "produces_iuk": True,
            "produces_amylase": False,
            "iuk_color": "Yellow",
            "amylase_variant": "",
            "growth_media_ids": []
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверка создания образца
        sample_id = response.data['id']
        sample = Sample.objects.get(id=sample_id)

        self.assertEqual(sample.comment_text, "API test comment")
        self.assertEqual(sample.appendix_note_text, "API test note")
        self.assertTrue(sample.mobilizes_phosphates)
        self.assertFalse(sample.stains_medium)
        self.assertTrue(sample.produces_siderophores)
        self.assertTrue(sample.produces_iuk)
        self.assertFalse(sample.produces_amylase)
        self.assertEqual(sample.iuk_color, "Yellow")

    def test_update_sample_with_new_fields(self):
        """Тест обновления образца через API с новыми полями"""
        # Создание образца
        sample = Sample.objects.create(
            strain=self.strain,
            comment_text="Original comment",
            mobilizes_phosphates=False
        )

        url = reverse('update_sample', args=[sample.id])
        data = {
            "comment_text": "Updated comment",
            "mobilizes_phosphates": True,
            "stains_medium": True
        }

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверка обновления
        sample.refresh_from_db()
        self.assertEqual(sample.comment_text, "Updated comment")
        self.assertTrue(sample.mobilizes_phosphates)
        self.assertTrue(sample.stains_medium)

    def test_growth_medium_api_endpoints(self):
        """Тест API endpoints для сред роста"""
        # Создание среды роста
        create_url = reverse('create_growth_medium')
        data = {
            "name": "API Test Medium",
            "description": "Test medium for API testing"
        }

        response = self.client.post(create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        medium_id = response.data['id']

        # Получение списка сред роста
        list_url = reverse('get_growth_media')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['growth_media']) > 0)

        # Обновление среды роста
        update_url = reverse('update_growth_medium', args=[medium_id])
        data = {
            "name": "Updated API Test Medium",
            "description": "Updated description"
        }

        response = self.client.put(update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Удаление среды роста
        delete_url = reverse('delete_growth_medium', args=[medium_id])
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SchemaValidationTests(TestCase):
    """Тесты валидации схем Pydantic"""

    def test_sample_schema_validation(self):
        """Тест валидации схемы SampleSchema"""
        valid_data = {
            "id": 1,
            "strain_id": 1,
            "comment_text": "Valid comment",
            "appendix_note_text": "Valid note",
            "mobilizes_phosphates": True,
            "stains_medium": False,
            "produces_siderophores": True,
            "produces_iuk": True,
            "produces_amylase": False,
            "iuk_color": "Pink",
            "amylase_variant": "α-amylase",
            "has_photo": False,
            "is_identified": True,
            "has_antibiotic_activity": False,
            "has_genome": True,
            "has_biochemistry": False,
            "seq_status": False,
            "created_at": "2025-01-01T10:00:00Z",
            "updated_at": "2025-01-01T10:00:00Z"
        }

        # Валидация должна пройти успешно
        schema = SampleSchema(**valid_data)
        self.assertEqual(schema.comment_text, "Valid comment")
        self.assertEqual(schema.iuk_color, "Pink")
        self.assertEqual(schema.created_at, "2025-01-01T10:00:00Z")
        self.assertEqual(schema.updated_at, "2025-01-01T10:00:00Z")

    def test_growth_medium_schema_validation(self):
        """Тест валидации схемы GrowthMediumSchema"""
        valid_data = {
            "id": 1,
            "name": "Test Medium",
            "description": "Test description"
        }

        # Валидация должна пройти успешно
        schema = GrowthMediumSchema(**valid_data)
        self.assertEqual(schema.name, "Test Medium")
        self.assertEqual(schema.description, "Test description")

    def test_schema_validation_errors(self):
        """Тест ошибок валидации схем"""
        invalid_data = {
            "id": 1,
            "name": "",  # Пустое имя - должно вызвать ошибку
            "description": "Test description"
        }

        # Валидация должна вызвать ошибку
        with self.assertRaises(Exception):
            GrowthMediumSchema(**invalid_data)
