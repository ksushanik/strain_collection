# Frontend ESLint Cleanup Plan

## Цель
Избавиться от `any`, неиспользуемых переменных и устаревших конструкций, чтобы `npm run lint` проходил без ошибок и предупреждений.

## Текущие наблюдения
- Бóльшая часть ошибок лежит в компонентах выборок образцов (`AddSampleForm`, `EditSampleForm`, `SampleCharacteristics`, автокомплиты), а также в сервисах (`api.ts`, shared hooks/services).
- Многочисленные `any` используются для ответов API и обработчиков форм.
- В `BaseApiClient` и связанных тестах типы уже приведены в порядок — можно использовать их как пример.

## Практические шаги
1. **Обновить типы данных** *(частично выполнено)*
   - ✅ `SampleCharacteristicsUpdate`, справочники и часть API-ответов уже типизированы.
   - ⬜️ Продолжить расширение `frontend/src/types/index.ts` и `frontend/src/shared/types/**` для оставшихся сущностей (ростовые среды, bulk‑ответы, upload‑результаты и т. д.).

2. **Компоненты форм** *(в прогрессе)*
   - ✅ `AddSampleForm`, `EditSampleForm`, `SampleCharacteristics` переведены на строгие типы и `isAxiosError`.
   - ⬜️ Проверить `CreateStrainForm`, `GrowthMediaSelector`, фото‑загрузчик (`PhotoUpload`) — убрать `any`, синхронизировать сигнатуры `onChange`.

3. **Автокомплиты и панели**
   - ✅ `StorageAutocomplete` использует агрегированную статистику и типы `StorageBoxSummary`/`AutocompleteOption`.
   - ⬜️ Аналогично типизировать `StrainAutocomplete`, `SourceAutocomplete`, `GrowthMediaSelector` и `BulkOperationsPanel` (оставшиеся `any` в логике референсов).

4. **Shared слои**
   - ✅ `BaseApiClient` и его тесты приведены к строгим типам.
   - ⬜️ `shared/hooks/useApiError`, `shared/services/api.ts`, `shared/test/utils.tsx` — заменить `any`, уточнить интерфейсы ответов.

5. **Поэтапный прогон ESLint**
   - После каждого блока запускать `npm run lint`. Фиксировать повторяющиеся группы ошибок в этом документе, чтобы видеть оставшиеся точки.

6. **Логи и заглушки**
   - Продолжить удалять временные `console.log`; если требуется отладка — использовать локальные проверки/ошибки.

## Финальный контроль
- `npm run lint` — должен проходить без ошибок/предупреждений.
- `npm test -- --watch=false` — регрессия не допускается.
- Обновить документацию/next-agent заметки о завершении чистки.
