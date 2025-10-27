"""
РўРµСЃС‚С‹ РґР»СЏ РјРѕРґСѓР»СЏ storage_management
"""

import json
import threading
from unittest.mock import patch
from django.db import connections
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Storage, StorageBox
from sample_management.models import Sample
from sample_management.models import SampleStorageAllocation
from strain_management.models import Strain
from storage_management import services as storage_services
from storage_management.services import (
    ServiceLogEntry,
    ServiceResult,
    StorageServiceError,
)


class StorageModelTests(TestCase):
    """РўРµСЃС‚С‹ РјРѕРґРµР»Рё Storage (СЏС‡РµР№РєРё)"""
    
    def test_storage_creation(self):
        """РўРµСЃС‚ СЃРѕР·РґР°РЅРёСЏ СЏС‡РµР№РєРё С…СЂР°РЅРµРЅРёСЏ"""
        storage = Storage.objects.create(
            box_id='BOX001',
            cell_id='A1'
        )
        
        self.assertEqual(storage.box_id, 'BOX001')
        self.assertEqual(storage.cell_id, 'A1')
        self.assertEqual(str(storage), 'Р‘РѕРєСЃ BOX001, СЏС‡РµР№РєР° A1')
    
    def test_storage_cell_id_validation(self):
        """РўРµСЃС‚ РІР°Р»РёРґР°С†РёРё cell_id"""
        # РџСЂР°РІРёР»СЊРЅС‹Р№ С„РѕСЂРјР°С‚
        storage = Storage.objects.create(
            box_id='BOX002',
            cell_id='B12'
        )
        self.assertEqual(storage.cell_id, 'B12')
        
        # РќРµРїСЂР°РІРёР»СЊРЅС‹Р№ С„РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ РІС‹Р·С‹РІР°С‚СЊ РѕС€РёР±РєСѓ РІР°Р»РёРґР°С†РёРё
        with self.assertRaises(Exception):
            storage = Storage(
                box_id='BOX003',
                cell_id='invalid'
            )
            storage.full_clean()  # Р’С‹Р·С‹РІР°РµС‚ РІР°Р»РёРґР°С†РёСЋ
    
    def test_storage_unique_together(self):
        """РўРµСЃС‚ СѓРЅРёРєР°Р»СЊРЅРѕСЃС‚Рё РєРѕРјР±РёРЅР°С†РёРё box_id + cell_id"""
        Storage.objects.create(
            box_id='BOX004',
            cell_id='C3'
        )
        
        # РџРѕРїС‹С‚РєР° СЃРѕР·РґР°С‚СЊ РґСѓР±Р»РёРєР°С‚ РґРѕР»Р¶РЅР° РІС‹Р·РІР°С‚СЊ РѕС€РёР±РєСѓ
        with self.assertRaises(Exception):
            Storage.objects.create(
                box_id='BOX004',
                cell_id='C3'
            )


