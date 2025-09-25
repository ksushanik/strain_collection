#!/usr/bin/env python
"""
Предложение по улучшению модели Sample для решения проблемы дублирования номеров образцов

Анализ показал следующие паттерны дублирования:
1. 🔄 Один штамм в разных местах хранения (реплики)
2. 🧬 Вариации одного штамма (разные обработки: HS - heat shock, разные изоляты)
3. 🔀 Разные штаммы с одним номером образца

Предлагаемые изменения в модели:
"""

from django.db import models

class ImprovedSample(models.Model):
    """
    Улучшенная модель Sample с поддержкой реплик и вариаций
    """
    
    # Основные поля (существующие)
    original_sample_number = models.CharField(
        max_length=50, 
        verbose_name="Номер образца",
        help_text="Оригинальный номер образца из источника"
    )
    
    # НОВЫЕ ПОЛЯ для решения проблемы дублирования
    
    # 1. Поле для различения реплик одного образца
    replica_number = models.PositiveIntegerField(
        default=1,
        verbose_name="Номер реплики",
        help_text="Номер копии образца (1, 2, 3...)"
    )
    
    # 2. Поле для типа обработки образца
    PROCESSING_CHOICES = [
        ('original', 'Оригинальный'),
        ('hs', 'Heat Shock (HS)'),
        ('replica', 'Реплика'),
        ('subculture', 'Субкультура'),
        ('isolate', 'Изолят'),
    ]
    
    processing_type = models.CharField(
        max_length=20,
        choices=PROCESSING_CHOICES,
        default='original',
        verbose_name="Тип обработки",
        help_text="Тип обработки или состояние образца"
    )
    
    # 3. Поле для номера изолята/варианта
    isolate_number = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Номер изолята",
        help_text="Номер изолята или варианта (1, 2, 3, 4, 5...)"
    )
    
    # 4. Составной уникальный идентификатор
    @property
    def unique_sample_id(self):
        """
        Создает уникальный идентификатор образца
        Формат: {original_sample_number}-{isolate_number}-{processing_type}-{replica_number}
        Пример: 100I-2-HS-1
        """
        parts = [self.original_sample_number]
        
        if self.isolate_number:
            parts.append(self.isolate_number)
        
        if self.processing_type != 'original':
            parts.append(self.processing_type.upper())
        
        if self.replica_number > 1:
            parts.append(f"R{self.replica_number}")
        
        return "-".join(parts)
    
    # 5. Поле для группировки связанных образцов
    sample_group = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Группа образцов",
        help_text="Группа для связанных образцов (например, все варианты 100I)"
    )
    
    # Существующие поля
    strain = models.ForeignKey('strain_management.Strain', on_delete=models.CASCADE)
    storage = models.ForeignKey('storage_management.Storage', on_delete=models.CASCADE)
    
    class Meta:
        # Составной уникальный индекс
        unique_together = [
            ['original_sample_number', 'isolate_number', 'processing_type', 'replica_number']
        ]
        
        # Индексы для быстрого поиска
        indexes = [
            models.Index(fields=['original_sample_number']),
            models.Index(fields=['sample_group']),
            models.Index(fields=['processing_type']),
        ]
        
        verbose_name = "Образец"
        verbose_name_plural = "Образцы"
    
    def __str__(self):
        return self.unique_sample_id


# Миграция для существующих данных
def create_migration_script():
    """
    Скрипт для миграции существующих данных
    """
    migration_logic = """
    
    # Логика миграции существующих данных:
    
    1. Анализ существующих образцов:
       - Группировка по original_sample_number
       - Определение типа обработки по названию штамма (HS, номера изолятов)
       - Присвоение номеров реплик для дубликатов
    
    2. Алгоритм определения полей:
       
       def migrate_existing_sample(sample):
           strain_name = str(sample.strain)
           
           # Определяем тип обработки
           if 'HS' in strain_name:
               processing_type = 'hs'
           elif any(char.isdigit() for char in strain_name.split('-')[-1]):
               processing_type = 'isolate'
           else:
               processing_type = 'original'
           
           # Извлекаем номер изолята
           isolate_number = None
           parts = strain_name.split('-')
           for part in parts:
               if part.replace('HS', '').isdigit():
                   isolate_number = part.replace('HS', '')
                   break
           
           # Определяем номер реплики
           same_samples = Sample.objects.filter(
               original_sample_number=sample.original_sample_number,
               strain__name__contains=isolate_number or '',
               strain__name__contains='HS' if 'HS' in strain_name else ''
           )
           replica_number = list(same_samples).index(sample) + 1
           
           return {
               'processing_type': processing_type,
               'isolate_number': isolate_number,
               'replica_number': replica_number,
               'sample_group': sample.original_sample_number
           }
    
    3. Примеры результата миграции:
       
       Было: 100I (8 образцов с одинаковым номером)
       Стало:
       - 100I-1-ORIGINAL-1    (IB 2014I100-1)
       - 100I-1-HS-1          (IB 2014I100-1HS)
       - 100I-2-ORIGINAL-1    (IB 2014I100-2)
       - 100I-2-HS-1          (IB 2014I100-2HS)
       - 100I-3-ORIGINAL-1    (IB 2014I100-3)
       - 100I-3-HS-1          (IB 2014I100-3HS)
       - 100I-4-ORIGINAL-1    (IB 2014I100-4)
       - 100I-5-ORIGINAL-1    (IB 2014I100-5)
    """
    
    return migration_logic


# Преимущества нового подхода
def benefits_analysis():
    """
    Преимущества улучшенной модели:
    
    1. 🎯 Уникальность:
       - Каждый образец имеет уникальный составной ключ
       - Невозможно создать полные дубликаты
    
    2. 🔍 Улучшенный поиск:
       - Поиск по группам образцов
       - Фильтрация по типу обработки
       - Поиск реплик
    
    3. 📊 Лучшая аналитика:
       - Подсчет реплик
       - Анализ типов обработки
       - Группировка связанных образцов
    
    4. 🔧 Гибкость:
       - Легко добавлять новые типы обработки
       - Поддержка любого количества реплик
       - Сохранение связей между вариантами
    
    5. 📈 Масштабируемость:
       - Подготовка к росту коллекции
       - Стандартизация номенклатуры
       - Упрощение импорта новых данных
    """
    pass


if __name__ == "__main__":
    print("📋 Предложение по улучшению модели Sample")
    print("=" * 50)
    print(create_migration_script())
    print("\n" + "=" * 50)
    print("💡 Для реализации этого предложения потребуется:")
    print("1. Создание новой миграции Django")
    print("2. Скрипт для миграции существующих данных")
    print("3. Обновление форм и представлений")
    print("4. Обновление логики импорта CSV")
    print("5. Тестирование на существующих данных")