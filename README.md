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
- 🔧 **Админ-панель**: http://localhost/admin/ (логин: admin, пароль: admin123)
- 📡 **API документация**: http://localhost/docs/
- 💻 **Frontend (режим разработки)**: http://localhost:3000/

> 📖 **Подробное руководство**: [DEPLOYMENT_README.md](DEPLOYMENT_README.md)

## ⚡ Разработка

### Быстрый старт для разработки:
```bash
# Переходим в папку deployment для выполнения команд
cd deployment

# Настройка среды разработки (только БД в Docker)
make dev-setup

# Запуск PostgreSQL
make dev-start

# В отдельных терминалах:
make dev-backend   # Django (localhost:8000)
make dev-frontend  # React (localhost:3000)
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
├── config/                     # Конфигурационные файлы
│   ├── .flake8               # Конфигурация линтера
│   ├── .hadolint.yaml        # Конфигурация Docker линтера
│   ├── deploy.config         # Конфигурация деплоя
│   └── env_example           # Пример переменных окружения
├── deployment/                 # Docker конфигурации и развертывание
│   ├── docker-compose.yml    # Продакшн конфигурация
│   ├── docker-compose.dev.yml # Конфигурация для разработки
│   └── Makefile              # Команды автоматизации
├── docs/                       # Организованная документация
│   ├── architecture/         # Архитектурная документация
│   ├── development/          # Документация для разработчиков
│   └── deployment/           # Документация по развертыванию
├── data/                       # CSV файлы с данными
└── scripts/                    # Скрипты импорта и обработки
```

## 🚀 Быстрый старт

### 🚀 Ручной деплой (GitHub Actions)
- Ручной запуск: вкладка `Actions` → `Deploy to Production` → `Run workflow`.
- Запуск из CLI: `cd deployment && make deploy-gh` (требуется установленный `gh` и авторизация: `gh auth login`).
- Подробности и список секретов: `README_DEPLOY.md`.

### 📡 Статус и логи деплоя (GitHub CLI)
- Проверить статус последнего запуска: `cd deployment && make deploy-gh-status`
- Показать логи последнего запуска: `cd deployment && make deploy-gh-logs`
- Стримить логи до завершения: `cd deployment && make deploy-gh-watch`

#### ℹ️ Примечание об авторизации gh/GH_TOKEN
- Команды `make deploy-gh*` используют либо локальную авторизацию `gh`, либо токен из переменной окружения `GH_TOKEN` (если установлен).
- Для `GH_TOKEN` нужны права `repo` и `workflow`. Установите токен в окружение: `set GH_TOKEN=YOUR_TOKEN` (PowerShell) или `export GH_TOKEN=YOUR_TOKEN` (bash).
- Если `GH_TOKEN` не задан, выполните `gh auth login` и авторизуйтесь в `GitHub.com` через HTTPS.

##### Файл `.github/gh.env` (автозагрузка токена)
- Makefile автоматически пытается загрузить токен из файла `.github/gh.env` (ключ `GH_TOKEN=...`).
- Путь загрузки: из директории `deployment` берётся `../.github/gh.env`.
- При отсутствии локальной авторизации `gh` Makefile выполнит неинтерактивный вход с этим токеном.
- Формат файла:
  - Строка `GH_TOKEN=ghp_XXXXXXXX...` без кавычек.
  - Храните файл локально, не коммитьте его в репозиторий.

### 📦 Локальный продакшн (Docker)
```bash
cd deployment
make deploy          # build + up локально
# при проблемах с bake используйте
make deploy-no-bake  # сборка без BuildKit/Bake
```

### 💻 Локальная разработка
```bash
cd deployment

# Запуск всех сервисов (Postgres + backend + frontend)
make up

# Отключение всех сервисов
make down

# Отдельно: запустить backend или frontend
make backend-up
make frontend-up
```

### 🧪 Продакшн-команды (через SSH)
```bash
cd deployment
make status-prod     # статус сервисов на проде
make logs-prod       # логи (например: make logs-prod backend 50)
make migrate-prod    # применить миграции БД на проде
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
- **Web интерфейс**: http://localhost:3000/analytics
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
- **Frontend (React)**: http://localhost:3000/ (в режиме разработки)
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
- `deployment/Makefile` - Команды автоматизации

## 🔐 Администрирование

### Доступ к админ-панели
После развертывания системы автоматически создается администратор:
- **URL**: http://localhost/admin/
- **Логин**: admin
- **Пароль**: admin123

### Управление пользователями
```bash
# Создание нового суперпользователя
docker compose exec backend python manage.py createsuperuser

# Изменение пароля существующего пользователя
docker compose exec backend python manage.py changepassword admin

# Создание пользователя через Django shell
docker compose exec backend python manage.py shell -c "
from django.contrib.auth.models import User
User.objects.create_superuser('newadmin', 'admin@example.com', 'newpassword')
"
```

### Административные функции
В админ-панели доступны:
- ✅ Управление штаммами и образцами
- ✅ Управление пользователями и правами доступа
- ✅ Просмотр логов аудита
- ✅ Управление справочными данными
- ✅ Массовые операции с данными
- ✅ Экспорт/импорт данных

### Мониторинг системы
```bash
# Проверка статуса всех сервисов
docker compose ps

# Просмотр логов
docker compose logs backend
docker compose logs frontend
docker compose logs db

# Мониторинг ресурсов
docker stats
```

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