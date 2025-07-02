# 🧬 Система учета штаммов микроорганизмов

Современное веб-приложение для управления коллекцией штаммов микроорганизмов с расширенными возможностями поиска, массовых операций и аналитики.

## 🚀 Быстрое развертывание

### Автоматическое развертывание одной командой:
```bash
git clone <repository-url> strain-collection
cd strain-collection
make quick-deploy
```

### Система будет доступна на:
- 🌐 **Веб-интерфейс**: http://localhost
- 🔧 **Админ-панель**: http://localhost/admin/ (admin/admin123)
- 📡 **API документация**: http://localhost/api/
- 💻 **Frontend (режим разработки)**: http://localhost:5173/

> 📖 **Подробное руководство**: [DEPLOYMENT_README.md](DEPLOYMENT_README.md)

## ⚡ Разработка

### Быстрый старт для разработки:
```bash
# Настройка среды разработки (только БД в Docker)
make dev-setup

# Запуск PostgreSQL
make dev-start

# В отдельных терминалах:
make dev-backend   # Django (localhost:8000)
make dev-frontend  # React (localhost:5173)
```

**Преимущества режима разработки:**
- ✅ Быстрая итерация (hot reload)
- ✅ Только PostgreSQL в Docker
- ✅ Django и React локально
- ✅ Полный доступ к отладке

> 📖 **Подробное руководство**: [DEV_QUICK_START.md](DEV_QUICK_START.md)

## 🎯 Описание проекта

Веб-приложение для учета коллекции штаммов микроорганизмов с возможностями:
- ✅ Управление штаммами и образцами (881 штамм, 1796 образцов)
- 📦 Отслеживание местоположения в хранилище (1793 ячейки)
- 🔍 Расширенный поиск и фильтрация (Advanced Filters) с И/ИЛИ группами, boolean и диапазонами дат
- 📋 Массовые операции (экспорт, обновление, удаление) с выбранными записями
- 📊 Аналитика и статистика коллекции
- 💾 Экспорт данных в CSV, JSON, Excel
- 🗄️ Автоматическое резервное копирование
- 🔐 Административная панель Django
- 📡 REST API для интеграции

## 🏗️ Структура проекта

```
strain_collection_new/
├── backend/                    # Django бэкенд
│   ├── strain_tracker_project/ # Главный проект Django
│   ├── collection_manager/     # Приложение для управления коллекцией
│   ├── requirements.txt        # Python зависимости
│   ├── .env                   # Переменные окружения
│   └── manage.py              # Django management
├── frontend/                   # React + Vite фронтенд (TypeScript)
├── deployment/                 # Docker конфигурации
│   └── docker-compose.yml     # PostgreSQL контейнер
├── data/                       # CSV файлы с данными
├── scripts/                    # Скрипты импорта и обработки
└── Makefile                    # Команды автоматизации
```

## 🚀 Быстрый старт

### 🐳 Docker Hub развертывание (РЕКОМЕНДУЕТСЯ)
```bash
# Создание ультра-минимального пакета (50KB)
make create-ultra-minimal

# Копирование на сервер и развертывание
scp strain_ultra_minimal.tar.gz user@server:
ssh user@server
tar -xzf strain_ultra_minimal.tar.gz
cd strain_ultra_minimal/
./deploy_hub.sh
```

### 📦 Локальное Docker развертывание
```bash
# Полная автоматизация - одна команда
make quick-deploy
```

### 💻 Режим разработки
```bash
# Настройка окружения разработки
make dev-setup

# Запуск в отдельных терминалах
make dev-backend    # Django на :8000
make dev-frontend   # React (localhost:5173)
```

### 🔧 Ручная установка
```bash
# 1. Настройка проекта
make setup

# 2. Запуск базы данных
make db-start

# 3. Применение миграций
make migrate

# 4. Импорт данных
make import

# 5. Создание суперпользователя (опционально)
make admin

# 6. Запуск сервера
make dev
```

