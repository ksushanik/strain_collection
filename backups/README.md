# Система backup базы данных

Эта директория содержит backup'ы PostgreSQL базы данных системы учета штаммов.

## Структура файлов

```
backups/
├── strain_collection_full_YYYYMMDD_HHMMSS.sql.gz     # Полные backup'ы (сжатые)
├── strain_collection_schema_YYYYMMDD_HHMMSS.sql.gz   # Backup схемы
├── strain_collection_pre_restore_YYYYMMDD_HHMMSS.sql.gz  # Pre-restore backup'ы
├── *.json                                             # Метаданные backup'ов
├── backup.log                                         # Лог операций backup
├── restore.log                                        # Лог операций восстановления
└── cron.log                                          # Лог автоматических backup'ов
```

## Команды управления

### Создание backup'ов
```bash
# Полный backup с данными
make backup-create

# Только схема БД
make backup-schema

# Прямой вызов скрипта
python scripts/backup_database.py create --type full
python scripts/backup_database.py create --type schema --no-compress
```

### Просмотр backup'ов
```bash
# Список всех backup'ов
make backup-list

# Информация о конкретном backup'е
make restore-info
# или
python scripts/restore_database.py backup_file.sql.gz --info-only
```

### Восстановление
```bash
# Восстановление с созданием backup'а текущей БД
make restore-db

# Восстановление без создания backup'а
python scripts/restore_database.py backup_file.sql.gz --no-backup

# Восстановление с полной заменой таблиц
python scripts/restore_database.py backup_file.sql.gz --drop-existing
```

### Автоматические backup'ы
```bash
# Установка ежедневных backup'ов
make backup-auto-install

# Установка еженедельных backup'ов
python scripts/setup_backup_cron.py install --schedule weekly

# Просмотр текущих настроек
make backup-auto-show

# Удаление автоматических backup'ов
make backup-auto-remove
```

### Очистка и валидация
```bash
# Очистка старых backup'ов
make backup-cleanup

# Валидация backup файла
make backup-validate

# Тестирование системы
make backup-test
```

## Типы backup'ов

### 1. Полный backup (full)
- Содержит схему и все данные
- Размер: ~10-50 MB (в зависимости от количества данных)
- Время создания: 10-60 секунд
- Использование: полное восстановление системы

### 2. Backup схемы (schema)
- Только структура таблиц, индексы, ключи
- Размер: ~100-500 KB
- Время создания: 5-10 секунд  
- Использование: восстановление структуры БД

### 3. Pre-restore backup
- Автоматически создается перед восстановлением
- Защищает от потери текущих данных
- Именование: `strain_collection_pre_restore_TIMESTAMP_`

## Расписания автоматических backup'ов

### Daily (ежедневно)
- 02:00 - полный backup
- 03:00 воскресенье - очистка старых backup'ов (>30 дней)

### Weekly (еженедельно)  
- 02:00 понедельник - полный backup
- 23:00 вторник-воскресенье - backup схемы
- 03:00 первое воскресенье месяца - очистка (>60 дней)

### Monthly (ежемесячно)
- 02:00 первое число - полный backup
- 02:00 воскресенье - backup схемы
- 03:00 квартально - очистка (>90 дней)

## Метаданные backup'ов

Каждый backup сопровождается JSON файлом с метаданными:

```json
{
  "backup_file": "strain_collection_full_20250620_140000.sql.gz",
  "backup_type": "full",
  "creation_time": "2025-06-20T14:00:00",
  "database_stats": {
    "timestamp": "2025-06-20T14:00:00",
    "database": "strain_tracker",
    "tables_count": 25,
    "database_size": "45 MB",
    "records": {
      "collection_manager_strain": 881,
      "collection_manager_sample": 1796,
      "collection_manager_storage": 1793
    }
  },
  "file_size": 8945612,
  "compressed": true
}
```

## Безопасность

### Защита данных
- Backup'ы сжимаются для экономии места
- Создается pre-restore backup перед восстановлением
- Валидация backup'ов перед восстановлением
- Подтверждение опасных операций

### Ротация backup'ов
- Автоматическое удаление старых backup'ов
- Сохранение минимального количества backup'ов
- Настраиваемые периоды хранения

## Восстановление в аварийных ситуациях

### 1. Полная потеря данных
```bash
# Остановить приложение
make db-stop

# Запустить чистую БД
make db-start

# Восстановить из последнего backup'а
make restore-db
# выбрать последний полный backup

# Применить миграции Django
make migrate

# Запустить приложение
make start
```

### 2. Частичное повреждение данных
```bash
# Создать backup поврежденной БД для анализа
make backup-create

# Восстановить из backup'а без удаления таблиц
python scripts/restore_database.py latest_backup.sql.gz

# Проверить целостность данных
make validate-data
```

### 3. Откат к предыдущему состоянию
```bash
# Просмотреть доступные backup'ы
make backup-list

# Восстановить нужный backup
make restore-db
# указать нужный backup файл
```

## Мониторинг

### Логи
- `backup.log` - все операции backup
- `restore.log` - все операции восстановления  
- `cron.log` - автоматические backup'ы

### Проверка работоспособности
```bash
# Тест создания backup'а
make backup-test

# Статус cron задач
crontab -l | grep strain_collection

# Последние backup'ы
make backup-list | head -5
``` 