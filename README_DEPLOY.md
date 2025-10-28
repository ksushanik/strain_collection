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
├── deployment/Makefile                # Основные команды автоматизации (запускать из папки deployment)
├── scripts/
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

## CI/CD через GitHub Actions

- Триггер: только ручной запуск (`workflow_dispatch`). Автозапуск на `push` отключён.
- Сборка и публикация образов выполняется командами из `deployment/Makefile`:
  - `cd deployment && make build-images`
  - `cd deployment && make push-images`
- Запуск деплоя из CLI: `cd deployment && make deploy-gh` (требуется установленный `gh` и авторизация: `gh auth login`).
 - Проверка статуса и логов из CLI:
   - Статус последнего запуска: `cd deployment && make deploy-gh-status`
   - Логи последнего запуска: `cd deployment && make deploy-gh-logs`
   - Стриминг логов до завершения: `cd deployment && make deploy-gh-watch`

### ℹ️ Примечание об авторизации gh/GH_TOKEN
- Все цели `deploy-gh*` поддерживают два варианта авторизации:
  - Локальная авторизация `gh` через `gh auth login` (GitHub.com → HTTPS).
  - Переменная окружения `GH_TOKEN` с правами `repo` и `workflow`.
- Если `GH_TOKEN` установлен, Makefile передаёт его напрямую в команды `gh` для неинтерактивного запуска.
- Установка токена: `set GH_TOKEN=YOUR_TOKEN` (PowerShell) или `export GH_TOKEN=YOUR_TOKEN` (bash).
- SSH ключ записывается с нормализацией окончаний строк (CRLF → LF), затем настраивается алиас `4feb`.
- Деплой выполняется скриптом `scripts/update_remote_server.sh` с параметрами из секретов.
- После деплоя выполняется HTTP health-check.

#### Файл `.github/gh.env` (автозагрузка токена)
- Makefile автоматически пытается прочитать токен из файла `.github/gh.env` и выполнить `gh auth login --with-token`, если `gh` не авторизован.
- Ожидаемый формат: одна строка `GH_TOKEN=ghp_XXXXXXXX...`.
- Расположение: относительно каталога `deployment` используется путь `../.github/gh.env`.
- Безопасность: этот файл должен оставаться локальным (не хранить в VCS). Для CI используйте секреты репозитория.

Требуемые секреты репозитория:
- `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` — доступ к Docker Hub
- `PROD_SSH_KEY` — приватный SSH ключ (формат LF; в workflow CRLF нормализуется автоматически)
- `PROD_SSH_HOST`, `PROD_SSH_USER`, `PROD_SSH_PORT` — параметры SSH-подключения
- `PROD_SSH_KNOWN_HOSTS` — строка known_hosts для прод-сервера
- `PROD_REMOTE_DIR` — каталог на сервере (например, `~/strain_ultra_minimal`)
- `PROD_HEALTHCHECK_URL` — URL для проверки здоровья API

Как запустить вручную:
- Вкладка `Actions` → `Deploy to Production` → `Run workflow`.
- Из CLI: `cd deployment && make deploy-gh`.
 - Статус/логи: `cd deployment && make deploy-gh-status` / `make deploy-gh-logs` / `make deploy-gh-watch`.

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
cd deployment && make build-images

# Только обновление сервера (без пересборки)
cd deployment && make update-remote
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
cd deployment && make migrate-prod

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