class StorageBoxModelTests(TestCase):
    """РўРµСЃС‚С‹ РјРѕРґРµР»Рё StorageBox (Р±РѕРєСЃС‹)"""
    
    def test_storage_box_creation(self):
        """РўРµСЃС‚ СЃРѕР·РґР°РЅРёСЏ Р±РѕРєСЃР°"""
        box = StorageBox.objects.create(
            box_id='BOX001',
            rows=8,
            cols=12,
            description='РўРµСЃС‚РѕРІС‹Р№ Р±РѕРєСЃ'
        )
        
        self.assertEqual(box.box_id, 'BOX001')
        self.assertEqual(box.rows, 8)
        self.assertEqual(box.cols, 12)
        self.assertEqual(box.description, 'РўРµСЃС‚РѕРІС‹Р№ Р±РѕРєСЃ')
        self.assertEqual(str(box), 'Р‘РѕРєСЃ BOX001 (8Г—12)')
    
    def test_storage_box_required_fields(self):
        """РўРµСЃС‚ РѕР±СЏР·Р°С‚РµР»СЊРЅС‹С… РїРѕР»РµР№ Р±РѕРєСЃР°"""
        from django.core.exceptions import ValidationError
        from django.db import IntegrityError
        
        # РўРµСЃС‚ СЃРѕР·РґР°РЅРёСЏ Р±РµР· box_id (РґРѕР»Р¶РЅРѕ РІС‹Р·РІР°С‚СЊ РѕС€РёР±РєСѓ)
        with self.assertRaises((ValidationError, IntegrityError)):
            box = StorageBox(
                # РџСЂРѕРїСѓСЃРєР°РµРј РѕР±СЏР·Р°С‚РµР»СЊРЅРѕРµ РїРѕР»Рµ box_id
                rows=8,
                cols=12
            )
            box.full_clean()  # Р’С‹Р·С‹РІР°РµРј РІР°Р»РёРґР°С†РёСЋ
            box.save()
    
    def test_storage_box_unique_box_id(self):
        """РўРµСЃС‚ СѓРЅРёРєР°Р»СЊРЅРѕСЃС‚Рё box_id"""
        StorageBox.objects.create(
            box_id='BOX002',
            rows=8,
            cols=12
        )
        
        # РџРѕРїС‹С‚РєР° СЃРѕР·РґР°С‚СЊ Р±РѕРєСЃ СЃ С‚РµРј Р¶Рµ box_id РґРѕР»Р¶РЅР° РІС‹Р·РІР°С‚СЊ РѕС€РёР±РєСѓ
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
        self.storage3 = Storage.objects.create(box_id='API_BOX001', cell_id='A3')

        self.strain = Strain.objects.create(short_code='API_STR001', identifier='API Test Strain')
        self.sample = Sample.objects.create(storage=self.storage1, strain=self.strain)

    def test_list_storages_endpoint(self):
        response = self.client.get('/api/storage/storages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 3)

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

    def test_bulk_assign_cells_endpoint(self):
        spare_sample = Sample.objects.create(strain=self.strain)
        payload = {
            'assignments': [
                {'cell_id': 'A3', 'sample_id': spare_sample.id}
            ]
        }
        response = self.client.post(
            f"/api/storage/boxes/{self.storage_box.box_id}/cells/bulk-assign/",
            json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        spare_sample.refresh_from_db()
        self.assertEqual(spare_sample.storage_id, self.storage3.id)
        self.assertEqual(response.data['statistics']['successful'], 1)
        self.assertFalse(response.data['errors'])

    def test_bulk_allocate_cells_endpoint(self):
        spare_sample = Sample.objects.create(strain=self.strain)
        payload = {
            'assignments': [
                {'cell_id': 'A3', 'sample_id': spare_sample.id}
            ]
        }
        response = self.client.post(
            f"/api/storage/boxes/{self.storage_box.box_id}/cells/bulk-allocate/",
            json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        spare_sample.refresh_from_db()
        # bulk allocate РЅРµ РґРѕР»Р¶РµРЅ СѓСЃС‚Р°РЅР°РІР»РёРІР°С‚СЊ primary РїРѕР»Рµ Сѓ РѕР±СЂР°Р·С†Р°
        self.assertIsNone(spare_sample.storage_id)
        # РїСЂРѕРІРµСЂСЏРµРј, С‡С‚Рѕ СЃРѕР·РґР°РЅР° РјСѓР»СЊС‚Рё-Р°Р»Р»РѕРєР°С†РёСЏ
        storage = Storage.objects.get(box_id=self.storage_box.box_id, cell_id='A3')
        from sample_management.models import SampleStorageAllocation
        self.assertTrue(SampleStorageAllocation.objects.filter(sample=spare_sample, storage=storage).exists())
        self.assertEqual(response.data['statistics']['successful'], 1)
        self.assertFalse(response.data['errors'])

    def test_cells_with_samples_without_strain_are_considered_occupied(self):
        Sample.objects.create(storage=self.storage2)  # Р±РµР· С€С‚Р°РјРјР°, РЅРѕ СЏС‡РµР№РєР° РґРѕР»Р¶РЅР° СЃС‡РёС‚Р°С‚СЊСЃСЏ Р·Р°РЅСЏС‚РѕР№

        overview = self.client.get('/api/storage/')
        self.assertEqual(overview.status_code, status.HTTP_200_OK)
        box_summary = next(box for box in overview.data['boxes'] if box['box_id'] == self.storage_box.box_id)
        self.assertEqual(box_summary['occupied'], 2)
        self.assertEqual(box_summary['free_cells'], box_summary['total_cells'] - 2)

        summary = self.client.get('/api/storage/summary/')
        self.assertEqual(summary.status_code, status.HTTP_200_OK)
        summary_box = next(box for box in summary.data['boxes'] if box['box_id'] == self.storage_box.box_id)
        self.assertEqual(summary_box['occupied'], 2)
        self.assertEqual(summary_box['free_cells'], summary_box['total'] - 2)

        free_cells_response = self.client.get(f"/api/storage/boxes/{self.storage_box.box_id}/cells/")
        self.assertEqual(free_cells_response.status_code, status.HTTP_200_OK)
        cell_ids = {cell['cell_id'] for cell in free_cells_response.data['cells']}
        self.assertNotIn('A2', cell_ids)

    @patch('storage_management.api.log_change')
    @patch('storage_management.api.storage_services.assign_primary_cell')
    def test_assign_cell_propagates_service_logs(self, mock_assign, mock_log_change):
        log_entry = ServiceLogEntry(
            content_type='sample',
            object_id=self.sample.id,
            action='UPDATE',
            old_values={'previous_storage_id': self.storage1.id},
            new_values={'storage_id': self.storage2.id},
            comment='test log entry',
            batch_id='batch-123',
        )
        mock_assign.return_value = ServiceResult(
            payload={
                'assignment': {
                    'sample_id': self.sample.id,
                    'box_id': self.storage_box.box_id,
                    'cell_id': 'A2',
                    'strain_code': self.strain.short_code if self.strain else None,
                }
            },
            logs=[log_entry],
        )

        response = self.client.post(
            f"/api/storage/boxes/{self.storage_box.box_id}/cells/A2/assign/",
            json.dumps({'sample_id': self.sample.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['assignment']['cell_id'], 'A2')
        mock_log_change.assert_called_once()
        logged_kwargs = mock_log_change.call_args.kwargs
        self.assertEqual(logged_kwargs['object_id'], self.sample.id)
        self.assertEqual(logged_kwargs['comment'], 'test log entry')
        self.assertEqual(logged_kwargs['batch_id'], 'batch-123')

    @patch('storage_management.api.storage_services.assign_primary_cell')
    def test_assign_cell_handles_service_error(self, mock_assign):
        mock_assign.side_effect = StorageServiceError(
            message='Ячейка занята',
            status_code=status.HTTP_409_CONFLICT,
            code='CELL_OCCUPIED',
            extra={'occupied_by': {'sample_id': self.sample.id}},
        )

        response = self.client.post(
            f"/api/storage/boxes/{self.storage_box.box_id}/cells/A2/assign/",
            json.dumps({'sample_id': self.sample.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['error_code'], 'CELL_OCCUPIED')
        self.assertIn('occupied_by', response.data)
        mock_assign.assert_called_once()


class StorageServiceConcurrencyTests(TransactionTestCase):
    """Проверка, что сервисный слой корректно сериализует конкурентные вызовы."""

    reset_sequences = True

    def setUp(self):
        self.box = StorageBox.objects.create(box_id='CC_BOX', rows=3, cols=3)
        # заранее создаём ячейку, чтобы сервис мог захватывать блокировку
        Storage.objects.create(box_id='CC_BOX', cell_id='A1')
        self.strain = Strain.objects.create(short_code='CC_STR', identifier='Concurrency Strain')

    def test_assign_primary_cell_serializes_conflicts(self):
        sample_one = Sample.objects.create(strain=self.strain)
        sample_two = Sample.objects.create(strain=self.strain)

        barrier = threading.Barrier(2)
        successes = []
        failures = []

        def worker(sample_id):
            connections.close_all()
            barrier.wait()
            try:
                storage_services.assign_primary_cell(
                    sample_id=sample_id,
                    box_id='CC_BOX',
                    cell_id='A1',
                )
                successes.append(sample_id)
            except StorageServiceError as exc:
                failures.append(exc.code)

        threads = [
            threading.Thread(target=worker, args=(sample_one.id,)),
            threading.Thread(target=worker, args=(sample_two.id,)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0], 'CELL_OCCUPIED_LEGACY')
        assigned_sample = Sample.objects.get(id=successes[0])
        self.assertIsNotNone(assigned_sample.storage_id)

    def test_allocate_cell_serializes_conflicts(self):
        sample_one = Sample.objects.create(strain=self.strain)
        sample_two = Sample.objects.create(strain=self.strain)

        barrier = threading.Barrier(2)
        successes = []
        failures = []

        def worker(sample_id):
            connections.close_all()
            barrier.wait()
            try:
                result = storage_services.allocate_sample_to_cell(
                    sample_id=sample_id,
                    box_id='CC_BOX',
                    cell_id='A1',
                    is_primary=False,
                )
                successes.append(result.payload['allocation']['sample_id'])
            except StorageServiceError as exc:
                failures.append(exc.code)

        threads = [
            threading.Thread(target=worker, args=(sample_one.id,)),
            threading.Thread(target=worker, args=(sample_two.id,)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0], 'ALLOCATION_OCCUPIED')
        self.assertEqual(
            SampleStorageAllocation.objects.filter(storage__box_id='CC_BOX', storage__cell_id='A1').count(),
            1,
        )


class StorageIntegrationTests(TestCase):
    """РРЅС‚РµРіСЂР°С†РёРѕРЅРЅС‹Рµ С‚РµСЃС‚С‹ РґР»СЏ storage_management"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_box_and_storage_relationship(self):
        """РўРµСЃС‚ СЃРІСЏР·Рё РјРµР¶РґСѓ Р±РѕРєСЃР°РјРё Рё СЏС‡РµР№РєР°РјРё"""
        # РЎРѕР·РґР°РµРј Р±РѕРєСЃ
        box = StorageBox.objects.create(
            box_id='INT_BOX001',
            rows=5,
            cols=5,
            description='РРЅС‚РµРіСЂР°С†РёРѕРЅРЅС‹Р№ С‚РµСЃС‚'
        )
        
        # РЎРѕР·РґР°РµРј СЏС‡РµР№РєРё РґР»СЏ СЌС‚РѕРіРѕ Р±РѕРєСЃР°
        storage1 = Storage.objects.create(
            box_id='INT_BOX001',
            cell_id='A1'
        )
        storage2 = Storage.objects.create(
            box_id='INT_BOX001',
            cell_id='A2'
        )
        
        # РџСЂРѕРІРµСЂСЏРµРј, С‡С‚Рѕ СЏС‡РµР№РєРё СЃРІСЏР·Р°РЅС‹ СЃ Р±РѕРєСЃРѕРј
        box_storages = Storage.objects.filter(box_id='INT_BOX001')
        self.assertEqual(box_storages.count(), 2)
        self.assertIn(storage1, box_storages)
        self.assertIn(storage2, box_storages)
    
    def test_storage_search_and_filtering(self):
        """РўРµСЃС‚ РїРѕРёСЃРєР° Рё С„РёР»СЊС‚СЂР°С†РёРё СЏС‡РµРµРє"""
        # РЎРѕР·РґР°РµРј С‚РµСЃС‚РѕРІС‹Рµ РґР°РЅРЅС‹Рµ
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
        
        # РўРµСЃС‚РёСЂСѓРµРј С„РёР»СЊС‚СЂР°С†РёСЋ РїРѕ box_id
        search_results = Storage.objects.filter(box_id='SEARCH_BOX001')
        self.assertEqual(search_results.count(), 2)
        
        # РўРµСЃС‚РёСЂСѓРµРј С„РёР»СЊС‚СЂР°С†РёСЋ РїРѕ cell_id
        a1_results = Storage.objects.filter(cell_id='A1')
        self.assertEqual(a1_results.count(), 2)  # A1 РµСЃС‚СЊ РІ РґРІСѓС… СЂР°Р·РЅС‹С… Р±РѕРєСЃР°С…


class StorageConsistencyCommandTests(TestCase):
    """Tests for the ensure_storage_consistency management command."""

    def test_creates_missing_box_and_cells(self):
        Storage.objects.create(box_id='NOBOX', cell_id='A1')
        Storage.objects.create(box_id='NOBOX', cell_id='A2')
        Storage.objects.create(box_id='NOBOX', cell_id='B1')

        call_command('ensure_storage_consistency', '--box', 'NOBOX')

        box = StorageBox.objects.get(box_id='NOBOX')
        self.assertEqual(box.rows, 2)
        self.assertEqual(box.cols, 2)
        self.assertTrue(Storage.objects.filter(box_id='NOBOX', cell_id='B2').exists())

    def test_updates_existing_box_dimensions(self):
        StorageBox.objects.create(box_id='META_BOX', rows=1, cols=1)
        Storage.objects.create(box_id='META_BOX', cell_id='A1')
        Storage.objects.create(box_id='META_BOX', cell_id='B1')
        Storage.objects.create(box_id='META_BOX', cell_id='C1')
        Storage.objects.create(box_id='META_BOX', cell_id='C2')

        call_command('ensure_storage_consistency', '--box', 'META_BOX')

        box = StorageBox.objects.get(box_id='META_BOX')
        self.assertEqual(box.rows, 3)
        self.assertEqual(box.cols, 2)

    def test_dry_run_does_not_mutate_data(self):
        Storage.objects.create(box_id='DRYBOX', cell_id='A1')
        Storage.objects.create(box_id='DRYBOX', cell_id='A2')
        Storage.objects.create(box_id='DRYBOX', cell_id='B1')

        call_command('ensure_storage_consistency', '--box', 'DRYBOX', '--dry-run')

        self.assertFalse(StorageBox.objects.filter(box_id='DRYBOX').exists())
        self.assertFalse(Storage.objects.filter(box_id='DRYBOX', cell_id='B2').exists())
