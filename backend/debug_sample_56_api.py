#!/usr/bin/env python3
"""
Скрипт для проверки API данных образца 56
"""

import os
import sys
import django

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strain_tracker_project.settings')
django.setup()

from sample_management.models import Sample
from storage_management.models import Storage
import json

def debug_sample_56():
    """Проверяем данные образца 56 и их структуру"""
    
    try:
        # Получаем образец 56
        sample = Sample.objects.select_related(
            'strain', 'storage', 'source', 'location', 'index_letter',
            'iuk_color', 'amylase_variant'
        ).prefetch_related('growth_media').get(id=56)
        
        print("=== ДАННЫЕ ОБРАЗЦА 56 ===")
        print(f"ID: {sample.id}")
        print(f"Original Sample Number: {sample.original_sample_number}")
        print(f"Strain ID: {sample.strain_id}")
        print(f"Storage ID: {sample.storage_id}")
        
        if sample.storage:
            print(f"\n=== ДАННЫЕ ХРАНИЛИЩА ===")
            print(f"Storage ID: {sample.storage.id}")
            print(f"Box ID: {sample.storage.box_id}")
            print(f"Cell ID: {sample.storage.cell_id}")
            print(f"Storage String: {sample.storage}")
        else:
            print("Storage: None")
        
        # Проверяем структуру данных, которую ожидает фронтенд
        print(f"\n=== СТРУКТУРА ДЛЯ ФРОНТЕНДА ===")
        
        # Данные для currentCellData
        if sample.storage:
            current_cell_data = {
                'id': sample.storage.id,
                'cell_id': sample.storage.cell_id,
                'box_id': sample.storage.box_id
            }
            print(f"currentCellData: {json.dumps(current_cell_data, indent=2, ensure_ascii=False)}")
        
        # Данные для formData
        form_data = {
            'storage_id': sample.storage_id or sample.storage.id if sample.storage else None,
        }
        print(f"formData.storage_id: {form_data['storage_id']}")
        
        # Данные для selectedBoxId
        selected_box_id = sample.storage.box_id if sample.storage else None
        print(f"selectedBoxId: {selected_box_id}")
        
        print(f"\n=== ПРОВЕРКА API ENDPOINTS ===")
        
        # Проверяем, что возвращает API для свободных боксов
        from django.test import Client
        from django.contrib.auth.models import User
        
        # Создаем тестового пользователя если нужно
        user, created = User.objects.get_or_create(username='test_user')
        
        client = Client()
        client.force_login(user)
        
        # Проверяем /storage/boxes/free/
        response = client.get('/api/storage/')
        print(f"Storage snapshot API status: {response.status_code}")
        if response.status_code == 200:
            snapshot = response.json()
            boxes = snapshot.get('boxes', [])
            free_boxes = [box for box in boxes if (box.get('free_cells') or 0) > 0]
            print(f"Free boxes count: {len(free_boxes)}")

            box_1_data = next((box for box in boxes if str(box.get('box_id')) == '1'), None)
            if box_1_data:
                print(f"Box 1 snapshot: {json.dumps(box_1_data, indent=2, ensure_ascii=False)}")
            else:
                print("Box 1 not present in snapshot")
        
        # Проверяем /storage/boxes/1/free-cells/
        if sample.storage and sample.storage.box_id:
            response = client.get(f'/api/storage/boxes/{sample.storage.box_id}/cells/')
            print(f"\nFree cells API status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                cells = data.get('cells', [])
                print(f"Free cells count in box {sample.storage.box_id}: {len(cells)}")
                
                # Ищем ячейку G2
                cell_g2_found = False
                for cell in cells:
                    if cell.get('cell_id') == 'G2':
                        cell_g2_found = True
                        print(f"Cell G2 found in free cells: {json.dumps(cell, indent=2, ensure_ascii=False)}")
                        break
                
                if not cell_g2_found:
                    print("Cell G2 NOT found in free cells list")
        
        print(f"\n=== АНАЛИЗ ПРОБЛЕМЫ ===")
        print("Проблема может быть в том, что:")
        print("1. Бокс 1 не показывается в списке свободных боксов, так как все ячейки заняты")
        print("2. Ячейка G2 не показывается в списке свободных ячеек, так как она занята образцом 56")
        print("3. Компонент StorageAutocomplete не учитывает текущую ячейку при редактировании")
        
    except Sample.DoesNotExist:
        print("Образец 56 не найден")
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

def test_storage_queries():
    """Тестируем запросы к хранилищу напрямую"""
    from storage_management.models import Storage
    from sample_management.models import Sample
    
    print("\n=== ТЕСТИРОВАНИЕ ЗАПРОСОВ К ХРАНИЛИЩУ ===")
    
    # Проверяем свободные боксы
    occupied_boxes = Sample.objects.filter(storage__isnull=False).values_list('storage__box_id', flat=True).distinct()
    all_boxes = Storage.objects.values_list('box_id', flat=True).distinct().order_by('box_id')
    free_boxes = [box for box in all_boxes if box not in occupied_boxes]
    
    print(f"Все боксы: {list(all_boxes)}")
    print(f"Занятые боксы: {list(occupied_boxes)}")
    print(f"Свободные боксы: {free_boxes}")
    
    # Проверяем свободные ячейки в боксе 1
    occupied_cells_box1 = Sample.objects.filter(
        storage__box_id=1,
        storage__isnull=False
    ).values_list('storage__cell_id', flat=True)
    
    all_cells_box1 = Storage.objects.filter(box_id=1).values_list('cell_id', flat=True)
    free_cells_box1 = [cell for cell in all_cells_box1 if cell not in occupied_cells_box1]
    
    print(f"\nВсе ячейки в боксе 1: {list(all_cells_box1)}")
    print(f"Занятые ячейки в боксе 1: {list(occupied_cells_box1)}")
    print(f"Свободные ячейки в боксе 1: {free_cells_box1}")
    
    # Проверяем, есть ли вообще свободные ячейки
    total_storage = Storage.objects.count()
    occupied_storage = Sample.objects.filter(storage__isnull=False).count()
    free_storage = total_storage - occupied_storage
    
    print(f"\nОбщая статистика:")
    print(f"Всего мест хранения: {total_storage}")
    print(f"Занято: {occupied_storage}")
    print(f"Свободно: {free_storage}")

if __name__ == '__main__':
    try:
        debug_sample_56()
        test_storage_queries()
    except Sample.DoesNotExist:
        print("Образец 56 не найден")
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
