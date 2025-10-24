#!/usr/bin/env python3
"""
Скрипт для исправления имен файлов с кириллическими символами.
Переименовывает файлы в безопасные ASCII имена и обновляет записи в базе данных.
"""

import os
import sys
import django
from pathlib import Path
import re
import uuid
from urllib.parse import unquote

# Настройка Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strain_tracker_project.settings')
django.setup()

from sample_management.models import SamplePhoto


def transliterate_cyrillic(text):
    """Транслитерация кириллицы в латиницу"""
    cyrillic_to_latin = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'YO',
        'Ж': 'ZH', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'KH', 'Ц': 'TS', 'Ч': 'CH', 'Ш': 'SH', 'Щ': 'SHCH',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'YU', 'Я': 'YA'
    }
    
    result = ''
    for char in text:
        result += cyrillic_to_latin.get(char, char)
    
    return result


def fix_cyrillic_filenames():
    """Исправляет имена файлов с кириллицей"""
    media_root = Path('/app/media')
    fixed_count = 0
    
    # Находим все фото с кириллицей в именах
    photos = SamplePhoto.objects.all()
    cyrillic_photos = []
    
    for photo in photos:
        if photo.image and re.search(r'[а-яё]', photo.image.name, re.IGNORECASE):
            cyrillic_photos.append(photo)
    
    print(f"Найдено {len(cyrillic_photos)} файлов с кириллицей в именах")
    
    for photo in cyrillic_photos:
        old_path = media_root / photo.image.name
        
        if not old_path.exists():
            print(f"Файл не найден: {old_path}")
            continue
        
        # Получаем имя файла и расширение
        old_name = old_path.name
        file_extension = old_path.suffix
        
        # Создаем новое имя файла
        # Вариант 1: Транслитерация
        new_name = transliterate_cyrillic(old_name)
        
        # Вариант 2: UUID (более надежно)
        if re.search(r'[а-яё]', new_name, re.IGNORECASE):
            new_name = f"{uuid.uuid4().hex}{file_extension}"
        
        # Создаем новый путь
        new_path = old_path.parent / new_name
        
        # Убеждаемся, что новое имя уникально
        counter = 1
        while new_path.exists():
            name_without_ext = new_name.rsplit('.', 1)[0]
            new_name = f"{name_without_ext}_{counter}{file_extension}"
            new_path = old_path.parent / new_name
            counter += 1
        
        try:
            # Переименовываем файл
            old_path.rename(new_path)
            
            # Обновляем запись в базе данных
            old_image_name = photo.image.name
            photo.image.name = str(new_path.relative_to(media_root))
            photo.save()
            
            print(f"Переименован: {old_image_name} -> {photo.image.name}")
            fixed_count += 1
            
        except Exception as e:
            print(f"Ошибка при переименовании {old_path}: {e}")
    
    print(f"Исправлено файлов: {fixed_count}")


if __name__ == '__main__':
    fix_cyrillic_filenames()