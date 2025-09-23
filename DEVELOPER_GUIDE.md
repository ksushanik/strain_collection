# Developer Guide - Strain Collection Project

## 🚀 Быстрый старт

### Запуск проекта
```bash
# Клонирование и настройка
git clone <repository>
cd strain_collection_new

# Запуск среды разработки
make dev-setup    # Настройка PostgreSQL + pgAdmin
make dev-start    # Запуск Django (8000) + React (3000)

# Проверка состояния
make dev-status
```

### Доступ к приложению
- **Frontend**: http://localhost:3000/
- **Backend API**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs/
- **pgAdmin**: http://localhost:5050/ (admin@admin.com / admin)

## 📁 Структура проекта

### Backend (Django)
```
backend/
├── strain_tracker_project/     # Основной проект
├── reference_data/            # 📚 Справочные данные
├── strain_management/         # 🧬 Управление штаммами  
├── sample_management/         # 🧪 Управление образцами
├── storage_management/        # 📦 Управление хранилищем
├── audit_logging/            # 📋 Аудит и логирование
└── collection_manager/       # ⚠️ Legacy (выводится)
```

### API Endpoints
- `/api/reference/` - справочные данные (источники, местоположения, среды)
- `/api/strains/` - штаммы микроорганизмов
- `/api/samples/` - образцы коллекции
- `/api/storage/` - хранилище и боксы
- `/api/audit/` - логи изменений

## 🔧 Ключевые команды

### Разработка
```bash
make dev-migrate     # Применить миграции
make dev-test        # Запустить тесты
make dev-shell       # Django shell
make dev-logs        # Просмотр логов
```

### База данных
```bash
make backup-create   # Создать backup
make backup-restore  # Восстановить backup
make dev-reset-db    # Сброс БД (осторожно!)
```

## 📋 Текущий статус (Stage 1 - 95% завершен)

### ✅ Готово
- Модульная архитектура (5 приложений)
- Полные CRUD API с Pydantic валидацией
- Миграции базы данных
- URL маршрутизация
- Основное тестирование

### 🔄 В работе
- Интеграция frontend с новыми API
- Обновление документации
- Миграция тестов

### ⏳ Планируется
- Django Admin интерфейсы
- Очистка legacy кода
- Stage 2: Микросервисы

## 🎯 Важные файлы для изучения

### Планирование
- `STAGE1_IMPLEMENTATION_PLAN.md` - план реализации
- `IMPLEMENTATION_CONTEXT.md` - детальный контекст
- `MCP_CONTEXT.md` - контекст для MCP
- `memory-bank/progress.md` - общий прогресс

### Конфигурация
- `backend/strain_tracker_project/settings.py` - настройки Django
- `backend/strain_tracker_project/urls.py` - основные маршруты
- `docker-compose.dev.yml` - среда разработки

### Модели и API
- `backend/*/models.py` - модели данных
- `backend/*/api.py` - API endpoints
- `backend/*/urls.py` - маршруты приложений

## 🔍 Полезные советы

### Отладка
```bash
# Проверка состояния Django
python manage.py check

# Просмотр миграций
python manage.py showmigrations

# Создание суперпользователя
python manage.py createsuperuser
```

### Тестирование API
```bash
# Через curl
curl http://localhost:8000/api/strains/

# Через браузер
http://localhost:8000/docs/  # Swagger UI
```

### Работа с данными
- **Продакшн данные**: 881 штамм, 1,796 образцов
- **Импорт CSV**: `python manage.py import_csv_data`
- **Backup**: автоматический через cron

## ⚠️ Важные замечания

1. **Legacy код**: `collection_manager` постепенно выводится
2. **Миграции**: всегда тестируйте на копии данных
3. **API совместимость**: старые endpoints сохранены
4. **Безопасность**: не коммитьте секреты в .env файлы

## 🔗 Ресурсы

- **Продакшн**: https://culturedb.elcity.ru/
- **Django Docs**: https://docs.djangoproject.com/
- **React Docs**: https://react.dev/
- **Pydantic**: https://docs.pydantic.dev/

## 📞 Поддержка

При возникновении вопросов:
1. Изучите документацию в `memory-bank/`
2. Проверьте логи через `make dev-logs`
3. Используйте `MCP_CONTEXT.md` для понимания архитектуры