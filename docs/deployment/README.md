# 🚀 Документация по развертыванию

Документация по развертыванию системы в различных окружениях.

## 📁 Содержимое

- **[README_DEPLOY.md](../../README_DEPLOY.md)** - Автоматизированная система деплоя
- **[BACKUP_QUICK_START.md](../../BACKUP_QUICK_START.md)** - Система резервного копирования
 - **[deployment/README.md](../../deployment/README.md)** - Локальное развертывание и конфигурация Docker

## 🎯 Типы развертывания

### 🔧 Разработка (Development)
```bash
cd deployment
make dev
```
- Горячая перезагрузка
- Отладочные инструменты
- Локальная база данных

### 🧪 Тестирование (Staging)
```bash
cd deployment
make staging
```
- Копия продакшн окружения
- Тестовые данные
- Мониторинг

### 🌐 Продакшн (Production)
```bash
cd deployment
make deploy
```
- Оптимизированная сборка
- SSL сертификаты
- Резервное копирование
- Мониторинг и логирование

Также доступен авто-деплой через GitHub Actions при push в ветку `main` или ручном запуске. Подробности см. в `README_DEPLOY.md`.

## 🐳 Docker конфигурация

### Основные сервисы
- **backend**: Django API сервер
- **frontend**: React приложение с Nginx
- **db**: PostgreSQL база данных
- **redis**: Кэширование и сессии

### Файлы конфигурации
- `deployment/docker-compose.yml` - Продакшн
- `deployment/docker-compose.dev.yml` - Разработка
- `backend/Dockerfile` - Backend образ
- `frontend/Dockerfile` - Frontend образ

## 🔧 Переменные окружения

Основные переменные (см. `config/env_example`):
- `DATABASE_URL` - Подключение к БД
- `SECRET_KEY` - Django секретный ключ
- `DEBUG` - Режим отладки
- `ALLOWED_HOSTS` - Разрешенные хосты

## 📊 Мониторинг

### Проверка статуса
```bash
# Статус сервисов
make status

# Логи
make logs

# Здоровье системы
make health-check
```

### Резервное копирование
```bash
# Создание бэкапа
make backup

# Восстановление
make restore BACKUP_FILE=backup_name.sql
```

## 🔗 Связанные файлы

- Конфигурация: `../../config/`
- Файлы развертывания: `../../deployment/`
- Скрипты: `../../scripts/`