"""
Общие фикстуры для pytest
"""
import pytest
import os
import django
from django.test import Client
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strain_tracker_project.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.db import transaction
import factory
from faker import Faker

fake = Faker('ru_RU')


@pytest.fixture
def client():
    """Базовый Django test client"""
    return Client()


@pytest.fixture
def api_client():
    """DRF API client"""
    return APIClient()


@pytest.fixture
def user():
    """Создание тестового пользователя"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """API client с аутентифицированным пользователем"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def db_transaction():
    """Фикстура для тестов с транзакциями"""
    with transaction.atomic():
        yield


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Автоматически включает доступ к БД для всех тестов
    """
    pass


# Фабрики для создания тестовых данных
class IndexLetterFactory(factory.django.DjangoModelFactory):
    """Фабрика для создания IndexLetter"""
    class Meta:
        model = 'collection_manager.IndexLetter'
    
    letter_value = factory.Faker('random_element', elements=['A', 'B', 'C', 'D', 'E'])

class LocationFactory(factory.django.DjangoModelFactory):
    """Фабрика для создания Location"""
    class Meta:
        model = 'collection_manager.Location'
    
    name = factory.Faker('city')

class SourceFactory(factory.django.DjangoModelFactory):
    """Фабрика для создания Source"""
    class Meta:
        model = 'collection_manager.Source'
    
    organism_name = factory.Faker('word')
    source_type = factory.Faker('word')
    category = factory.Faker('word')

class StorageFactory(factory.django.DjangoModelFactory):
    """Фабрика для создания Storage"""
    class Meta:
        model = 'collection_manager.Storage'
    
    box_id = factory.Sequence(lambda n: f"BOX{n:03d}")
    cell_id = factory.Faker('random_element', elements=['A1', 'B2', 'C3', 'D4', 'E5'])

class StrainFactory(factory.django.DjangoModelFactory):
    """Фабрика для создания Strain"""
    class Meta:
        model = 'collection_manager.Strain'
    
    short_code = factory.Sequence(lambda n: f"STR{n:04d}")
    identifier = factory.Faker('word')
    rrna_taxonomy = factory.Faker('word')
    name_alt = factory.Faker('word')

class SampleFactory(factory.django.DjangoModelFactory):
    """Фабрика для создания Sample"""
    class Meta:
        model = 'collection_manager.Sample'
    
    index_letter = factory.SubFactory(IndexLetterFactory)
    strain = factory.SubFactory(StrainFactory)
    storage = factory.SubFactory(StorageFactory)
    source = factory.SubFactory(SourceFactory)
    location = factory.SubFactory(LocationFactory)
    original_sample_number = factory.Sequence(lambda n: f"SAMPLE{n:04d}")


# Фикстуры для тестов
@pytest.fixture
def index_letter():
    """Фикстура для создания IndexLetter"""
    return IndexLetterFactory()


@pytest.fixture
def location():
    """Фикстура для создания Location"""
    return LocationFactory()


@pytest.fixture
def source():
    """Фикстура для создания Source"""
    return SourceFactory()


@pytest.fixture
def storage():
    """Фикстура для создания Storage"""
    return StorageFactory()


@pytest.fixture
def strain():
    """Фикстура для создания Strain"""
    return StrainFactory()


@pytest.fixture
def sample():
    """Фикстура для создания Sample"""
    return SampleFactory()