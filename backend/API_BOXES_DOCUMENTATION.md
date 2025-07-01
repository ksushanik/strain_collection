# API Documentation: Storage Boxes Management

## Обзор

Новые API endpoints для полноценного управления боксами хранения и операций с ячейками.

## Endpoints для боксов

### 1. Создание бокса
```http
POST /api/reference-data/boxes/create/
Content-Type: application/json

{
  "box_id": "BOX_001",
  "rows": 8,
  "cols": 12,
  "description": "Описание бокса (необязательно)"
}
```

**Ответ (201):**
```json
{
  "message": "Бокс успешно создан",
  "box": {
    "box_id": "BOX_001",
    "rows": 8,
    "cols": 12,
    "description": "Описание бокса",
    "cells_created": 96
  }
}
```

### 2. Получение информации о боксе
```http
GET /api/reference-data/boxes/{box_id}/
```

**Ответ (200):**
```json
{
  "box_id": "BOX_001",
  "rows": 8,
  "cols": 12,
  "description": "Описание бокса",
  "created_at": "2025-01-07T04:00:00Z",
  "statistics": {
    "total_cells": 96,
    "occupied_cells": 15,
    "free_marked_cells": 5,
    "empty_cells": 76,
    "occupancy_percentage": 15.6
  }
}
```

### 3. Обновление бокса
```http
PUT /api/reference-data/boxes/{box_id}/update/
Content-Type: application/json

{
  "description": "Новое описание бокса"
}
```

**Ответ (200):**
```json
{
  "message": "Бокс успешно обновлен",
  "box": {
    "box_id": "BOX_001",
    "rows": 8,
    "cols": 12,
    "description": "Новое описание бокса",
    "created_at": "2025-01-07T04:00:00Z"
  }
}
```

### 4. Удаление бокса
```http
DELETE /api/reference-data/boxes/{box_id}/delete/
```

**Параметры:**
- `?force=true` - принудительное удаление даже при наличии занятых ячеек

**Ответ (200):**
```json
{
  "message": "Бокс BOX_001 успешно удален",
  "statistics": {
    "cells_deleted": 96,
    "samples_freed": 15,
    "force_delete_used": false
  }
}
```

**Ошибка при наличии занятых ячеек (400):**
```json
{
  "error": "Бокс содержит 15 занятых ячеек. Используйте параметр ?force=true для принудительного удаления",
  "occupied_cells": 15,
  "can_force_delete": true
}
```

## Endpoints для ячеек

### 1. Размещение образца в ячейке
```http
PUT /api/reference-data/boxes/{box_id}/cells/{cell_id}/assign/
Content-Type: application/json

{
  "sample_id": 123
}
```

**Ответ (200):**
```json
{
  "message": "Образец успешно размещен в ячейке A1",
  "assignment": {
    "sample_id": 123,
    "box_id": "BOX_001",
    "cell_id": "A1",
    "strain_code": "STR_001"
  }
}
```

**Ошибки:**
- **400** - Ячейка уже занята
- **400** - Образец уже размещен в другой ячейке
- **404** - Ячейка или образец не найдены

### 2. Освобождение ячейки
```http
DELETE /api/reference-data/boxes/{box_id}/cells/{cell_id}/clear/
```

**Ответ (200):**
```json
{
  "message": "Ячейка A1 успешно освобождена",
  "freed_sample": {
    "sample_id": 123,
    "strain_code": "STR_001"
  }
}
```

### 3. Массовое размещение образцов
```http
POST /api/reference-data/boxes/{box_id}/cells/bulk-assign/
Content-Type: application/json

{
  "assignments": [
    {"cell_id": "A1", "sample_id": 123},
    {"cell_id": "A2", "sample_id": 124},
    {"cell_id": "B1", "sample_id": 125}
  ]
}
```

**Ответ (200):**
```json
{
  "message": "Массовое размещение завершено",
  "statistics": {
    "total_requested": 3,
    "successful": 2,
    "failed": 1
  },
  "successful_assignments": [
    {
      "sample_id": 123,
      "cell_id": "A1",
      "strain_code": "STR_001"
    },
    {
      "sample_id": 124,
      "cell_id": "A2",
      "strain_code": "STR_002"
    }
  ],
  "errors": [
    "Ячейка B1 уже занята образцом ID 100"
  ]
}
```

## Валидация

### Правила валидации для боксов:
- `box_id`: строка 1-20 символов, уникальная
- `rows`: целое число 1-99
- `cols`: целое число 1-99
- `description`: необязательная строка

### Правила валидации для ячеек:
- `cell_id`: формат `^[A-Z][0-9]{1,2}$` (например: A1, B12, Z99)
- `sample_id`: положительное целое число

## Логирование

Все операции логируются через систему `log_change`:
- **CREATE** - создание бокса
- **UPDATE** - обновление бокса
- **DELETE** - удаление бокса
- **ASSIGN_CELL** - размещение образца
- **CLEAR_CELL** - освобождение ячейки
- **BULK_ASSIGN_CELL** - массовое размещение

## Безопасность

- Все операции выполняются в транзакциях
- Проверка существования связанных объектов
- Валидация доступности ячеек перед размещением
- Защита от race conditions при одновременном доступе
- Детальные сообщения об ошибках без раскрытия внутренней структуры

## Тестирование

Для тестирования API используйте скрипт:
```bash
cd backend
python test_box_api.py
```

Скрипт проверяет:
- Создание тестового бокса
- Получение информации о боксе
- Обновление описания
- Получение списка ячеек
- Удаление бокса