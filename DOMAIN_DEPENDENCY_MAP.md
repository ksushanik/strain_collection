# Карта зависимостей между доменами

## Обзор архитектуры

Система коллекции штаммов состоит из 5 основных приложений Django:

1. **collection_manager** - Монолитное приложение (legacy)
2. **strain_management** - Управление штаммами
3. **sample_management** - Управление образцами
4. **storage_management** - Управление хранилищем
5. **reference_data** - Справочные данные

## Детальная карта зависимостей

### 1. Домен: Справочные данные (reference_data)
**Роль**: Центральный справочник, не зависит от других доменов

**Модели**:
- `IndexLetter` - Индексные буквы
- `Location` - Местоположения
- `Source` - Источники образцов
- `IUKColor` - Цвета ИУК
- `AmylaseVariant` - Варианты амилазы
- `GrowthMedium` - Среды роста

**Зависимости**: Нет исходящих зависимостей
**Потребители**: Все остальные домены

---

### 2. Домен: Управление штаммами (strain_management)
**Роль**: Каталог штаммов микроорганизмов

**Модели**:
- `Strain` - Штаммы микроорганизмов

**Зависимости**: Нет прямых зависимостей
**Потребители**: sample_management

**Поля**:
- `short_code` - Короткий код штамма
- `rrna_taxonomy` - rRNA таксономия
- `identifier` - Идентификатор штамма
- `name_alt` - Альтернативное название
- `rcam_collection_id` - ID коллекции RCAM

---

### 3. Домен: Управление хранилищем (storage_management)
**Роль**: Физическое размещение образцов

**Модели**:
- `Storage` - Ячейки хранения (бокс + ячейка)
- `StorageBox` - Боксы/контейнеры

**Зависимости**: Нет прямых зависимостей
**Потребители**: sample_management

**Связи**:
- `StorageBox` → `Storage` (один ко многим, через box_id)

---

### 4. Домен: Управление образцами (sample_management)
**Роль**: Центральный домен, связывающий штаммы с хранилищем

**Модели**:
- `Sample` - Образцы штаммов
- `SampleGrowthMedia` - Связь образцов со средами роста
- `SamplePhoto` - Фотографии образцов

**Зависимости**:
```
Sample → strain_management.Strain (ForeignKey, CASCADE)
Sample → storage_management.Storage (ForeignKey, SET_NULL)
Sample → reference_data.IndexLetter (ForeignKey, SET_NULL)
Sample → reference_data.Source (ForeignKey, SET_NULL)
Sample → reference_data.Location (ForeignKey, SET_NULL)
Sample → reference_data.IUKColor (ForeignKey, SET_NULL)
Sample → reference_data.AmylaseVariant (ForeignKey, SET_NULL)

SampleGrowthMedia → Sample (ForeignKey, CASCADE)
SampleGrowthMedia → reference_data.GrowthMedium (ForeignKey, CASCADE)

SamplePhoto → Sample (ForeignKey, CASCADE)
```

---

### 5. Домен: Монолитный менеджер (collection_manager) - LEGACY
**Роль**: Дублирует функциональность других доменов, подлежит разбиению

**Модели** (дублируют функциональность):
- `IndexLetter`, `Location`, `Source` → reference_data
- `Storage` → storage_management  
- `Strain` → strain_management
- `Sample`, `SampleGrowthMedia` → sample_management
- `IUKColor`, `AmylaseVariant`, `GrowthMedium` → reference_data
- `Comment`, `AppendixNote` → audit_logging
- `ChangeLog` → audit_logging
- `StorageBox` → storage_management

## Анализ связей по типам

### Сильные связи (CASCADE)
```
strain_management.Strain ←→ sample_management.Sample
sample_management.Sample ←→ sample_management.SampleGrowthMedia
sample_management.Sample ←→ sample_management.SamplePhoto
```

### Слабые связи (SET_NULL)
```
reference_data.* ←→ sample_management.Sample
storage_management.Storage ←→ sample_management.Sample
```

## Рекомендации по микросервисной архитектуре

### Bounded Context'ы

1. **Catalog Service** (strain_management + reference_data)
   - Управление каталогом штаммов
   - Справочные данные
   - Независимый сервис

2. **Sample Service** (sample_management)
   - Управление образцами
   - Связи с каталогом и хранилищем
   - Центральный сервис

3. **Storage Service** (storage_management)
   - Управление физическим хранилищем
   - Независимый сервис

4. **Audit Service** (audit_logging)
   - Журналирование изменений
   - Независимый сервис

### Стратегия миграции

**Этап 1**: Разбиение collection_manager
- Перенести модели в соответствующие приложения
- Обновить импорты и зависимости
- Сохранить единую базу данных

**Этап 2**: API Gateway
- Создать единую точку входа
- Маршрутизация запросов по доменам
- Сохранить REST API совместимость

**Этап 3**: Выделение сервисов
- Отдельные базы данных
- Асинхронная коммуникация через события
- Saga pattern для транзакций

### Критические точки

1. **Sample ↔ Strain связь**: Сильная связь, требует careful design
2. **Sample ↔ Storage связь**: Может быть асинхронной
3. **Reference Data**: Может быть кэширована в других сервисах
4. **Audit Logging**: Должен быть event-driven

### Метрики успеха

- Время отклика API < 200ms
- Доступность каждого сервиса > 99.9%
- Возможность независимого деплоя
- Отсутствие циклических зависимостей между сервисами