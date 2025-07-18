# 🚀 Автоматизированная система деплоя strain-collection

## Обзор

Полностью автоматизированная система деплоя на продакшн сервер `4feb` (https://culturedb.elcity.ru).

## Основные команды

### 🎯 Полный деплой на продакшн
```bash
make deploy-prod
```
**Выполняет все операции в автоматическом режиме:**
1. Собирает React frontend (`npm run build`)
2. Собирает Docker образы без кэша
3. Отправляет образы в Docker Hub
4. Обновляет продакшн сервер
5. Проверяет статус после развертывания

### 🔍 Мониторинг продакшн сервера
```bash
# Проверка общего статуса
make status-prod

# Просмотр логов
make logs-prod                    # Все сервисы, 50 строк
make logs-prod backend 100        # Backend, 100 строк  
make logs-prod frontend 20        # Frontend, 20 строк
make logs-prod db 30              # Database, 30 строк
```

### 🗄️ Управление миграциями базы данных
```bash
# Применение миграций (входит в deploy-prod)
make migrate-prod

# Детальная работа с миграциями
./scripts/migrate_production.sh check    # Проверить статус
./scripts/migrate_production.sh apply    # Применить миграции
./scripts/migrate_production.sh show     # Показать все миграции
```

### 🔧 Компоненты деплоя (отдельные этапы)
```bash
make build-images     # Сборка Docker образов
make push-images      # Отправка в Docker Hub
make update-remote    # Обновление удаленного сервера
```

## Структура автоматизации

```
strain_collection_new/
├── Makefile                           # Основные команды автоматизации
├── scripts/
│   ├── update_docker_hub.sh          # Отправка образов в Docker Hub
│   ├── update_remote_server.sh       # Обновление продакшн сервера (включает миграции)
│   ├── check_production_status.sh    # Проверка статуса сервера
│   ├── logs_production.sh            # Просмотр логов
│   └── migrate_production.sh         # Управление миграциями Django
└── README_DEPLOY.md                   # Эта документация
```

## Процесс автоматического деплоя

### 1. Сборка frontend
- Компиляция TypeScript
- Сборка React приложения с Vite
- Оптимизация для продакшн

### 2. Сборка Docker образов
```bash
# Backend образ
docker build --no-cache -t gimmyhat/strain-collection-backend:latest backend/

# Frontend образ  
docker build --no-cache -t gimmyhat/strain-collection-frontend:latest frontend/
```

### 3. Отправка в Docker Hub
- Проверка авторизации в Docker Hub
- Push backend и frontend образов
- Отображение размеров образов

### 4. Обновление продакшн сервера
- Подключение к серверу `4feb` по SSH
- Создание резервной копии конфигурации
- Остановка сервисов
- Загрузка новых образов
- Очистка старых образов
- Запуск обновленной системы
- **Автоматическая проверка и применение миграций Django**
- Проверка статуса health checks

## Мониторинг и диагностика

### Проверка статуса (`make status-prod`)
- ✅ Подключение к серверу
- 📊 Статус всех контейнеров
- 💾 Использование CPU и памяти
- 💿 Свободное место на диске
- 📝 Поиск ошибок в логах
- 🌐 Проверка доступности API и Frontend

### Просмотр логов (`make logs-prod`)
- Поддержка выбора сервиса (backend/frontend/db/all)
- Настраиваемое количество строк
- Инструкции для просмотра в реальном времени

## Примеры использования

### Обычный workflow разработки
```bash
# Разработка завершена, готов к деплою (включает миграции)
make deploy-prod

# Проверка после деплоя
make status-prod

# При необходимости - просмотр логов
make logs-prod backend 50

# Если нужны только миграции (без полного деплоя)
make migrate-prod
```

### Быстрая диагностика проблем
```bash
# Проверка общего состояния
make status-prod

# Детальные логи при ошибках
make logs-prod backend 100
make logs-prod frontend 50
```

### Частичное обновление
```bash
# Только пересборка образов
make build-images

# Только обновление сервера (без пересборки)
make update-remote
```

## Требования

### Локальная машина
- Docker и docker-compose
- Node.js и npm (для сборки frontend)
- SSH доступ к серверу `4feb`
- Авторизация в Docker Hub (`docker login`)

### Продакшн сервер
- Настроенный SSH ключ для подключения как `4feb`
- Docker и docker-compose на сервере
- Рабочий каталог `~/strain_ultra_minimal`

## Безопасность

- Автоматическое создание резервных копий `.env` файлов
- Graceful shutdown сервисов перед обновлением
- Health checks для проверки успешного запуска
- Откат возможен через SSH подключение

## Troubleshooting

### Проблемы с подключением
```bash
# Проверка SSH подключения
ssh 4feb

# Ручная проверка статуса на сервере
ssh 4feb 'cd ~/strain_ultra_minimal && docker compose ps'
```

### Проблемы с образами
```bash
# Проверка локальных образов
docker images | grep strain-collection

# Ручная пересборка конкретного образа
docker build --no-cache -t gimmyhat/strain-collection-frontend:latest frontend/
```

### Проблемы на продакшн сервере
```bash
# Просмотр логов в реальном времени
ssh 4feb 'cd ~/strain_ultra_minimal && docker compose logs -f'

# Перезапуск сервисов
ssh 4feb 'cd ~/strain_ultra_minimal && docker compose restart'
```

## Работа с миграциями базы данных

### Автоматические миграции
При выполнении `make deploy-prod` миграции применяются автоматически:
1. Система запускается с новыми образами
2. Проверяется статус миграций (`showmigrations`)
3. Если найдены неприменённые миграции - они применяются автоматически
4. Процесс логируется и отображается в выводе

### Ручное управление миграциями
```bash
# Быстрое применение миграций
make migrate-prod

# Детальная работа с миграциями
./scripts/migrate_production.sh check     # Проверить статус
./scripts/migrate_production.sh apply     # Применить с backup'ом БД
./scripts/migrate_production.sh show      # Показать все миграции
./scripts/migrate_production.sh rollback  # Информация об откате
```

### Безопасность миграций
- Автоматическое создание backup'а БД перед применением миграций
- Проверка работоспособности backend контейнера
- Детальное логирование всех операций
- Информация об откате миграций (только через администратора)

### Troubleshooting миграций
```bash
# Проверка статуса миграций
ssh 4feb 'cd ~/strain_ultra_minimal && docker compose exec backend python manage.py showmigrations'

# Ручное применение конкретной миграции
ssh 4feb 'cd ~/strain_ultra_minimal && docker compose exec backend python manage.py migrate app_name migration_number'

# Просмотр SQL для миграции (без применения)
ssh 4feb 'cd ~/strain_ultra_minimal && docker compose exec backend python manage.py sqlmigrate app_name migration_number'
```

## Мониторинг после деплоя

После успешного деплоя система автоматически доступна по адресу:
- **Frontend**: https://culturedb.elcity.ru
- **API**: https://culturedb.elcity.ru/api/
- **Health Check**: https://culturedb.elcity.ru/api/health/

Используйте `make status-prod` для регулярной проверки состояния системы. 