# План работ для следующей LLM

## Общая цель
Перевести оставшиеся части API (в первую очередь strain_management) на модульную архитектуру, минимизировать использование legacy-прокси из collection_manager, поддерживать документацию и pi_status в актуальном состоянии и подготовить план полного отключения устаревших маршрутов.

## Шаги по приоритету

### 1. Strain Management
- Сравнить ackend/collection_manager/api.py и ackend/strain_management/api.py, выявить отсутствующие сценарии (bulk update/export/search/stats, edge-case'ы).
- При необходимости перенести вспомогательные утилиты из legacy (collection_manager.utils) в strain_management и адаптировать.
- Расширить тесты: ackend/strain_management/tests.py (CRUD, bulk, экспорт, corner cases). После изменений запускать python -m pytest backend/strain_management/tests.py (потребуется PostgreSQL: make db-up).
- Убедиться, что фронтовые клиенты для штаммов используют новые маршруты (rontend/src/services/api.ts, rontend/src/features/strains/...).

### 2. Legacy-прокси /api/reference-data/boxes/*
- Поиск по репозиторию: g "reference-data/boxes".
- Для каждого использования решить, можно ли перейти на /api/storage/boxes/.... Если нет — оставить прокси и задокументировать причину + TODO с планом деприкации.
- Обновить README/документацию (например, docs/api_router_cleanup_phase1.md) с явным предупреждением о legacy-статусе.

### 3. pi_status и документация
- При каждом изменении маршрутов синхронизировать ackend/collection_manager/api.py:39 (список эндпоинтов).
- Поддерживать в актуальном состоянии:
  - docs/api_router_cleanup_plan.md (чекбоксы, прогресс по фазам);
  - docs/api_router_cleanup_phase1.md (таблица маршрутов и потребителей);
  - docs/api_router_cleanup_next_steps.md (оперативный TODO-лист);
  - docs/api_router_cleanup_handoff.md (статус, риски, быстрый старт).

### 4. Frontend
- Проверить rontend/src/services/api.ts, rontend/src/pages/Storage.tsx, rontend/src/features/samples/services/samples-api.ts — нет ли залежей legacy-URL или несоответствий новым данным (ree_cells, generated_id, и т. д.).
- После правок запускать 
pm test -- --watch=false и 
pm run lint.
- При обновлении strain_management не забыть про UI/клиенты для штаммов.

### 5. План деприкации
- Составить отдельный документ (например, docs/api_router_cleanup_deprecation.md) с этапами: анонс → предупреждение → отключение legacy-прокси.
- Обсудить сроки, подготовить шаблон уведомления для пользователей и команд.
- Возможный дополнительный шаг: добавить в pi_status отдельный список deprecated-эндпоинтов.

### 6. Тесты и окружение
- Поднять БД: cd deployment && make db-up (PostgreSQL на localhost:5433, пользователь strain_user, БД strain_collection_test).
- Backend-тесты: python -m pytest backend/storage_management/tests.py backend/strain_management/tests.py (при изменениях в соответствующих модулях).
- Frontend: 
pm test -- --watch=false, 
pm run lint.
- Smoke после изменений: curl http://localhost:8000/api/storage/summary/, curl http://localhost:8000/api/strains/export/?format=json.

## Риски и вопросы
- Есть ли внешние клиенты, которые всё ещё используют /api/reference-data/boxes/*? Нужен grace-период.
- Какие сроки выключения legacy-прокси согласованы? Зафиксировать в документации.
- Какой backup-план, если при отключении всплывут неучтённые интеграции?

## Полезные файлы и ссылки
- Backend: ackend/storage_management/api.py, ackend/storage_management/tests.py, ackend/strain_management/api.py, ackend/collection_manager/api.py.
- Frontend: rontend/src/services/api.ts, rontend/src/pages/Storage.tsx, rontend/src/features/samples/services/samples-api.ts.
- Docs: docs/api_router_cleanup_plan.md, docs/api_router_cleanup_phase1.md, docs/api_router_cleanup_next_steps.md, docs/api_router_cleanup_handoff.md.

## Напоминания
- Не удалять legacy-прокси до утверждения плана деприкации.
- Следить за git status: в репозитории могут быть чужие незакоммиченные изменения.
- Секреты (.env*, Makefile) не коммитить и не публиковать.
- После каждого заметного шага обновлять pi_status, документацию и тесты — это основной критерий готовности.
