# Storage Boxes API

Актуальная документация по REST-интерфейсам, обслуживающим хранение образцов. Все маршруты расположены под префиксом `/api/storage/` и предоставляются приложением `storage_management`.

## 1. Краткий обзор

| Цель                              | Метод | URI                                             |
|-----------------------------------|-------|--------------------------------------------------|
| Сводный снимок по всем боксам     | GET   | `/api/storage/`                                 |
| Детальный грид по боксу           | GET   | `/api/storage/boxes/{box_id}/detail/`           |
| Свободные ячейки бокса            | GET   | `/api/storage/boxes/{box_id}/cells/`            |
| Создать бокс                      | POST  | `/api/storage/boxes/create/`                    |
| Получить/обновить/удалить бокс    | GET/PUT/DELETE | `/api/storage/boxes/{box_id}/`/`update/`/`delete/` |
| Разместить образец в ячейке       | POST  | `/api/storage/boxes/{box_id}/cells/{cell_id}/allocate/` |
| Удалить размещение                | DELETE| `/api/storage/boxes/{box_id}/cells/{cell_id}/unallocate/` |
| Массовое размещение дополнительных ячеек | POST | `/api/storage/boxes/{box_id}/cells/bulk-allocate/` |

> **Важно:** прежние ручки `assign`, `clear`, `bulk-assign` остаются только для совместимости и помечены заголовком `X-Endpoint-Deprecated`. Клиенты должны перейти на `allocate/unallocate`.

## 2. Снимок хранилища

### GET `/api/storage/`
Возвращает упорядоченный список боксов и агрегаты.

```json
{
  "boxes": [
    {
      "box_id": "BOX-08",
      "rows": 9,
      "cols": 9,
      "description": "Основной бокс",
      "occupied": 78,
      "free_cells": 3,
      "total_cells": 81,
      "cells": [
        {
          "id": 1234,
          "box_id": "BOX-08",
          "cell_id": "A1",
          "occupied": true,
          "sample_id": 567,
          "strain_code": "STR-001",
          "is_free_cell": false
        }
        /* ... */
      ]
    }
  ],
  "total_boxes": 12,
  "total_cells": 972,
  "occupied_cells": 620,
  "free_cells": 352
}
```

* `cells` присутствуют только для уже инициализированных ячеек; поле пригодно для построения агрегатов без дополнительного запроса.
* Список упорядочен по числовой части идентификатора бокса и, при равенстве, в алфавитном порядке.

### GET `/api/storage/boxes/{box_id}/detail/`
Возвращает грид ячеек выбранного бокса (используется на фронтенде для раскрытой карточки).

```json
{
  "box_id": "BOX-08",
  "rows": 9,
  "cols": 9,
  "description": "Основной бокс",
  "total_cells": 81,
  "occupied_cells": 78,
  "free_cells": 3,
  "occupancy_percentage": 96.3,
  "cells_grid": [
    [
      {
        "row": 1,
        "col": 1,
        "cell_id": "A1",
        "storage_id": 1234,
        "is_occupied": true,
        "sample_info": {
          "sample_id": 567,
          "strain_id": 42,
          "strain_number": "STR-001",
          "comment": null,
          "total_samples": 1
        }
      },
      {
        "row": 1,
        "col": 2,
        "cell_id": "A2",
        "storage_id": null,
        "is_occupied": false,
        "sample_info": null
      }
    ]
    /* ... */
  ]
}
```

Ошибки:
* `404` — бокс не найден или ещё не инициализирован (нет геометрии),
* `409` — геометрия не может быть определена (если в БД неконсистентные данные).

### GET `/api/storage/boxes/{box_id}/cells/`
Возвращает первые 100 свободных ячеек для автокомплита в форме.

Ответ:
```json
{
  "box_id": "BOX-08",
  "cells": [
    { "id": 2345, "box_id": "BOX-08", "cell_id": "I7", "display_name": "Cell I7" }
    /* ... */
  ]
}
```

Параметр `search` фильтрует по подстроке в ID ячейки или ID бокса.

## 3. Управление боксами

### POST `/api/storage/boxes/create/`
```json
{
  "box_id": "BOX-08",
  "rows": 9,
  "cols": 9,
  "description": "Основной бокс"
}
```

Ответ `201`:
```json
{
  "message": "Бокс создан",
  "box": {
    "box_id": "BOX-08",
    "rows": 9,
    "cols": 9,
    "description": "Основной бокс",
    "created_at": "2025-10-29T13:00:00Z"
  }
}
```