## 🛠️ Основные команды

| Команда | Описание |
|---------|----------|
| `make help` | Показать все доступные команды |
| `make setup` | Настройка виртуальной среды и зависимостей |
| `make db-start` | Запуск PostgreSQL в Docker |
| `make dev` | Запуск Django сервера разработки |
| `make import` | Импорт данных из CSV файлов |
| `make status` | Проверка статуса системы |
| `make test-api` | Тестирование API endpoints |
| `make test-search` | Тестирование расширенного поиска |
| `make test-bulk` | Тестирование массовых операций |
| `make test-analytics` | Тестирование аналитики |
| `make test-all-new` | Тестирование всех новых функций |
| `make migrate-changelog` | Применение миграции системы версионирования |
| `make clean-db` | Очистка базы данных |

## 🗄️ База данных

### Основные таблицы:
- **Strains**: Штаммы микроорганизмов (881 записей)
- **Samples**: Образцы штаммов (1796 записей) 
- **Storage**: Информация о хранении (1793 ячейки)

### Справочники:
- **Locations**: Местоположения (16 записей)
- **Sources**: Источники образцов (100 записей)
- **IndexLetters**: Индексные буквы (10 записей)
- **Comments**: Комментарии (3 записи)
- **AppendixNotes**: Примечания (3 записи)

## 📊 Статистика данных

- **Всего штаммов**: 881
- **Всего образцов**: 1796
- **Занятые ячейки**: 1750
- **Свободные ячейки**: 45
- **Боксы**: 5 (боксы 1-5)
- **Ячейки в боксе**: A1-I9 (81 ячейка на бокс)

## 🔍 Система поиска и фильтрации

### Полнотекстовый поиск
Система поддерживает расширенный поиск по всем полям:

**Поиск штаммов:**
- По коду штамма (`short_code`)
- По идентификатору (`identifier`)
- По таксономии (`rrna_taxonomy`)
- По ID коллекции RCAM

**Поиск образцов:**
- По всем полям штамма
- По источникам (название организма, тип источника)
- По локациям (название места)
- По ячейкам хранения (бокс, ячейка)

### API endpoints для поиска
```bash
# Поиск штаммов
GET /api/strains/?search=Streptomyces&limit=10

# Поиск образцов по тексту
GET /api/samples/?search=A1&limit=10

# Фильтрация по источнику
GET /api/samples/?source_type=Sponge

# Фильтрация по локации
GET /api/samples/?search=Baikal

# Комбинированные фильтры
GET /api/samples/?has_photo=true&is_identified=true&limit=50
```

### Тестирование поиска
```bash
make test-search
```

## 📋 Массовые операции

Система поддерживает эффективные массовые операции для управления большими объемами данных:

### Массовое редактирование образцов
```bash
# API endpoint для массового обновления
POST /api/samples/bulk-update/
{
  "sample_ids": [1, 2, 3],
  "update_data": {
    "has_photo": true,
    "is_identified": true
  }
}
```

### Массовое удаление
```bash
# Массовое удаление образцов
POST /api/samples/bulk-delete/
{
  "sample_ids": [1, 2, 3]
}

# Массовое удаление штаммов (с проверкой связей)
POST /api/strains/bulk-delete/
{
  "strain_ids": [1, 2],
  "force_delete": false
}
```

### Экспорт данных
```bash
# Экспорт выбранных образцов в CSV
GET /api/samples/export/?sample_ids=1,2,3,4,5

# Экспорт с фильтрацией
GET /api/samples/export/?source_type=Sponge&has_photo=true
```

### Тестирование массовых операций
```bash
make test-bulk
```

## 📊 Аналитика и отчеты

Система предоставляет расширенную аналитику для мониторинга коллекции:

### Основные метрики
- **Общая статистика**: количество штаммов, образцов, ячеек хранения
- **Заполненность хранилища**: процент занятых ячеек
- **Распределение по источникам**: графики по типам организмов
- **Временные тренды**: создание образцов по месяцам

