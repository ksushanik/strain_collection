#!/usr/bin/env python
"""
Модуль для нормализации текста - замена визуально похожих кириллических символов на латинские
"""

def normalize_cyrillic_to_latin(text):
    """
    Заменяет кириллические символы, которые визуально похожи на латинские,
    на соответствующие латинские символы.
    
    Args:
        text (str): Исходный текст
        
    Returns:
        str: Нормализованный текст с латинскими символами
    """
    if not text or not isinstance(text, str):
        return text
    
    # Словарь замен кириллических символов на латинские
    cyrillic_to_latin = {
        'А': 'A',  # U+0410 -> U+0041
        'В': 'B',  # U+0412 -> U+0042
        'Е': 'E',  # U+0415 -> U+0045
        'К': 'K',  # U+041A -> U+004B
        'М': 'M',  # U+041C -> U+004D
        'Н': 'H',  # U+041D -> U+0048
        'О': 'O',  # U+041E -> U+004F
        'Р': 'P',  # U+0420 -> U+0050
        'С': 'C',  # U+0421 -> U+0043
        'Т': 'T',  # U+0422 -> U+0054
        'У': 'Y',  # U+0423 -> U+0059 (приблизительно)
        'Х': 'X',  # U+0425 -> U+0058
        'а': 'a',  # U+0430 -> U+0061
        'е': 'e',  # U+0435 -> U+0065
        'о': 'o',  # U+043E -> U+006F
        'р': 'p',  # U+0440 -> U+0070
        'с': 'c',  # U+0441 -> U+0063
        'у': 'y',  # U+0443 -> U+0079
        'х': 'x',  # U+0445 -> U+0078
    }
    
    # Применяем замены
    normalized_text = text
    for cyrillic, latin in cyrillic_to_latin.items():
        normalized_text = normalized_text.replace(cyrillic, latin)
    
    return normalized_text


def test_normalization():
    """Тестирует функцию нормализации"""
    test_cases = [
        ('11А', '11A'),  # Кириллическая А -> латинская A
        ('12В', '12B'),  # Кириллическая В -> латинская B
        ('ABC', 'ABC'),  # Уже латинские символы
        ('123', '123'),  # Цифры остаются без изменений
        ('АВС123', 'ABC123'),  # Смешанный текст
        ('', ''),  # Пустая строка
        (None, None),  # None
    ]
    
    print("🧪 Тестирование нормализации:")
    print("=" * 40)
    
    for input_text, expected in test_cases:
        result = normalize_cyrillic_to_latin(input_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_text}' -> '{result}' (ожидалось: '{expected}')")
        
        if input_text and isinstance(input_text, str):
            print(f"   Unicode коды входа: {[ord(c) for c in input_text]}")
            print(f"   Unicode коды выхода: {[ord(c) for c in result]}")
        print()


if __name__ == "__main__":
    test_normalization()