### GET `/api/storage/boxes/{box_id}/`
Возвращает метаданные бокса и агрегаты (без грида):
```json
{
  "box_id": "BOX-08",
  "rows": 9,
  "cols": 9,
  "description": "Основной бокс",
  "created_at": "2025-10-29T13:00:00Z",
  "statistics": {
    "total_cells": 81,
    "occupied_cells": 78,
    "free_cells": 3,
    "occupancy_percentage": 96.3
  }
}
```

### PUT `/api/storage/boxes/{box_id}/update/`
```json
{
  "description": "Запасной бокс"
}
```
Ответ `200` аналогично GET.

### DELETE `/api/storage/boxes/{box_id}/delete/`
* флаг `?force=true` разрешает удаление даже при занятых ячейках.
* Успешный ответ возвращает статистику по удалённым ячейкам и освободившимся образцам.
* При попытке удалить без `force` при занятых ячейках — `400` с подсказкой.

## 4. Работа с ячейками

### POST `/api/storage/boxes/{box_id}/cells/{cell_id}/allocate/`
```json
{
  "sample_id": 567,
  "is_primary": true
}
```

Ответ `200`:
```json
{
  "message": "Размещение выполнено",
  "allocation": {
    "sample_id": 567,
    "box_id": "BOX-08",
    "cell_id": "A1",
    "storage_id": 1234,
    "is_primary": true,
    "created": true
  }
}
```

Ошибки (`StorageServiceError`):
* `409 LEGACY_CELL_OCCUPIED` — legacy-ячейка занята, надо очистить `clear_storage_cell` или перевести данные вручную.
* `400 ALLOCATION_OCCUPIED` — ячейка занята allocation другого образца.
* `404 SAMPLE_NOT_FOUND` или `STORAGE_NOT_FOUND` — некорректные идентификаторы.

### DELETE `/api/storage/boxes/{box_id}/cells/{cell_id}/unallocate/`
```json
{
  "sample_id": 567
}
```

Ответ `200`:
```json
{
  "message": "Размещение удалено",
  "unallocated": {
    "sample_id": 567,
    "box_id": "BOX-08",
    "cell_id": "A1",
    "was_primary": true
  }
}
```

### POST `/api/storage/boxes/{box_id}/cells/bulk-allocate/`
Используется для добавления дополнительных (не основных) ячеек.
```json
{
  "assignments": [
    { "cell_id": "A3", "sample_id": 567 },
    { "cell_id": "A4", "sample_id": 567 }
  ]
}
```

Ответ `200`:
```json
{
  "message": "Массовое размещение выполнено",
  "statistics": {
    "total_requested": 2,
    "successful": 2,
    "failed": 0
  },
  "successful_allocations": [
    { "sample_id": 567, "cell_id": "A3", "storage_id": 3456, "is_primary": false },
    { "sample_id": 567, "cell_id": "A4", "storage_id": 3457, "is_primary": false }
  ],
  "errors": []
}
```

## 5. Заголовки депрекации

Для legacy-ручек (`assign`, `clear`, `bulk-assign`) ответы содержат:

```
X-Endpoint-Deprecated: true
X-Endpoint-Name: assign_cell
X-Endpoint-Deprecated-Message: Endpoint /assign/ is deprecated. Use POST /allocate/ with payload {"is_primary": true}.
X-Endpoint-Replacement: /api/storage/boxes/{box_id}/cells/{cell_id}/allocate/
```

Фронтенд и интеграции должны реагировать на эти заголовки и выводить предупреждение пользователю.

## 6. Логи и аудит

Каждая операция меняет журнал `log_change` через сервисный слой:
* `allocate`/`bulk-allocate` — `action="UPDATE"` для образца, сохраняется история предыдущей основной ячейки;
* `unallocate` — помечает удаление allocation и сбрасывает `sample.storage` при необходимости;
* операции с боксами — `action="CREATE"`, `UPDATE`, `DELETE`.

Для проверки консистентности доступны:
* управляющая команда `python manage.py ensure_storage_consistency [--dry-run]`;
* скрипт `backend/scripts/audit_storage_state.py` (использует тот же snapshot).

## 7. История изменений

* **2025‑10‑29** — консолидация API на `/api/storage/…`, введены `allocate/unallocate`, добавлены заголовки депрекации.
* **2025‑10‑28** — миграция snapshot-эндпоинтов на общий сервис `build_storage_snapshot`.

---
Последнее обновление: 29.10.2025.
