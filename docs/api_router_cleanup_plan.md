API Router Cleanup Plan
=======================

Context
-------
- Legacy `collection_manager` API still exposes large monolithic handlers that are no longer routed but referenced by docs and frontend.
- Modular apps (`strain_management`, `sample_management`, `storage_management`, `reference_data`, `audit_logging`) provide the current endpoints but miss parity with legacy features (bulk operations, exports, search, stats, etc.).
- `api_status` reports outdated paths, confusing clients and automated health checks.

Objectives
----------
1. Align exposed routes with actual backend capabilities.
2. Restore missing functionality (bulk/export/search) in modular apps and frontend.
3. Retire or deprecate unused legacy endpoints without breaking existing consumers.
4. Ensure documentation and status reporting reflect the new structure.

Work Breakdown
--------------
Phase 1 - Discovery & Alignment
- [x] Map every endpoint currently returned by `collection_manager.api.api_status` to real handlers.
- [x] Catalogue frontend calls (`frontend/src/services`, feature-specific clients) and docs references that still target legacy URLs. ✅ Обновлён `frontend/src/features/strains/services/strains-api.ts` для обращения к актуальным маршрутам.
- [ ] Decide retention strategy for `collection_manager` (deprecate vs. thin proxy layer).

Phase 2 - API Refactor
- [x] Extend `strain_management` views/urls with missing bulk, export, search, stats operations (reusing validated logic from legacy module). ✅ Bulk delete/update/export, расширенные фильтры и статистика перенесены, добавлены тесты.
- [x] Extend `sample_management` in the same fashion (bulk, export, photos, etc.). ✅ Completed: bulk delete/update, search, export, stats now live in `sample_management` with tests and Spectacular docs.
- [x] Consolidate storage routes under `storage_management` and migrate callers off `/api/reference-data/boxes/...` (storage clients now call `/api/storage/boxes/...`).
- [x] Update `api_status`, documentation, and tests to match the new routes.

Phase 3 - Frontend Updates
- [x] Point services in `frontend/src/services/api.ts` and feature clients to new modular endpoints. ✅ Основной сервис и feature-клиент штаммов синхронизированы с `/api/strains/...`.
  - [x] Samples feature client switched to modular endpoints (`frontend/src/features/samples/services/samples-api.ts`).
- [ ] Audit remaining feature-specific API clients (например, `features/strains/services/strains-api.ts`) на предмет дублирования логики; либо объединить с общим сервисом, либо оставить c явной пометкой.
- [ ] Проверить вспомогательные компоненты/страницы (`StrainDetail`, `Storage` UI) на корректное отображение новых payload (например, `samples_stats.free_cells`).

> Дополнительно: отдельно ведётся документ `docs/frontend_lint_cleanup_plan.md` — после наведения типового порядка в компонентах/сервисах связать статусы двух планов.

Phase 4 - Cleanup & Validation
- [ ] Remove unused handlers from `collection_manager/api.py` once parity confirmed.
- [ ] Adjust pytest suites (`backend/*/tests.py`, `backend/collection_manager/test_api.py`) to cover new endpoints and ensure regression coverage.
  - [x] Sample suite refreshed with bulk/search/export/stats coverage (`backend/sample_management/tests.py`).
- [ ] Run test suite and linting, update docs (README.md, API docs) accordingly.

Task Tracking
-------------
- [ ] Create migration plan for client-facing endpoints (include deprecation notice if needed).
- [ ] Define acceptance criteria per phase (e.g., bulk operations return 200 and update records correctly).
- [ ] Schedule regression test run on staging prior to release.
- [ ] Automate PostgreSQL availability in CI to unblock strain_management pytest suite (локально требуется `make db-up`).

Open Questions / To Clarify
---------------------------
- Do we need to maintain backwards-compatible proxies under `/api/...` for a grace period?
- Are there external integrations hitting the legacy endpoints beyond our frontend?
- Should analytics/statistics endpoints move to a dedicated module or stay under `collection_manager`?

Next Steps
----------
1. Confirm deprecation strategy with stakeholders.
2. Implement Phase 1 tasks and report findings.
3. Iterate through Phase 2/3 with PR checkpoints per module.

Testing Strategy
----------------
- Run targeted pytest suites after each backend module change (`pytest backend/strain_management tests`, etc.).
- Execute `pytest backend/collection_manager/test_api.py` until legacy proxies are removed to detect regressions early.
- For storage changes, cover `backend/storage_management/tests.py` and `backend/test_integration_api.py`.
- For frontend updates, run `npm test -- --watch=false` (or project equivalent) plus linting before merge.
- Wire CI to block merge if any of the above suites fail.
- Sample parity check: run `python -m pytest backend/sample_management/tests.py` once PostgreSQL (`localhost:5433`, user `strain_user`) is available; current environment lacks the DB, so execution deferred.
