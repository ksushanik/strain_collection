"""
Тесты для модуля audit_logging
"""

import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime, date
from django.contrib.auth.models import User

from .models import ChangeLog
from strain_management.models import Strain
from reference_data.models import IndexLetter, Location, Source, IUKColor, AmylaseVariant, GrowthMedium


class ChangeLogModelTests(TestCase):
    """Тесты модели ChangeLog"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_change_log_creation(self):
        """Тест создания записи в журнале изменений"""
        change_log = ChangeLog.objects.create(
            table_name='strain_management_strain',
            record_id=1,
            action='CREATE',
            user=self.user,
            changes={'name': 'Test Strain'},
            timestamp=datetime.now()
        )
        
        self.assertEqual(change_log.table_name, 'strain_management_strain')
        self.assertEqual(change_log.record_id, 1)
        self.assertEqual(change_log.action, 'CREATE')
        self.assertEqual(change_log.user, self.user)
        self.assertEqual(change_log.changes['name'], 'Test Strain')
    
    def test_change_log_str_representation(self):
        """Тест строкового представления записи журнала"""
        change_log = ChangeLog.objects.create(
            table_name='test_table',
            record_id=123,
            action='UPDATE',
            user=self.user,
            changes={'field': 'value'},
            timestamp=datetime.now()
        )
        
        expected_str = f"test_table:123 - UPDATE by {self.user.username}"
        self.assertEqual(str(change_log), expected_str)
    
    def test_change_log_required_fields(self):
        """Тест обязательных полей записи журнала"""
        with self.assertRaises(Exception):
            ChangeLog.objects.create(
                # Пропускаем обязательные поля
                table_name='test_table'
            )


class AuditLoggingAPITests(TestCase):
    """Тесты API аудита и логирования"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='apipass123'
        )
        
        # Создаем тестовые записи журнала
        self.change_log1 = ChangeLog.objects.create(
            table_name='strain_management_strain',
            record_id=1,
            action='CREATE',
            user=self.user,
            changes={'name': 'API Test Strain 1'},
            timestamp=datetime.now()
        )
        
        self.change_log2 = ChangeLog.objects.create(
            table_name='sample_management_sample',
            record_id=2,
            action='UPDATE',
            user=self.user,
            changes={'status': 'active'},
            timestamp=datetime.now()
        )
    
    def test_get_change_logs_list(self):
        """Тест получения списка записей журнала изменений"""
        response = self.client.get('/api/audit/change-logs/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
    
    def test_get_change_log_detail(self):
        """Тест получения детальной информации о записи журнала"""
        response = self.client.get(f'/api/audit/change-logs/{self.change_log1.id}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['table_name'], 'strain_management_strain')
        self.assertEqual(data['action'], 'CREATE')
        self.assertEqual(data['record_id'], 1)
    
    def test_get_object_history(self):
        """Тест получения истории объекта"""
        response = self.client.get('/api/audit/object-history/', {
            'table_name': 'strain_management_strain',
            'record_id': 1
        })
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['action'], 'CREATE')
    
    def test_get_user_activity(self):
        """Тест получения активности пользователя"""
        response = self.client.get(f'/api/audit/user-activity/{self.user.id}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)  # Два действия пользователя
    
    def test_batch_log_operations(self):
        """Тест пакетного логирования операций"""
        batch_data = {
            'operations': [
                {
                    'table_name': 'test_table1',
                    'record_id': 10,
                    'action': 'CREATE',
                    'user_id': self.user.id,
                    'changes': {'field1': 'value1'}
                },
                {
                    'table_name': 'test_table2',
                    'record_id': 20,
                    'action': 'UPDATE',
                    'user_id': self.user.id,
                    'changes': {'field2': 'value2'}
                }
            ]
        }
        
        response = self.client.post('/api/audit/batch-log/', batch_data, format='json')
        self.assertEqual(response.status_code, 201)
        
        # Проверяем, что записи созданы
        new_logs = ChangeLog.objects.filter(table_name__in=['test_table1', 'test_table2'])
        self.assertEqual(new_logs.count(), 2)
    
    def test_get_audit_statistics(self):
        """Тест получения статистики аудита"""
        response = self.client.get('/api/audit/statistics/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('total_changes', data)
        self.assertIn('changes_by_action', data)
        self.assertIn('changes_by_table', data)
        self.assertIn('recent_activity', data)
    
    def test_validate_log_data(self):
        """Тест валидации данных журнала"""
        log_data = {
            'table_name': 'test_validation_table',
            'record_id': 999,
            'action': 'DELETE',
            'user_id': self.user.id,
            'changes': {'deleted': True}
        }
        
        response = self.client.post('/api/audit/validate/', log_data, format='json')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('is_valid', data)


@pytest.mark.unit
class TestChangeLogModel:
    """Pytest тесты для модели ChangeLog"""
    
    @pytest.fixture
    def test_user(self, db):
        """Фикстура для создания тестового пользователя"""
        return User.objects.create_user(
            username='pytestuser',
            email='pytest@example.com',
            password='pytestpass123'
        )
    
    def test_change_log_str_representation(self, test_user):
        """Тест строкового представления записи журнала"""
        change_log = ChangeLog.objects.create(
            table_name='pytest_table',
            record_id=456,
            action='CREATE',
            user=test_user,
            changes={'pytest_field': 'pytest_value'},
            timestamp=datetime.now()
        )
        
        expected_str = f"pytest_table:456 - CREATE by {test_user.username}"
        assert str(change_log) == expected_str
    
    def test_change_log_fields(self, test_user):
        """Тест полей записи журнала"""
        changes_data = {'name': 'Test Name', 'status': 'active'}
        
        change_log = ChangeLog.objects.create(
            table_name='pytest_test_table',
            record_id=789,
            action='UPDATE',
            user=test_user,
            changes=changes_data,
            timestamp=datetime.now()
        )
        
        assert change_log.table_name == 'pytest_test_table'
        assert change_log.record_id == 789
        assert change_log.action == 'UPDATE'
        assert change_log.user == test_user
        assert change_log.changes == changes_data
    
    def test_change_log_user_relationship(self, test_user):
        """Тест связи записи журнала с пользователем"""
        change_log = ChangeLog.objects.create(
            table_name='relationship_table',
            record_id=111,
            action='DELETE',
            user=test_user,
            changes={'deleted': True},
            timestamp=datetime.now()
        )
        
        assert change_log.user == test_user
        assert change_log.user.username == 'pytestuser'


@pytest.mark.api
class TestAuditLoggingAPI:
    """Pytest тесты для API аудита"""
    
    @pytest.fixture
    def audit_data(self, db):
        """Фикстура для создания тестовых данных аудита"""
        user = User.objects.create_user(
            username='pytest_api_user',
            email='pytest_api@example.com',
            password='pytest_api_pass123'
        )
        
        change_log1 = ChangeLog.objects.create(
            table_name='pytest_strain_table',
            record_id=100,
            action='CREATE',
            user=user,
            changes={'name': 'Pytest Strain'},
            timestamp=datetime.now()
        )
        
        change_log2 = ChangeLog.objects.create(
            table_name='pytest_sample_table',
            record_id=200,
            action='UPDATE',
            user=user,
            changes={'status': 'updated'},
            timestamp=datetime.now()
        )
        
        return {
            'user': user,
            'change_log1': change_log1,
            'change_log2': change_log2
        }
    
    def test_change_logs_list_endpoint(self, api_client, audit_data):
        """Тест endpoint списка записей журнала"""
        response = api_client.get('/api/audit/change-logs/')
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
    
    def test_change_log_detail_endpoint(self, api_client, audit_data):
        """Тест endpoint детальной информации о записи журнала"""
        change_log = audit_data['change_log1']
        response = api_client.get(f'/api/audit/change-logs/{change_log.id}/')
        assert response.status_code == 200
        
        data = response.json()
        assert data['table_name'] == 'pytest_strain_table'
        assert data['action'] == 'CREATE'
        assert data['record_id'] == 100
    
    def test_object_history_endpoint(self, api_client, audit_data):
        """Тест endpoint истории объекта"""
        response = api_client.get('/api/audit/object-history/', {
            'table_name': 'pytest_strain_table',
            'record_id': 100
        })
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['action'] == 'CREATE'
    
    def test_user_activity_endpoint(self, api_client, audit_data):
        """Тест endpoint активности пользователя"""
        user = audit_data['user']
        response = api_client.get(f'/api/audit/user-activity/{user.id}/')
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
    
    def test_audit_statistics_endpoint(self, api_client, audit_data):
        """Тест endpoint статистики аудита"""
        response = api_client.get('/api/audit/statistics/')
        assert response.status_code == 200
        
        data = response.json()
        assert 'total_changes' in data
        assert 'changes_by_action' in data
        assert 'changes_by_table' in data
        assert 'recent_activity' in data
    
    def test_batch_log_endpoint(self, api_client, audit_data):
        """Тест endpoint пакетного логирования"""
        user = audit_data['user']
        batch_data = {
            'operations': [
                {
                    'table_name': 'pytest_batch_table1',
                    'record_id': 301,
                    'action': 'CREATE',
                    'user_id': user.id,
                    'changes': {'batch_field1': 'batch_value1'}
                },
                {
                    'table_name': 'pytest_batch_table2',
                    'record_id': 302,
                    'action': 'UPDATE',
                    'user_id': user.id,
                    'changes': {'batch_field2': 'batch_value2'}
                }
            ]
        }
        
        response = api_client.post('/api/audit/batch-log/', batch_data, format='json')
        assert response.status_code == 201
        
        # Проверяем, что записи созданы
        new_logs = ChangeLog.objects.filter(
            table_name__in=['pytest_batch_table1', 'pytest_batch_table2']
        )
        assert new_logs.count() == 2
    
    def test_log_validation_endpoint(self, api_client, audit_data):
        """Тест endpoint валидации журнала"""
        user = audit_data['user']
        log_data = {
            'table_name': 'pytest_validation_table',
            'record_id': 999,
            'action': 'DELETE',
            'user_id': user.id,
            'changes': {'validated': True}
        }
        
        response = api_client.post('/api/audit/validate/', log_data, format='json')
        assert response.status_code == 200
        
        data = response.json()
        assert 'is_valid' in data
