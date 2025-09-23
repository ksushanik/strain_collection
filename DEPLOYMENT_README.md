# 🚀 Быстрое развертывание системы учета штаммов микроорганизмов

## 📋 Описание

Система учета штаммов микроорганизмов - это веб-приложение для управления коллекцией штаммов, образцов и хранилища с полным REST API и современным интерфейсом.

## 🎯 Цель

Минимальными средствами развернуть полнофункциональную систему на любом сервере с Docker.

---

## ⚡ Быстрый старт

### 1️⃣ Одной командой

```bash
# Клонируйте репозиторий и запустите автоматическое развертывание
git clone <repository-url> strain-collection
cd strain-collection
chmod +x scripts/init_deploy.sh
./scripts/init_deploy.sh
```

### 2️⃣ Готово! 

Система будет доступна на:
- 🌐 **Веб-интерфейс**: http://localhost
- 🔧 **Админ-панель**: http://localhost/admin/ (admin/admin123)
- 📡 **API**: http://localhost/api/

---

## 📦 Что включено

### ✅ Автоматически настраивается:
- PostgreSQL база данных с оптимизированными настройками
- Django backend с Gunicorn (3 воркера)
- React frontend с Nginx
- SSL сертификаты (Certbot)
- Система логирования и мониторинга
- Автоматическое создание админ-пользователя
- Импорт данных из CSV файлов (если доступны)

### 📊 Данные для импорта:
Поместите CSV файлы в папку `data/`:
- `Strains_Table.csv` - штаммы микроорганизмов
- `Samples_Table.csv` - образцы
- `Storage_Table.csv` - данные хранилища
- `IndexLetters_Table.csv` - индексные буквы
- `Sources_Table.csv` - источники
- `Locations_Table.csv` - локации
- `AppendixNotes_Table.csv` - примечания
- `Comments_Table.csv` - комментарии

---

## 🔧 Системные требования

### Минимальные:
- **ОС**: Linux, macOS, Windows (с WSL2)
- **RAM**: 2 GB
- **Диск**: 5 GB свободного места
- **Docker**: 20.10+
- **Docker Compose**: 1.29+

### Рекомендуемые:
- **ОС**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: 4 GB
- **Диск**: 20 GB (SSD)
- **CPU**: 2 cores

---

## 🛠️ Ручное развертывание

### 1. Подготовка

```bash
# Клонирование репозитория
git clone <repository-url> strain-collection
cd strain-collection

# Проверка требований
docker --version
docker-compose --version
```

### 2. Конфигурация

```bash
# Создание .env файла (автоматически создается скриптом)
cp config/env_example .env
nano .env  # Отредактируйте при необходимости
```

### 3. Запуск

```bash
# Сборка и запуск контейнеров
docker-compose up -d --build

# Применение миграций (если нужно)
docker-compose exec backend python manage.py migrate

# Создание суперпользователя
docker-compose exec backend python manage.py createsuperuser

# Импорт данных (если есть CSV файлы)
docker-compose exec backend python manage.py import_csv_data --table=all
```

---

## 📁 Структура проекта

```
strain-collection/
├── 🐳 deployment/docker-compose.yml # Основная конфигурация Docker
├── 📝 .env                        # Переменные окружения
├── 🚀 scripts/
│   └── init_deploy.sh            # Скрипт автоматического развертывания
├── 📊 data/                       # CSV файлы для импорта
│   ├── Strains_Table.csv
│   ├── Samples_Table.csv
│   └── ...
├── 🔙 backend/                    # Django API сервер
│   ├── Dockerfile
│   ├── requirements.txt
│   └── ...
├── 🎨 frontend/                   # React интерфейс
│   ├── Dockerfile
│   ├── package.json
│   └── ...
├── 💾 backups/                    # Автоматические бэкапы БД
├── 📋 logs/                       # Логи всех сервисов
└── 🔐 data/certbot/              # SSL сертификаты
```

---

## 🔐 Безопасность

### Настройки по умолчанию:
- **База данных**: изолирована в Docker сети
- **Пароли**: автогенерация в .env
- **SSL**: автоматические сертификаты Let's Encrypt
- **CORS**: настроен для локального доступа

### ⚠️ Для продакшена:
1. Измените пароли в `.env`
2. Настройте домен в `DJANGO_ALLOWED_HOSTS`
3. Включите HTTPS в nginx конфигурации
4. Настройте файрволл

---

## 💾 Управление данными

### Бэкапы
```bash
# Автоматический бэкап
make backup-create

# Восстановление
make restore-db BACKUP_FILE=backups/backup_2024-06-21_12-00-00.sql.gz
```

### Мониторинг
```bash
# Статус контейнеров
docker-compose ps

# Логи
docker-compose logs -f backend
docker-compose logs -f nginx

# Использование ресурсов
docker stats
```

### Обновления
```bash
# Остановка системы
docker-compose down

# Обновление кода
git pull

# Пересборка и запуск
docker-compose up -d --build
```

---

## 🚨 Устранение неполадок

### Проблема: Контейнеры не запускаются
```bash
# Проверка логов
docker-compose logs

# Очистка и пересборка
docker-compose down -v
docker system prune -f
docker-compose up -d --build
```

### Проблема: База данных недоступна
```bash
# Проверка состояния PostgreSQL
docker-compose exec db pg_isready -U strain_user -d strain_db

# Пересоздание volume
docker-compose down -v
docker volume rm strain-collection_postgres_data
docker-compose up -d
```

### Проблема: Веб-интерфейс недоступен
```bash
# Проверка nginx
docker-compose exec nginx nginx -t

# Проверка портов
netstat -tulpn | grep :80
```

---

## 📞 Поддержка

### 🔧 API Endpoints
- `GET /api/health/` - состояние системы
- `GET /api/strains/` - список штаммов
- `GET /api/samples/` - список образцов
- `GET /api/storage/` - данные хранилища

### 🐛 Сообщение об ошибках
При возникновении проблем приложите:
1. Вывод `docker-compose ps`
2. Логи: `docker-compose logs > logs.txt`
3. Версию Docker: `docker --version`
4. ОС и версию

### 📚 Документация
- **API**: http://localhost/api/ (Swagger UI)
- **Admin**: http://localhost/admin/docs/
- **Код**: комментарии в исходном коде

---

## 🎉 Готово к работе!

После успешного развертывания система готова для:
- ✅ Управления штаммами микроорганизмов
- ✅ Учета образцов и хранилища
- ✅ Поиска и фильтрации данных
- ✅ Массовых операций
- ✅ Экспорта данных
- ✅ Создания бэкапов

**Начните работу**: http://localhost