### Аналитические графики
- Распределение по типам источников (диаграмма)
- Топ 10 штаммов по количеству образцов
- Характеристики образцов (фото, идентификация, геном и т.д.)
- Использование хранилища

### Доступ к аналитике
- **Web интерфейс**: http://localhost:5173/analytics
- **API статистики**: http://localhost:8000/api/stats/

### Тестирование аналитики
```bash
make test-analytics
```

## 🔄 Система версионирования

Система автоматически отслеживает все изменения для обеспечения прозрачности и возможности аудита:

### Функции отслеживания
- **Журнал изменений**: все создания, обновления и удаления
- **Версионирование данных**: старые и новые значения полей
- **Идентификация пользователя**: IP адрес, User Agent
- **Массовые операции**: группировка связанных изменений
- **Метаданные**: временные метки, комментарии

### Типы отслеживаемых действий
- `CREATE` - Создание записи
- `UPDATE` - Обновление записи  
- `DELETE` - Удаление записи
- `BULK_UPDATE` - Массовое обновление
- `BULK_DELETE` - Массовое удаление

### Доступ к журналу изменений
- **Админ панель**: http://localhost:8000/admin/collection_manager/changelog/
- **Фильтрация**: по типу действия, объекту, дате
- **Только чтение**: изменения нельзя редактировать

### Применение миграции
```bash
make migrate-changelog
```

## 🌐 Доступ к системе

После запуска сервера доступны следующие URL:

- **Административная панель**: http://localhost:8000/admin/
- **API**: http://localhost:8000/api/
- **Frontend (React)**: http://localhost:5173/ (в режиме разработки)
- **Главная страница**: http://localhost:8000/

### Данные для входа в админку:
- **Логин**: admin
- **Пароль**: admin (или созданный через `make admin`)

## 🔧 Технологии

- **Backend**: Django 4.2 + Django REST Framework
- **Database**: PostgreSQL 14 в Docker
- **Frontend**: React + TypeScript (планируется)
- **Deployment**: Docker + Docker Compose
- **Automation**: Makefile

## 💾 Система backup и восстановления

### Создание backup'ов
```bash
# Полный backup с данными
make backup-create

# Backup только схемы БД
make backup-schema

# Список всех backup'ов
make backup-list
```

### Восстановление из backup'а
```bash
# Восстановление с защитным backup'ом текущей БД
make restore-db

# Информация о backup файле
make restore-info
```

### Автоматические backup'ы
```bash
# Установка ежедневных backup'ов
make backup-auto-install

# Просмотр настроек cron
make backup-auto-show

# Удаление автоматических backup'ов
make backup-auto-remove
```

### Управление backup'ами
```bash
# Очистка старых backup'ов (>30 дней)
make backup-cleanup

# Валидация backup файла
make backup-validate

# Тестирование системы backup
make backup-test
```

**📂 Backup'ы сохраняются в директории `backups/` с автоматическим сжатием и метаданными.**

Подробную документацию по системе backup см. в [`backups/README.md`](backups/README.md).

## 📁 Важные файлы

- `backend/collection_manager/models.py` - Модели данных
- `backend/collection_manager/admin.py` - Настройки админки
- `scripts/import_data.py` - Скрипт импорта CSV данных
- `scripts/backup_database.py` - Система backup БД
- `scripts/restore_database.py` - Система восстановления БД
- `deployment/docker-compose.yml` - Конфигурация PostgreSQL
- `Makefile` - Команды автоматизации

## 🐞 Решение проблем

### PostgreSQL не запускается
```bash
make db-stop
make db-start
```

### Ошибки миграций
```bash
make clean-db
make migrate
make import
```

### Восстановление после сбоя
```bash
# Создать backup текущего состояния
make backup-create

# Восстановить из последнего работающего backup'а
make restore-db

# Проверить статус
make status
```

### Проверка статуса
```bash
make status
``` 