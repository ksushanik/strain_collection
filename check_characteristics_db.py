#!/usr/bin/env python3
"""
Скрипт для проверки сохранения характеристик в базе данных
"""

import requests
import json

# Настройки
BASE_URL = "http://localhost:8000"
SAMPLE_ID = 3  # ID образца для проверки

def check_sample_characteristics():
    """Проверяет характеристики образца через API"""
    
    print(f"🔍 Проверяем характеристики образца {SAMPLE_ID}")
    
    # Получаем данные образца
    url = f"{BASE_URL}/api/samples/{SAMPLE_ID}/"
    
    try:
        response = requests.get(url)
        
        print(f"📥 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            sample_data = response.json()
            print(f"📥 Данные образца: {json.dumps(sample_data, ensure_ascii=False, indent=2)}")
            
            # Проверяем есть ли характеристики в ответе
            if 'characteristics' in sample_data:
                print("✅ Поле 'characteristics' найдено в ответе!")
                print(f"🔍 Характеристики: {json.dumps(sample_data['characteristics'], ensure_ascii=False, indent=2)}")
            else:
                print("❌ Поле 'characteristics' не найдено в ответе")
                print("📋 Доступные поля:", list(sample_data.keys()))
        else:
            print("❌ Ошибка при получении данных образца")
            print(f"📥 Ответ сервера: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def check_characteristics_list():
    """Проверяет список всех характеристик"""
    
    print(f"\n🔍 Проверяем список всех характеристик")
    
    url = f"{BASE_URL}/api/samples/characteristics/"
    
    try:
        response = requests.get(url)
        
        print(f"📥 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            characteristics = response.json()
            print(f"📥 Количество характеристик: {len(characteristics)}")
            
            # Ищем нашу характеристику
            for char in characteristics:
                if char['name'] == 'Вырабатывает сидерофоры':
                    print(f"✅ Найдена характеристика: {json.dumps(char, ensure_ascii=False, indent=2)}")
                    break
            else:
                print("❌ Характеристика 'Вырабатывает сидерофоры' не найдена")
        else:
            print("❌ Ошибка при получении списка характеристик")
            print(f"📥 Ответ сервера: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_sample_characteristics()
    check_characteristics_list()