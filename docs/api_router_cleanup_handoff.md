# API Router Cleanup — текущий статус

## 1. База
- Ветка: pi-router-cleanup.
- Актуальные артефакты: docs/api_router_cleanup_plan.md, docs/api_router_cleanup_next_steps.md.
- Модульные приложения: strain_management, sample_management, storage_management, 
eference_data, udit_logging.

## 2. Что уже сделано
- sample_management приведён к parity с legacy: search/bulk/export/stats + фронтовый клиент.
- strain_management: перенесены bulk delete/update/export, расширенный поиск и статистика; обновлены тесты и Spectacular-схемы.
- storage_management обслуживает /api/storage/boxes/...; фронт (rontend/src/services/api.ts, страница Storage.tsx) использует новые маршруты.
- pi_status обновлён и больше не перечисляет legacy /api/reference-data/boxes/...; прокси в collection_manager сняты.
- Документация и чек-листы (docs/api_router_cleanup_*) отражают новое состояние.

## 3. Зона внимания
- strain_management — запустить pytest после поднятия PostgreSQL (`make db-up`), добить edge-case'ы и зафиксировать результаты.
- Убедиться, что нигде не остались прямые вызовы /api/reference-data/boxes/...; после вырезания прокси клиенты должны использовать storage_management.
- Спланировать деприкейшн legacy-эндпоинтов и донести до пользователей сроки.

## 4. Быстрый старт окружения
`ash
cd deployment
make db-up          # поднять PostgreSQL (порт 5433)
make backend-up     # запустить Django (venv ../strain_venv)
make frontend-up    # React dev-server

# Остановка сервисов
make down
`
БД для локальных pytest: host=localhost, port=5433, user=strain_user, dbname=strain_collection_test.

## 5. Команды и тесты
- Backend: python -m pytest backend/storage_management/tests.py backend/strain_management/tests.py (потребуется Postgres; локально поднять через `make db-up`).
- Frontend: 
pm test -- --watch=false, 
pm run lint.
- Быстрый smoke: curl http://localhost:8000/api/storage/summary/, Swagger: http://localhost:8000/docs/.

## 6. Ключевые файлы
- ackend/storage_management/api.py, ackend/storage_management/urls.py, ackend/storage_management/tests.py.
- ackend/collection_manager/api.py — прокси и pi_status.
- rontend/src/services/api.ts, rontend/src/pages/Storage.tsx, rontend/src/config/api.ts.
- docs/api_router_cleanup_phase1.md, docs/api_router_cleanup_plan.md, docs/api_router_cleanup_next_steps.md.

## 7. Важные замечания
- Отследить метрики и внешних потребителей: после вырезания прокси fallback больше нет, поэтому мониторинг критичен.
- Следить за git status: проект может содержать незакоммиченные правки, не связанные с cleanup.
- Не забывать про конфиденциальные данные в .env* и Makefile.

## 8. Следующие шаги
1. Пройтись по strain_management, синхронизировать поведение и дописать тесты.
2. Проиндексировать фронтовые вызовы на тему /api/reference-data/boxes/* и подтвердить, что все переведены на новые маршруты; подготовить уведомление о прекращении поддержки.
3. Описать дедлайн отключения legacy-маршрутов в changelog/релиз-нотах.
4. Подготовить финальный чек: pi_status + документация + smoke-тесты перед закрытием эпика.
