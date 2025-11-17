# План приведения UI хранения к полной консистентности с API

Цель: убрать любые клиентские вычисления и фоллбеки, использовать данные только из API, сохранить текущий UX (подпись бокса с размерностью и количеством свободных, список свободных ячеек для выбора).

## Ключевые принципы
- Источник правды: только API.
- Никаких расчётов на фронте по `rows×cols` и разнице занятости.
- Список свободных ячеек показывается только из `/api/storage/boxes/{box_id}/cells/`.
- Подпись бокса формируется из полей, пришедших из API (`rows`, `cols`, `free_cells`, `total_cells`).

## API, на которые опираемся
- `GET /api/storage/` — сводка по боксам: `boxes[].{box_id, rows, cols, description, total_cells, occupied_cells, free_cells}`.
- `GET /api/storage/boxes/{box_id}/cells/` — свободные ячейки: `cells[].{id: storage_id, cell_id, display_name}`.
- (для визуализации) `GET /api/storage/boxes/{box_id}/detail/` — `cells_grid` не используется для списка свободных.

## Изменения фронтенда

### 1) `frontend/src/services/api.ts`
Задача: убрать все клиентские вычисления в нормализаторах.

- В `normalizeStorageBox`:
  - Удалить расчёт `geometricalTotal` и вычисление `total_cells`/`free_cells` на фронте.
  - Принимать значения из ответа: `total_cells`, `occupied_cells`, `free_cells` как есть.
- В `normalizeStorageOverview`:
  - Удалить `fallbackTotalCells`, `fallbackOccupiedCells`, расчёт `free_cells` по разнице.
  - Возвращать поля как пришли из API.

Ориентиры в коде:
- `frontend/src/services/api.ts:212–235` — убрать геометрические вычисления.
- `frontend/src/services/api.ts:238–255` — убрать все fallback-расчёты.

### 2) `frontend/src/features/samples/components/StorageManager/StorageManager.tsx`
Задача: не считать totals и не дополнять список ячеек из `cells_grid`.

- Функция `loadBoxes`:
  - Формировать текст опции бокса с использованием `boxSummary.rows`, `boxSummary.cols`, `boxSummary.free_cells`, `boxSummary.total_cells` только из API.
  - Не использовать локальные вычисления `geometryTotal`.
- Функция `loadCells`:
  - Удалить фоллбек на `/detail/` и сбор свободных из `cells_grid`.
  - Список ячеек = ответ `/boxes/{box_id}/cells/`.

Ориентиры в коде:
- `frontend/src/features/samples/components/StorageManager/StorageManager.tsx:104–129` — убрать `geometryTotal`.
- `frontend/src/features/samples/components/StorageManager/StorageManager.tsx:157–178` — удалить блок фоллбека.

### 3) `frontend/src/features/samples/components/StorageAutocomplete/StorageAutocomplete.tsx`
Задача: привести к тем же правилам.

- В загрузке боксов убрать вычисления по геометрии и любые дополнительные попытки «обогащать» данные вне API.
- В загрузке ячеек убрать резервный канал из `cells_grid`.

Ориентиры в коде:
- `frontend/src/features/samples/components/StorageAutocomplete/StorageAutocomplete.tsx:36–76` — убрать расчёты `geometryTotal`/fallback.
- `frontend/src/features/samples/components/StorageAutocomplete/StorageAutocomplete.tsx:169–209` — удалить фоллбек `cells_grid`.

### 4) `frontend/src/features/samples/components/StorageMultiAssign/StorageMultiAssign.tsx`
Задача: аналогично `StorageManager`:

- В рендере боксов убирать расчёты по `rows×cols` и использовать только API-поля.

Ориентиры в коде:
- `frontend/src/features/samples/components/StorageMultiAssign/StorageMultiAssign.tsx:61–75`.

### 5) `frontend/src/pages/Storage.tsx`
Задача: не считать totals по геометрии.

- В подготовке `boxesWithState` использовать `box.total_cells`, `box.occupied`, `box.free_cells` из API без перерасчёта.

Ориентиры в коде:
- `frontend/src/pages/Storage.tsx:104–129`.

## Поведение после аллокаций/освобождений
- После успешного `POST /api/storage/boxes/{box_id}/cells/{cell_id}/allocate/`:
  - Перезапросить `/api/storage/` и обновить опции «Бокс» (цифры свободных).
  - Перезапросить `/api/storage/boxes/{box_id}/cells/` и обновить «Ячейка».
- После `DELETE /unallocate/` — аналогично.

## Валидация

### Команды
- `npm run lint`
- `npm run typecheck`
- `npm run test`
- `npm run test:e2e`

### Что проверяем
- Выпадающий «Бокс» показывает `ID (rows×cols) — свободно free/total`, где `free/total` пришли из `/api/storage/`.
- «Ячейка» содержит только позиции из `/api/storage/boxes/{box_id}/cells/`.
- После аллокации счетчики и список обновляются.

## E2E сценарии
- Поднять фикстуры: бокс 9×9, несколько свободных.
- Открыть `/samples/add`, выбрать бокс, убедиться в подписи и наличии свободных ячеек.
- Добавить аллокацию, проверить, что `free_cells` уменьшился, список ячеек обновился.

## Граничные случаи
- Боксы без `rows/cols`: фронт ничего не рассчитывает; отображает то, что пришло из API (возможны 0/0). Требуется корректировка данных на бэкенде.
- Если API вернул `null`/`0` в totals — показываем как есть, без попытки «угадывать».

## Критерии приемки
- Все отображаемые числа и списки соответствуют ответам API без клиентских вычислений.
- Фоллбеки из `cells_grid` отсутствуют.
- Линт, тайпчек, юнит и e2e тесты проходят.

## Чеклист задач
- [x] api.ts: убрать вычисления в `normalizeStorageBox`.
- [x] api.ts: убрать fallback в `normalizeStorageOverview`.
- [x] StorageManager: убрать `geometryTotal`, удалить фоллбек из `loadCells`.
- [x] StorageAutocomplete: убрать расчёты и фоллбек.
- [x] StorageMultiAssign: убрать расчёты по геометрии.
- [x] Storage.tsx: убрать fallback-расчёты totals.
- [x] Обновить перезапросы после аллокаций/освобождений.
- [x] Линт/тайпчек/тесты/e2e выполнены и зелёные.