# MCP Context Configuration для Strain Collection Project

## Общая информация о проекте
- **Название**: Strain Collection Management System
- **Тип**: Django + React веб-приложение для управления коллекцией микроорганизмов
- **Статус**: Активная разработка, Stage 1 модульной рефакторизации завершен
- **Основной язык**: Python (Django), JavaScript (React)

## Архитектура проекта

### Backend (Django)
```
backend/
├── strain_tracker_project/     # Основной проект Django
├── collection_manager/         # Legacy приложение (постепенно выводится)
├── reference_data/            # Справочные данные (источники, местоположения)
├── strain_management/         # Управление штаммами
├── sample_management/         # Управление образцами
├── storage_management/        # Управление хранилищем
└── audit_logging/            # Аудит и логирование
```

### Frontend (React)
```
frontend/
├── src/
│   ├── components/           # React компоненты
│   ├── pages/               # Страницы приложения
│   ├── services/            # API сервисы
│   └── utils/               # Утилиты
```

## Текущий статус разработки

### ✅ Завершено (Stage 1)
1. **Модульная архитектура**: Создано 5 новых Django приложений
2. **Миграция моделей**: Все модели перенесены из collection_manager
3. **API endpoints**: Полные CRUD API с Pydantic валидацией
4. **База данных**: Миграции выполнены без потери данных
5. **URL маршрутизация**: Настроена для всех новых приложений

### 🔄 В процессе
1. **Тестирование API**: Проверка новых endpoints
2. **Обновление frontend**: Интеграция с новыми API
3. **Миграция тестов**: Адаптация под новую структуру

### 📋 Запланировано
1. **Django Admin**: Создание интерфейсов для новых приложений
2. **Документация**: Обновление API документации
3. **Очистка legacy кода**: Удаление устаревшего кода
4. **Stage 2**: Микросервисная архитектура

## Ключевые файлы для контекста

### Планы и документация
- `STAGE1_IMPLEMENTATION_PLAN.md` - План реализации Stage 1
- `IMPLEMENTATION_CONTEXT.md` - Детальный контекст реализации
- `memory-bank/progress.md` - Общий прогресс проекта

### Конфигурация
- `backend/strain_tracker_project/settings.py` - Настройки Django
- `backend/strain_tracker_project/urls.py` - Основные URL маршруты
- `docker-compose.yml` - Конфигурация Docker для продакшн
- `docker-compose.dev.yml` - Конфигурация для разработки

### Модели данных
- `backend/reference_data/models.py` - Справочные данные
- `backend/strain_management/models.py` - Модель штаммов
- `backend/sample_management/models.py` - Модели образцов
- `backend/storage_management/models.py` - Модели хранилища
- `backend/audit_logging/models.py` - Модели аудита

### API endpoints
- `backend/*/api.py` - API views для каждого приложения
- `backend/*/urls.py` - URL маршруты для каждого приложения

## Команды для быстрого старта

### Разработка
```bash
# Запуск среды разработки
make dev-setup
make dev-start

# Тестирование
make dev-test
make dev-migrate

# Проверка состояния
make dev-status
```

### Продакшн
```bash
# Развертывание
make deploy
make backup-create
```

## Важные соглашения

### Именование
- Модели: CamelCase (например, `StrainModel`)
- API endpoints: snake_case (например, `/api/strains/`)
- Файлы: snake_case (например, `strain_management`)

### Структура API
- Все API используют Pydantic схемы для валидации
- CRUD операции: list, create, retrieve, update, delete
- Дополнительные endpoints: validate, search, stats

### База данных
- PostgreSQL в продакшн
- SQLite для разработки (опционально)
- Миграции Django для изменений схемы

## Контакты и ресурсы
- **Продакшн сервер**: https://culturedb.elcity.ru/
- **Локальная разработка**: http://localhost:3000/ (React), http://localhost:8000/ (Django)
- **База данных**: PostgreSQL с полными данными коллекции

## Следующие этапы развития

### Stage 2: Микросервисы
- Разделение на независимые сервисы
- Event-driven архитектура
- API Gateway

### Stage 3: Оптимизация
- Кэширование
- Индексы базы данных
- Производительность

Этот файл должен обновляться при каждом значительном изменении в проекте для поддержания актуального контекста разработки.