# 📚 Документация проекта

Организованная структура документации системы учета штаммов микроорганизмов.

## 📁 Структура документации

### 🏗️ Архитектура и планирование
- **[architecture/](architecture/)** - Архитектурная документация
  - [ARCHITECTURE_PLAN.md](../ARCHITECTURE_PLAN.md) - Стратегический план перехода к микросервисам
  - [DOMAIN_DEPENDENCY_MAP.md](../DOMAIN_DEPENDENCY_MAP.md) - Карта зависимостей между доменами
  - [STAGE1_IMPLEMENTATION_PLAN.md](../STAGE1_IMPLEMENTATION_PLAN.md) - План реализации Stage 1

### 👨‍💻 Разработка
- **[development/](development/)** - Документация для разработчиков
  - [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) - Руководство для разработчиков
  - [MCP_CONTEXT.md](../MCP_CONTEXT.md) - Контекст для Model Context Protocol
  - [IMPLEMENTATION_CONTEXT.md](../IMPLEMENTATION_CONTEXT.md) - Контекст текущей реализации
  - [VALIDATION_README.md](../VALIDATION_README.md) - Система валидации данных

### 🚀 Развертывание
- **[deployment/](deployment/)** - Документация по развертыванию
  - [DEPLOYMENT_README.md](../DEPLOYMENT_README.md) - Руководство по развертыванию
  - [README_DEPLOY.md](../README_DEPLOY.md) - Автоматизированная система деплоя
  - [BACKUP_QUICK_START.md](../BACKUP_QUICK_START.md) - Система резервного копирования

### 🚀 Быстрый старт (в корне проекта)
- **[README.md](../README.md)** - Основная документация проекта
- **[QUICK_START.md](../QUICK_START.md)** - Быстрый старт для пользователей

### 🔧 Специализированная документация
- **[API_BOXES_DOCUMENTATION.md](../backend/API_BOXES_DOCUMENTATION.md)** - Актуальные REST‑ручки `/api/storage/...`, примеры ответов, заголовки депрекации
- **Storage toolkit**
  - [storage_service_guidelines.md](storage_service_guidelines.md) — рекомендации по работе с сервисным слоем, транзакциями и логированием
  - Скрипт аудита: `python backend/scripts/audit_storage_state.py`
  - Команда проверки целостности: `python manage.py ensure_storage_consistency --dry-run`

### 📊 Прогресс и память проекта
- **[memory-bank/](../memory-bank/)** - Банк памяти проекта с контекстом и прогрессом

## 🎯 Текущий статус проекта

**Stage 1 (Модульная рефакторизация): 95% завершено**

### ✅ Завершено:
- Модульная архитектура (5 новых Django приложений)
- Миграция моделей из collection_manager
- API endpoints с Pydantic валидацией
- Миграции базы данных
- URL маршрутизация
- Тестирование API endpoints
- Контекст разработки (MCP)

### 🔄 В процессе:
- Frontend интеграция с новыми API
- Миграция тестов
- Django Admin интерфейсы
- Обновление документации API

### 📋 Следующие шаги:
- Завершение Stage 1
- Переход к Stage 2 (проектирование сервисных границ)
- Подготовка к микросервисной архитектуре

## 🔗 Полезные ссылки

- **Проект**: Система учета штаммов микроорганизмов
- **Архитектура**: Django + React + PostgreSQL
- **Развертывание**: Docker + Docker Compose
- **API**: REST с Pydantic валидацией
- **База данных**: PostgreSQL с миграциями Django

---

*Последнее обновление: Январь 2025*
