# Plan For Next LLM Agent

## Current Status (after latest run)
- Backend: `backend/strain_management/api.py` now exposes bulk delete/update/export, extended filters, and sample stats in parity with legacy. Unit tests were added but currently require a running PostgreSQL instance (`make db-up`).
- Frontend: both `frontend/src/services/api.ts` and `frontend/src/features/strains/services/strains-api.ts` target the modular `/api/strains/...` routes; Strain detail pages consume the new `samples_stats` payload.
- Docs: `api_router_cleanup_*` files reflect the latest status, and `collection_manager.api_status` enumerates only supported endpoints.

## Key Files
- Backend: `backend/strain_management/api.py`, `backend/strain_management/tests.py`, `backend/collection_manager/api.py` (api_status).
- Frontend: `frontend/src/services/api.ts`, `frontend/src/features/strains/services/strains-api.ts`, `frontend/src/pages/StrainDetail.tsx`.
- Docs: `docs/api_router_cleanup_plan.md`, `docs/api_router_cleanup_phase1.md`, `docs/api_router_cleanup_next_steps.md`, `docs/api_router_cleanup_handoff.md`.

## Tests & Infrastructure
```
bash
make db-up          # запускает PostgreSQL (порт 5433, пользователь strain_user)
python -m pytest backend/strain_management/tests.py
python -m pytest backend/storage_management/tests.py
make down           # останавливает контейнеры
```
> Примечание: без поднятого PostgreSQL pytest для strain_management завершится ошибкой подключения.

## Next Tasks
1. **Strain Management QA**
   - Прогнать pytest после `make db-up`, дополнить тесты для edge-case'ов (повторные короткие коды, пустые экспортные выборки, Excel без openpyxl).
   - Проверить CSV/Excel экспорт на реальных данных, зафиксировать размеры отдаваемых файлов.
2. **Legacy /api/reference-data/boxes/***
   - Повторно просканировать репозиторий (`rg "reference-data/boxes"`) и оформить TODO сроков деприкации для оставшихся прокси.
   - Подготовить заметку в docs (`api_router_cleanup_deprecation.md`) с планом оповещений пользователей.
3. **Документация и статус**
   - Поддерживать `api_status` и `docs/api_router_cleanup_*` синхронно с изменениями.
   - Добавить раздел о требованиях к БД в `README`/handbook при следующем обновлении.
4. **Frontend**
   - Убедиться, что UI корректно визуализирует новые поля (`samples_stats`, `free_cells`), при необходимости обновить сторибуки/скриншоты.
   - После правок запускать `npm test -- --watch=false` и `npm run lint`.

## Risks
- Без Postgres невозможно подтвердить новые pytest, что задерживает регрессионный отчёт.
- Внешние клиенты всё ещё могут зависеть от `/api/reference-data/boxes/...`; требуется согласованный grace-period.
- Необходимо избегать случайной утечки `.env*` и других секретов в логах/коммитах.

## Useful Commands
```
bash
# Документация статуса
python -m django shell -c "from collection_manager.api import api_status; print(api_status(None).data)"

# Smoke-проверки
curl http://localhost:8000/api/storage/summary/
curl http://localhost:8000/api/strains/export/?format=json
```
