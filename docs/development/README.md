# 👨‍💻 Документация для разработчиков

Документация для разработчиков, работающих с проектом.

## 📁 Содержимое

- **[DEVELOPER_GUIDE.md](../../DEVELOPER_GUIDE.md)** - Основное руководство для разработчиков
- **[MCP_CONTEXT.md](../../MCP_CONTEXT.md)** - Контекст для Model Context Protocol
- **[IMPLEMENTATION_CONTEXT.md](../../IMPLEMENTATION_CONTEXT.md)** - Контекст текущей реализации
- **[VALIDATION_README.md](../../VALIDATION_README.md)** - Система валидации данных

## 🚀 Быстрый старт для разработчиков

### 1. Настройка окружения
```bash
# Клонирование репозитория
git clone <repository-url>
cd strain_collection_new

# Настройка переменных окружения
cp config/env_example .env

# Запуск в режиме разработки
cd deployment
make dev
```

### 2. Структура проекта
- **Backend**: Django REST API с модульной архитектурой
- **Frontend**: React + TypeScript + Tailwind CSS
- **Database**: PostgreSQL
- **Deployment**: Docker + Docker Compose

### 3. Основные команды разработки
```bash
# Backend
cd backend
python manage.py runserver
python manage.py migrate
python manage.py test

# Frontend
cd frontend
npm install
npm run dev
npm run build
```

## 🔧 Инструменты разработки

- **Линтеры**: flake8 (Python), ESLint (TypeScript)
- **Форматирование**: Black (Python), Prettier (TypeScript)
- **Тестирование**: Django Test Framework, Jest
- **API**: Django REST Framework + Pydantic

## 📊 Текущий статус

**Stage 1**: 95% завершено
- ✅ Модульная архитектура
- ✅ API с валидацией
- 🔄 Frontend интеграция

## 🔗 Полезные ссылки

- API документация: `../api/`
- Архитектура: `../architecture/`
- Развертывание: `../deployment/`