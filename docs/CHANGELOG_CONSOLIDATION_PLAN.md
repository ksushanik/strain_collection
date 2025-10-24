## Консолидация журнала изменений

### Текущее состояние
- **Две модели `ChangeLog`**:  
  - `audit_logging.models.ChangeLog` — таблица `audit_changelog` с именованными индексами.  
  - `collection_manager.models.ChangeLog` — таблица `changelog` без именованных индексов.
- **Импорты**: `collection_manager` (admin/utils/tests), `strain_tracker_project/admin.py` и ряд тестов используют локальную модель.
- **Миграции**:  
  - `collection_manager/migrations/0004_create_changelog.py` создаёт таблицу `changelog`.  
  - `audit_logging/migrations/0001_initial.py` создаёт таблицу `audit_changelog`.
- **Данные**: при параллельной работе сервис может писать в обе таблицы, что ведёт к расхождениям.

### Задачи
1. **Переиспользование модели**  
   - Обновить импорты (`collection_manager.utils`, `collection_manager.admin`, `collection_manager.tests`, `strain_tracker_project.admin`) на `audit_logging.models.ChangeLog`.  
   - Исключить экспорт/переиспользование модели из `collection_manager`.

2. **Миграция данных**  
   - Создать миграцию (в `collection_manager` или `audit_logging`) для копирования данных из `changelog` в `audit_changelog`, если таблица существует и содержит строки.  
   - Обеспечить идемпотентность (не дублировать записи при повторном прогоне).

3. **Удаление дубликата**  
   - После миграции удалить модель `ChangeLog` из `collection_manager` и зарегистрировать в админке модель из `audit_logging`.  
   - Добавить миграцию для удаления таблицы `changelog` (или оставить пустой, если требуется ручное удаление на проде, но тогда зафиксировать инструкцию).

4. **Регрессия и тесты**  
   - Обновить тесты, чтобы они использовали единственный источник модели.  
   - Прогнать проверки миграций (`makemigrations --check`, `migrate --plan`) и ручной smoke-тест вызова `log_change`.

### План внедрения
1. Добавить миграцию переноса данных (упорядочить: зависимость от `audit_logging`).
2. Переключить импорты и удалить дубликат модели.
3. Провести очистку (drop таблицы или документированный manual step).
4. Запустить тесты и задокументировать шаги развёртывания (резервные копии перед миграцией, порядок применения).

### Текущее выполнение
- ✅ Миграция `0016_remove_legacy_models` фиксирует, что дублирующие таблицы более не используются, без физических удалений.
- ✅ Миграция `0017_remove_sample_amylase_variant_delete_appendixnote_and_more` безопасно очищает старые `collection_manager_*` таблицы на чистых окружениях.
- ✅ Миграция `0018_move_changelog_to_audit` переносит записи из `changelog` в `audit_changelog` и синхронизирует sequence.
- ✅ Миграция `0019_cleanup_legacy_changelog` удаляет пустую таблицу `changelog` (если в ней нет данных).
- ✅ Все импорты внутри `collection_manager` и админки переключены на `audit_logging.ChangeLog`.
