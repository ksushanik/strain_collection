# API Router Cleanup - Stage 2 Task Brief

## Кратко
- strain_management ещё требует сравнения с legacy: bulk/export/search/stats есть, но нужно пройтись по тестам и UI.
- sample_management и фронтовый клиент работают через новые маршруты, остаётся следить за регрессиями и добить edge-case'ы (growth media, фото, характеристики).
- Хранилище переведено на /api/storage/boxes/..., старые /api/reference-data/boxes/... живут только как прокси — стоит обозначить срок депривации.

## Цели
1. Убедиться, что новые маршруты полностью покрывают legacy-функциональность (strain + storage).
2. Минимизировать обращения к legacy collection_manager (оставить только необходимые прокси).
3. Держать документацию, pi_status и тесты в актуальном состоянии.
4. Подготовить план отключения устаревших URL.

## Блоки работ
### 1. Strain Management
- Пройтись по ackend/collection_manager/api.py и ackend/strain_management/api.py на предмет оставшихся расхождений.
- Проверить/дописать тесты: bulk export/search/stats + corner cases.
- Пересмотреть фронтовые клиенты (rontend/src/services/api.ts, feature clients) на предмет дублей и прямых обращений к legacy.

### 2. Storage & Frontend
- Отследить всех потребителей /api/storage/boxes/... и убрать остатки /api/reference-data/boxes/... там, где это возможно.
- В rontend/src/pages/Storage.tsx и сервисе pi.ts посмотреть, нет ли доп. логики, завязанной на старую форму ответа.
- Запланировать уведомление пользователям о переносе (release notes / changelog).

### 3. Legacy collection_manager
- Оставить только необходимые прокси в collection_manager/urls.py и отметить их как deprecated.
- Для отключения спланировать временной промежуток, подготовить fallback-план на случай неожиданных интеграций.
- Следить за pi_status, чтобы он отражал только поддерживаемые маршруты.

### 4. Документация и состояние
- Обновлять docs/api_router_cleanup_phase1.md, docs/api_router_cleanup_plan.md, README/handbook при каждом перемещении маршрутов.
- Поддерживать pi_router_cleanup_handoff.md в актуальном состоянии (статус по модулям, known issues).

### 5. Тесты и окружение
- Базовый набор: python -m pytest backend/storage_management/tests.py backend/strain_management/tests.py.
- Вспомогательно: 
pm test -- --watch=false, линтер фронта.
- При необходимости разворачивать PostgreSQL через make db-up (deployment/Makefile).

## Риски и вопросы
- Есть ли внешние клиенты, которые всё ещё держатся за /api/reference-data/boxes/*?
- Нужен ли grace-period с двойной публикацией маршрутов?
- Когда фиксируем конечный дедлайн по отключению collection_manager?
