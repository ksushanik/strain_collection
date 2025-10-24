#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from pathlib import Path

def transliterate_cyrillic(text):
    """Простая транслитерация кириллицы в латиницу"""
    cyrillic_to_latin = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    
    result = ''
    for char in text:
        result += cyrillic_to_latin.get(char, char)
    
    return result

def has_cyrillic(text):
    """Проверяет, содержит ли текст кириллические символы"""
    return bool(re.search('[а-яё]', text, re.IGNORECASE))

def rename_files_in_directory(directory_path):
    """Переименовывает файлы с кириллицей в указанной директории"""
    directory = Path(directory_path)
    
    if not directory.exists():
        print(f"Директория {directory_path} не существует")
        return
    
    renamed_files = []
    
    # Рекурсивно обходим все файлы
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            filename = file_path.name
            
            if has_cyrillic(filename):
                # Создаем новое имя файла
                new_filename = transliterate_cyrillic(filename)
                new_file_path = file_path.parent / new_filename
                
                # Проверяем, что файл с таким именем не существует
                counter = 1
                original_new_filename = new_filename
                while new_file_path.exists():
                    name_part, ext = os.path.splitext(original_new_filename)
                    new_filename = f"{name_part}_{counter}{ext}"
                    new_file_path = file_path.parent / new_filename
                    counter += 1
                
                try:
                    # Переименовываем файл
                    file_path.rename(new_file_path)
                    renamed_files.append({
                        'old': str(file_path),
                        'new': str(new_file_path),
                        'old_name': filename,
                        'new_name': new_filename
                    })
                    print(f"Переименован: {filename} -> {new_filename}")
                except Exception as e:
                    print(f"Ошибка при переименовании {filename}: {e}")
    
    return renamed_files

if __name__ == "__main__":
    # Путь к директории с медиа файлами
    media_path = "/app/media"
    
    print("Начинаем переименование файлов с кириллицей...")
    print(f"Директория: {media_path}")
    
    renamed = rename_files_in_directory(media_path)
    
    print(f"\nВсего переименовано файлов: {len(renamed)}")
    
    if renamed:
        print("\nСписок переименованных файлов:")
        for item in renamed:
            print(f"  {item['old_name']} -> {item['new_name']}")