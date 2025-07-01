#!/usr/bin/env python3
"""
Простой тест для проверки новых API endpoints для боксов
Запуск: python test_box_api.py
"""

import requests
import json
import sys

# Базовый URL API
BASE_URL = "http://localhost:8000/api"

def test_api_status():
    """Проверяем статус API"""
    print("🔍 Проверяем статус API...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API статус: {data.get('status')}")
            print(f"📋 Доступно endpoints: {len(data.get('endpoints', []))}")
            return True
        else:
            print(f"❌ API недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return False

def test_create_box():
    """Тестируем создание бокса"""
    print("\n📦 Тестируем создание бокса...")
    
    # Генерируем уникальный ID для избежания конфликтов
    import time
    timestamp = int(time.time())
    test_box_data = {
        "box_id": f"TEST_BOX_{timestamp}",
        "rows": 8,
        "cols": 12,
        "description": "Тестовый бокс для проверки API"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/reference-data/boxes/create/",
            json=test_box_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Бокс создан: {data.get('message')}")
            print(f"📊 Создано ячеек: {data.get('box', {}).get('cells_created')}")
            return test_box_data["box_id"]
        else:
            print(f"❌ Ошибка создания бокса: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Ошибка при создании бокса: {e}")
        return None

def test_get_box(box_id):
    """Тестируем получение информации о боксе"""
    print(f"\n📋 Тестируем получение информации о боксе {box_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/reference-data/boxes/{box_id}/")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Информация получена:")
            print(f"   📦 ID: {data.get('box_id')}")
            print(f"   📏 Размер: {data.get('rows')}×{data.get('cols')}")
            print(f"   📊 Всего ячеек: {data.get('statistics', {}).get('total_cells')}")
            print(f"   📈 Заполненность: {data.get('statistics', {}).get('occupancy_percentage')}%")
            return True
        else:
            print(f"❌ Ошибка получения информации: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при получении информации: {e}")
        return False

def test_update_box(box_id):
    """Тестируем обновление бокса"""
    print(f"\n✏️ Тестируем обновление бокса {box_id}...")
    
    update_data = {
        "description": "Обновленное описание тестового бокса"
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/reference-data/boxes/{box_id}/update/",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Бокс обновлен: {data.get('message')}")
            return True
        else:
            print(f"❌ Ошибка обновления: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при обновлении: {e}")
        return False

def test_get_box_cells(box_id):
    """Тестируем получение ячеек бокса"""
    print(f"\n🔍 Тестируем получение ячеек бокса {box_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/reference-data/boxes/{box_id}/cells/")
        
        if response.status_code == 200:
            data = response.json()
            cells = data.get('cells', [])
            print(f"✅ Получено ячеек: {len(cells)}")
            if cells:
                print(f"   📍 Первая ячейка: {cells[0].get('cell_id')}")
                print(f"   📍 Последняя ячейка: {cells[-1].get('cell_id')}")
            return True
        else:
            print(f"❌ Ошибка получения ячеек: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при получении ячеек: {e}")
        return False

def test_delete_box(box_id):
    """Тестируем удаление бокса"""
    print(f"\n🗑️ Тестируем удаление бокса {box_id}...")
    
    try:
        # Сначала пробуем удалить без force
        response = requests.delete(f"{BASE_URL}/reference-data/boxes/{box_id}/delete/")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Бокс удален: {data.get('message')}")
            print(f"📊 Удалено ячеек: {data.get('statistics', {}).get('cells_deleted')}")
            return True
        else:
            print(f"❌ Ошибка удаления: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при удалении: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов API для боксов")
    print("=" * 50)
    
    # Проверяем доступность API
    if not test_api_status():
        print("\n❌ API недоступен. Убедитесь, что Django сервер запущен на порту 8000")
        sys.exit(1)
    
    # Создаем тестовый бокс
    box_id = test_create_box()
    if not box_id:
        print("\n❌ Не удалось создать тестовый бокс")
        sys.exit(1)
    
    # Тестируем операции с боксом
    success_count = 0
    total_tests = 4
    
    if test_get_box(box_id):
        success_count += 1
    
    if test_update_box(box_id):
        success_count += 1
    
    if test_get_box_cells(box_id):
        success_count += 1
    
    if test_delete_box(box_id):
        success_count += 1
    
    # Результаты
    print("\n" + "=" * 50)
    print(f"📊 Результаты тестирования:")
    print(f"✅ Успешно: {success_count}/{total_tests}")
    print(f"❌ Неудачно: {total_tests - success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 Все тесты прошли успешно!")
        sys.exit(0)
    else:
        print("⚠️ Некоторые тесты не прошли")
        sys.exit(1)

if __name__ == "__main__":
    main()