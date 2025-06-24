# 🤖 Автоматизация деплоя strain-collection

Полная автоматизация процесса развертывания системы управления коллекцией штаммов.

## 🎯 Возможности

- ✅ **Полностью автоматический деплой** - одна команда для полного цикла
- ✅ **Проверки перед деплоем** - требования, изменения, тесты
- ✅ **Безопасность** - резервные копии, откат в случае ошибок
- ✅ **Health checks** - проверка работоспособности после деплоя
- ✅ **Git integration** - автоматический деплой при коммитах
- ✅ **Гибкая настройка** - различные режимы и опции

## 🚀 Быстрый старт

### 1. Основная команда
```bash
make auto-deploy
```

### 2. Быстрый деплой (без тестов)
```bash
make auto-deploy-fast
```

### 3. Принудительный деплой
```bash
make auto-deploy-force
```

## 📋 Доступные команды

| Команда | Описание |
|---------|----------|
| `make auto-deploy` | Полный автоматический деплой с подтверждением |
| `make auto-deploy-force` | Принудительный деплой без подтверждений |
| `make auto-deploy-fast` | Быстрый деплой (пропуск тестов) |
| `make setup-git-hooks` | Настройка Git hooks для автодеплоя |
| `make remote-status` | Проверка статуса удаленного сервера |
| `make remote-logs` | Просмотр логов удаленного сервера |
| `make remote-restart` | Перезапуск сервисов на сервере |

## 🔧 Настройка

### Первоначальная настройка
```bash
# 1. Авторизация в Docker Hub
docker login --username gimmyhat

# 2. Настройка Git hooks (опционально)
make setup-git-hooks

# 3. Проверка настроек
make update-info
```

### Настройка автодеплоя через Git
```bash
# Включить автодеплой при коммитах в main/master
git config hooks.autodeploy true

# Отключить автодеплой
git config hooks.autodeploy false
```

## 🎮 Режимы работы

### 1. Интерактивный режим (по умолчанию)
- Запрашивает подтверждение перед деплоем
- Показывает предупреждения о незафиксированных изменениях
- Подходит для ручного деплоя

```bash
./scripts/auto_deploy.sh
```

### 2. Принудительный режим
- Без подтверждений и остановок
- Подходит для CI/CD и автоматизации

```bash
./scripts/auto_deploy.sh --force
```

### 3. Быстрый режим
- Пропускает тесты для ускорения
- Только для срочных обновлений

```bash
./scripts/auto_deploy.sh --force --skip-tests
```

## 🔍 Этапы автоматического деплоя

1. **Проверка требований**
   - Docker установлен и запущен
   - SSH доступ к серверу
   - Авторизация в Docker Hub
   - Существование директории на сервере

2. **Анализ изменений**
   - Статус Git репозитория
   - Незафиксированные изменения
   - Изменения в фронтенде

3. **Тестирование** (если не пропущено)
   - Сборка TypeScript
   - Линтинг кода
   - Юнит-тесты (при наличии)

4. **Сборка проекта**
   - Пересборка фронтенда
   - Сборка Docker образов

5. **Публикация**
   - Отправка образов на Docker Hub
   - Тегирование версии

6. **Деплой на сервер**
   - Создание резервной копии
   - Остановка старых сервисов
   - Загрузка новых образов
   - Запуск обновленной системы

7. **Проверка работоспособности**
   - Health checks контейнеров
   - Проверка HTTP доступности
   - Валидация API endpoints

## ⚙️ Конфигурация

Настройки находятся в файле `deploy.config`:

```bash
# Docker Hub
DOCKER_REGISTRY=gimmyhat
BACKEND_IMAGE=strain-collection-backend
FRONTEND_IMAGE=strain-collection-frontend

# Сервер
REMOTE_HOST=4feb
REMOTE_DIR=~/strain_ultra_minimal
REMOTE_URL=http://89.169.171.236:8081

# Параметры
HEALTH_CHECK_TIMEOUT=30
BACKUP_COUNT=5
```

## 🔒 Безопасность

### Резервные копии
- Автоматическое создание backup'а конфигурации
- Хранение последних 5 резервных копий
- Возможность быстрого отката

### Проверки безопасности
- Валидация SSH ключей
- Проверка прав доступа к серверу
- Контроль целостности образов

### Откат в случае ошибок
```bash
# Ручной откат к предыдущей версии
ssh 4feb "cd ~/strain_ultra_minimal && \
  docker compose down && \
  cp .env.backup.YYYYMMDD_HHMMSS .env && \
  docker compose up -d"
```

## 📊 Мониторинг

### Проверка статуса
```bash
make remote-status
```

### Просмотр логов
```bash
make remote-logs

# Или в режиме реального времени
ssh 4feb "cd ~/strain_ultra_minimal && docker compose logs -f"
```

### Health checks
Система автоматически проверяет:
- Статус Docker контейнеров
- HTTP доступность API
- Время отклика сервисов

## 🚨 Устранение проблем

### Проблема: Ошибка авторизации Docker Hub
```bash
docker login --username gimmyhat
# Введите пароль или токен
```

### Проблема: SSH недоступен
```bash
# Проверка подключения
ssh 4feb "echo 'OK'"

# Добавление ключа
ssh-copy-id 4feb
```

### Проблема: Контейнеры не запускаются
```bash
# Проверка логов
make remote-logs

# Перезапуск
make remote-restart

# Полная переустановка
ssh 4feb "cd ~/strain_ultra_minimal && \
  docker compose down -v && \
  docker system prune -f && \
  docker compose up -d"
```

## 📈 CI/CD Integration

### GitHub Actions (пример)
```yaml
name: Auto Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy
        run: ./scripts/auto_deploy.sh --force
        env:
          DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}
          DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
```

### GitLab CI (пример)
```yaml
deploy:
  stage: deploy
  script:
    - ./scripts/auto_deploy.sh --force
  only:
    - main
```

## 🎯 Best Practices

1. **Используйте интерактивный режим** для ручного деплоя
2. **Настройте Git hooks** для автоматического деплоя
3. **Проверяйте логи** после каждого деплоя
4. **Делайте резервные копии** перед критическими обновлениями
5. **Тестируйте в dev режиме** перед продуктивным деплоем

## 🔗 Связанные документы

- [README.md](README.md) - Основная документация
- [DEV_QUICK_START.md](DEV_QUICK_START.md) - Разработка
- [DEPLOYMENT_README.md](DEPLOYMENT_README.md) - Ручной деплой
- [BACKUP_QUICK_START.md](BACKUP_QUICK_START.md) - Резервные копии 