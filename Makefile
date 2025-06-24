# Makefile для управления системой учета штаммов микроорганизмов

.PHONY: help setup start stop restart import clean test

# Цвета для вывода
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Показать справку
	@echo "$(BLUE)=============================================================================$(NC)"
	@echo "$(BLUE)    Система учета штаммов микроорганизмов - Команды управления$(NC)"
	@echo "$(BLUE)=============================================================================$(NC)"
	@echo ""
	@echo "$(GREEN)🚀 БЫСТРОЕ РАЗВЕРТЫВАНИЕ:$(NC)"
	@echo "  $(YELLOW)quick-deploy$(NC)  - Полное автоматическое развертывание в Docker"
	@echo "  $(YELLOW)deploy-prod$(NC)   - Продакшн развертывание с оптимизациями"
	@echo "  $(YELLOW)deploy-clean$(NC)  - Чистое развертывание (удаляет все данные)"
	@echo "  $(YELLOW)deploy-dev$(NC)    - Развертывание для разработки"
	@echo ""
	@echo "$(GREEN)🔧 DOCKER УПРАВЛЕНИЕ:$(NC)"
	@echo "  $(YELLOW)docker-up$(NC)     - Запуск Docker контейнеров"
	@echo "  $(YELLOW)docker-down$(NC)   - Остановка Docker контейнеров"
	@echo "  $(YELLOW)docker-build$(NC)  - Сборка Docker образов"
	@echo "  $(YELLOW)docker-logs$(NC)   - Просмотр логов всех контейнеров"
	@echo ""
	@echo "$(GREEN)🔧 ЛОКАЛЬНАЯ РАЗРАБОТКА:$(NC)"
	@echo "  $(YELLOW)dev-setup$(NC)      - Настройка разработки (только БД в Docker)"
	@echo "  $(YELLOW)dev-start$(NC)      - Запуск режима разработки"
	@echo "  $(YELLOW)dev-backend$(NC)    - Запуск Django backend локально"
	@echo "  $(YELLOW)dev-frontend$(NC)   - Запуск React frontend локально"
	@echo "  $(YELLOW)dev-stop$(NC)       - Остановка режима разработки"
	@echo ""
	@echo "$(GREEN)🎨 ФРОНТЕНД УПРАВЛЕНИЕ:$(NC)"
	@echo "  $(YELLOW)frontend-build$(NC)  - Пересборка фронтенда с актуальными изменениями"
	@echo "  $(YELLOW)frontend-deploy$(NC) - Быстрое обновление фронтенда в Docker"
	@echo "  $(YELLOW)frontend-dev$(NC)    - Запуск фронтенда в dev режиме"
	@echo ""
	@echo "$(GREEN)🔧 КЛАССИЧЕСКИЕ КОМАНДЫ:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -v "deploy\|docker\|dev-" | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

setup: ## Установка и настройка проекта
	@echo "$(GREEN)🚀 Настройка проекта...$(NC)"
	@echo "📦 Создание виртуальной среды..."
	cd backend && python3 -m venv strain_venv
	@echo "📥 Установка зависимостей..."
	cd backend && . strain_venv/bin/activate && pip install -r requirements.txt
	@echo "📋 Копирование файла окружения..."
	cd backend && cp env_example .env || true
	@echo "$(GREEN)✅ Настройка завершена!$(NC)"

db-start: ## Запустить PostgreSQL контейнер
	@echo "$(GREEN)🐘 Запуск PostgreSQL...$(NC)"
	docker compose up -d
	@echo "⏳ Ожидание запуска базы данных..."
	sleep 10

db-stop: ## Остановить PostgreSQL контейнер
	@echo "$(RED)🛑 Остановка PostgreSQL...$(NC)"
	docker compose down

db-restart: db-stop db-start ## Перезапустить PostgreSQL

migrate: ## Применить миграции Django
	@echo "$(BLUE)🔄 Применение миграций...$(NC)"
	cd backend && . strain_venv/bin/activate && python manage.py makemigrations
	cd backend && . strain_venv/bin/activate && python manage.py migrate

import: ## Импорт данных из CSV файлов
	@echo "$(GREEN)📥 Импорт данных из CSV...$(NC)"
	cd backend && . strain_venv/bin/activate && python scripts/import_data.py

start: db-start migrate ## Запустить Django сервер
	@echo "$(GREEN)🌟 Запуск Django сервера...$(NC)"
	cd backend && . strain_venv/bin/activate && python manage.py runserver 0.0.0.0:8000

dev: ## Запустить в режиме разработки
	@echo "$(GREEN)🔧 Запуск в режиме разработки...$(NC)"
	cd backend && . strain_venv/bin/activate && python manage.py runserver

admin: ## Создать суперпользователя
	@echo "$(BLUE)👤 Создание суперпользователя...$(NC)"
	cd backend && . strain_venv/bin/activate && python manage.py createsuperuser

shell: ## Открыть Django shell
	cd backend && . strain_venv/bin/activate && python manage.py shell

test: ## Запустить тесты
	@echo "$(BLUE)🧪 Запуск тестов...$(NC)"
	cd backend && . strain_venv/bin/activate && python manage.py test

clean-db: ## Очистить базу данных
	@echo "$(RED)🗑️  Очистка базы данных...$(NC)"
	cd backend && . strain_venv/bin/activate && python manage.py shell -c "from collection_manager.models import *; Sample.objects.all().delete(); Strain.objects.all().delete(); Storage.objects.all().delete(); print('База данных очищена')"

full-import: clean-db import ## Полная переустановка данных
	@echo "$(GREEN)🔄 Полная переустановка данных завершена$(NC)"

logs: ## Показать логи PostgreSQL
	docker compose logs -f db

status: ## Проверить статус системы
	@echo "$(BLUE)📊 Статус системы:$(NC)"
	@echo "Docker контейнеры:"
	docker compose ps
	@echo "\nСтатистика базы данных:"
	cd backend && . strain_venv/bin/activate && python manage.py shell -c "from collection_manager.models import *; print(f'Штаммы: {Strain.objects.count()}'); print(f'Образцы: {Sample.objects.count()}'); print(f'Хранилища: {Storage.objects.count()}')"

# === BACKUP И ВОССТАНОВЛЕНИЕ ===

backup-create: ## Создать полный backup базы данных
	@echo "$(YELLOW)💾 Создание полного backup...$(NC)"
	cd backend && . strain_venv/bin/activate && python scripts/backup_database.py create --type full
	@echo "$(GREEN)✅ Полный backup создан$(NC)"

backup-schema: ## Создать backup только схемы БД
	@echo "$(YELLOW)📋 Создание backup схемы...$(NC)"
	cd backend && . strain_venv/bin/activate && python scripts/backup_database.py create --type schema
	@echo "$(GREEN)✅ Backup схемы создан$(NC)"

backup-list: ## Показать список всех backup'ов
	@echo "$(BLUE)📂 Список backup'ов:$(NC)"
	cd backend && . strain_venv/bin/activate && python scripts/backup_database.py list

backup-cleanup: ## Очистить старые backup'ы (старше 30 дней)
	@echo "$(YELLOW)🧹 Очистка старых backup'ов...$(NC)"
	cd backend && . strain_venv/bin/activate && python scripts/backup_database.py cleanup --keep-days 30 --keep-count 10
	@echo "$(GREEN)✅ Очистка завершена$(NC)"

backup-validate: ## Валидировать backup файл
	@echo "$(BLUE)🔍 Валидация backup...$(NC)"
	@read -p "Введите имя backup файла: " backup_file; \
	cd backend && . strain_venv/bin/activate && python scripts/backup_database.py validate --file $$backup_file

restore-db: ## Восстановить базу данных из backup
	@echo "$(YELLOW)🔄 Восстановление из backup...$(NC)"
	@echo "$(RED)⚠️  ВНИМАНИЕ: Это заменит текущие данные!$(NC)"
	@read -p "Введите имя backup файла: " backup_file; \
	cd backend && . strain_venv/bin/activate && python scripts/restore_database.py $$backup_file

restore-info: ## Показать информацию о backup файле
	@echo "$(BLUE)ℹ️  Информация о backup:$(NC)"
	@read -p "Введите имя backup файла: " backup_file; \
	cd backend && . strain_venv/bin/activate && python scripts/restore_database.py $$backup_file --info-only

backup-auto-install: ## Установить автоматические backup'ы (ежедневно)
	@echo "$(GREEN)⏰ Установка автоматических backup'ов...$(NC)"
	python3 backend/scripts/setup_backup_cron.py install --schedule daily

backup-auto-remove: ## Удалить автоматические backup'ы
	@echo "$(RED)❌ Удаление автоматических backup'ов...$(NC)"
	python3 backend/scripts/setup_backup_cron.py remove

backup-auto-show: ## Показать текущие настройки автоматических backup'ов
	@echo "$(BLUE)📅 Текущие автоматические backup'ы:$(NC)"
	python3 backend/scripts/setup_backup_cron.py show

backup-test: ## Тестирование системы backup
	@echo "$(BLUE)🧪 Тестирование системы backup...$(NC)"
	python3 backend/scripts/setup_backup_cron.py test

# Совместимость с предыдущими версиями
backup: backup-create ## Создать резервную копию базы данных (алиас)
restore: restore-db ## Восстановить базу данных из резервной копии (алиас)

# ===========================================
# QUICK DEPLOYMENT COMMANDS
# ===========================================

quick-deploy: ## 🚀 Быстрое развертывание (автоматический скрипт)
	@./deploy.sh

deploy-prod: ## 🏭 Развертывание в продакшн (без интерактивности)
	@echo "$(BLUE)🚀 Развертывание в продакшн...$(NC)"
	@mkdir -p logs backups data/certbot/conf data/certbot/www
	@docker compose down --remove-orphans || true
	@docker compose up -d --build
	@echo "$(GREEN)✅ Развертывание завершено$(NC)"
	@echo "$(YELLOW)🌐 Приложение доступно по адресу: http://localhost$(NC)"

deploy-clean: ## 🗑️ Чистое развертывание (удаляет все данные)
	@echo "$(RED)⚠️  ВНИМАНИЕ: Это удалит ВСЕ данные!$(NC)"
	@read -p "Продолжить? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@docker compose down -v --remove-orphans
	@docker system prune -a -f
	@rm -rf logs/* backups/* 
	@./deploy.sh

install: setup db-start migrate import ## Полная установка проекта
	@echo "$(GREEN)🎉 Проект полностью установлен и готов к работе!$(NC)"
	@echo "$(BLUE)Доступные URL:$(NC)"
	@echo "- Админ панель: http://localhost:8000/admin/"
	@echo "- API: http://localhost:8000/api/"

test-api: ## Тестирование API endpoints с валидацией
	@echo "$(BLUE)🔍 Тестирование API с валидацией Pydantic...$(NC)"
	@echo "📊 Главная страница:"
	@curl -s http://localhost:8000/ | python3 -m json.tool || echo "❌ Сервер недоступен"
	@echo "\n📊 API статус:"
	@curl -s http://localhost:8000/api/ | python3 -m json.tool || echo "❌ API недоступен"
	@echo "\n📊 Статистика системы:"
	@curl -s http://localhost:8000/api/stats/ | python3 -c "import sys,json; data=json.load(sys.stdin); print(f'Штаммы: {data[\"counts\"][\"strains\"]}, Образцы: {data[\"counts\"][\"samples\"]}, Валидация: {data[\"validation\"][\"engine\"]}')" || echo "❌ Статистика недоступна"
	@echo "\n✅ Тестирование валидации (корректные данные):"
	@curl -X POST http://localhost:8000/api/strains/validate/ -H "Content-Type: application/json" -d '{"id": 1, "short_code": "TEST-01", "identifier": "Test strain"}' | python3 -c "import sys,json; data=json.load(sys.stdin); print(f'Валидация: {\"✅ Успешно\" if data[\"valid\"] else \"❌ Ошибка\"}')" || echo "❌ Валидация недоступна"
	@echo "\n❌ Тестирование валидации (некорректные данные):"
	@curl -X POST http://localhost:8000/api/strains/validate/ -H "Content-Type: application/json" -d '{"id": -1, "short_code": ""}' | python3 -c "import sys,json; data=json.load(sys.stdin); print(f'Валидация: {\"❌ Ошибки обнаружены (ожидаемо)\" if not data[\"valid\"] else \"✅ Неожиданно успешно\"}, Количество ошибок: {len(data.get(\"errors\", []))}')" || echo "❌ Валидация недоступна"

validate-data: ## Валидация всех данных с помощью Pydantic
	@echo "$(BLUE)🔍 Валидация всех данных...$(NC)"
	python3 backend/scripts/validate_data.py

frontend-install: ## Установка зависимостей frontend
	@echo "$(GREEN)📦 Установка зависимостей React frontend...$(NC)"
	cd frontend && npm install

frontend-dev: ## Запуск React frontend в режиме разработки
	@echo "$(GREEN)🎨 Запуск React frontend на порту 3000...$(NC)"
	cd frontend && npm run dev

frontend-build: ## Сборка production версии frontend
	@echo "$(YELLOW)📦 Сборка production версии...$(NC)"
	cd frontend && npm run build

test-search: ## Тестирование расширенного поиска
	@echo "$(BLUE)🔍 Тестирование расширенного поиска...$(NC)"
	@echo "\n📊 Поиск штаммов по Streptomyces:"
	@curl -s "http://localhost:8000/api/strains/?search=Streptomyces&limit=3" | python3 -c "import sys,json; data=json.load(sys.stdin); print(f'Найдено штаммов: {data[\"total\"]}'); [print(f'  - {s[\"short_code\"]}: {s[\"identifier\"]}') for s in data['strains'][:3]]" 2>/dev/null || echo "❌ Ошибка поиска штаммов"
	@echo "\n🧪 Поиск образцов по A1:"
	@curl -s "http://localhost:8000/api/samples/?search=A1&limit=3" | python3 -c "import sys,json; data=json.load(sys.stdin); print(f'Найдено образцов: {data[\"total\"]}'); [print(f'  - ID: {s[\"id\"]}, Штамм: {s.get(\"strain\",{}).get(\"short_code\",\"N/A\")}, Ячейка: {s.get(\"storage\",{}).get(\"cell_id\",\"N/A\")}') for s in data['samples'][:3]]" 2>/dev/null || echo "❌ Ошибка поиска образцов"
	@echo "\n🦠 Поиск по источникам (губки):"
	@curl -s "http://localhost:8000/api/samples/?source_type=Sponge&limit=3" | python3 -c "import sys,json; data=json.load(sys.stdin); print(f'Найдено образцов из губок: {data[\"total\"]}'); [print(f'  - {s.get(\"source\",{}).get(\"organism_name\",\"N/A\")} ({s.get(\"source\",{}).get(\"source_type\",\"N/A\")})') for s in data['samples'][:3]]" 2>/dev/null || echo "❌ Ошибка поиска по источникам"
	@echo "\n🌊 Поиск по локации (Baikal):"
	@curl -s "http://localhost:8000/api/samples/?search=Baikal&limit=3" | python3 -c "import sys,json; data=json.load(sys.stdin); print(f'Найдено образцов: {data[\"total\"]}'); [print(f'  - Локация: {s.get(\"location\",{}).get(\"name\",\"N/A\")}') for s in data['samples'][:3]]" 2>/dev/null || echo "❌ Ошибка поиска по локации"
	@echo "\n✅ Тестирование расширенного поиска завершено!"

# Тестирование массовых операций
test-bulk: ## Тестирование массовых операций
	@echo "$(BLUE)📋 Тестирование массовых операций...$(NC)"
	@echo "\n🔄 Тестовое массовое обновление (установка has_photo=true для образцов 1,2):"
	@curl -s -X POST "http://localhost:8000/api/samples/bulk-update/" \
		-H "Content-Type: application/json" \
		-d '{"sample_ids": [1, 2], "update_data": {"has_photo": true}}' | python3 -c "import sys,json; data=json.load(sys.stdin); print(f'Обновлено образцов: {data.get(\"updated_count\", \"ошибка\")}'); print(f'Обновленные поля: {data.get(\"updated_fields\", [])}')" 2>/dev/null || echo "❌ Ошибка массового обновления"
	@echo "\n📥 Экспорт первых 5 образцов в CSV:"
	@curl -s "http://localhost:8000/api/samples/export/?sample_ids=1,2,3,4,5" -o test_export.csv && echo "✅ Файл test_export.csv создан" || echo "❌ Ошибка экспорта"

# Тестирование аналитики
test-analytics: ## Тестирование аналитики
	@echo "$(BLUE)📊 Тестирование аналитики...$(NC)"
	@echo "\n📈 Получение статистики:"
	@curl -s "http://localhost:8000/api/stats/" | python3 -c "import sys,json; data=json.load(sys.stdin); print(f'Штаммы: {data[\"counts\"][\"strains\"]}, Образцы: {data[\"counts\"][\"samples\"]}, Хранилища: {data[\"counts\"][\"storage\"]}')" 2>/dev/null || echo "❌ Ошибка получения статистики"
	@echo "\n🏠 Проверка хранилища (топ 5):"
	@curl -s "http://localhost:8000/api/storage/?limit=5" | python3 -c "import sys,json; data=json.load(sys.stdin); storage=data.get('storage',[]); print(f'Найдено ячеек: {data.get(\"total\", 0)}'); [print(f'  - Бокс {s[\"box_id\"]}, ячейка {s[\"cell_id\"]}: {\"Занята\" if s.get(\"is_free_cell\") == False else \"Свободна\"}') for s in storage[:3]]" 2>/dev/null || echo "❌ Ошибка получения данных хранилища"

# Применение миграций для версионирования  
migrate-changelog: ## Применение миграции для системы версионирования
	@echo "$(BLUE)🔄 Применение миграции для системы версионирования...$(NC)"
	cd backend && . strain_venv/bin/activate && python manage.py migrate

# Полное тестирование новых функций
test-all-new: ## Полное тестирование новых функций
	@echo "$(GREEN)🚀 Полное тестирование новых функций...$(NC)"
	make migrate-changelog
	@echo "\n=== МАССОВЫЕ ОПЕРАЦИИ ==="
	make test-bulk
	@echo "\n=== АНАЛИТИКА ==="
	make test-analytics
	@echo "\n=== ПОИСК ==="
	make test-search
	@echo "\n$(GREEN)✅ Все тесты завершены!$(NC)"

full-dev: ## Запуск всей системы (backend + frontend)
	@echo "$(GREEN)🚀 Запуск полной системы...$(NC)"
	@echo "Backend будет доступен на http://localhost:8000"
	@echo "Frontend будет доступен на http://localhost:3000"

# =============================================================================
# DOCKER РАЗВЕРТЫВАНИЕ
# =============================================================================

quick-deploy: ## Полное автоматическое развертывание в Docker
	@echo "$(BLUE)🚀 Запуск автоматического развертывания в Docker...$(NC)"
	@chmod +x scripts/init_deploy.sh
	@./scripts/init_deploy.sh

deploy-prod: ## Продакшн развертывание с оптимизациями
	@echo "$(BLUE)🏭 Продакшн развертывание...$(NC)"
	@$(MAKE) docker-down
	@$(MAKE) docker-build
	@$(MAKE) docker-up
	@echo "$(GREEN)✅ Продакшн система развернута$(NC)"
	@echo "$(YELLOW)🌐 Веб-интерфейс: http://localhost$(NC)"
	@echo "$(YELLOW)🔧 Админ-панель: http://localhost/admin/ (admin/admin123)$(NC)"

deploy-dev: ## Развертывание для разработки
	@echo "$(BLUE)🔧 Развертывание для разработки...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)📝 Создание .env файла...$(NC)"; \
		cp env_example .env; \
	fi
	@mkdir -p data/{certbot/conf,certbot/www} backups logs
	@$(MAKE) docker-build
	@$(MAKE) docker-up
	@echo "$(GREEN)✅ Система развернута для разработки$(NC)"

docker-up: ## Запуск Docker контейнеров
	@echo "$(BLUE)🐳 Запуск Docker контейнеров...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✅ Контейнеры запущены$(NC)"

docker-down: ## Остановка Docker контейнеров
	@echo "$(BLUE)🛑 Остановка Docker контейнеров...$(NC)"
	docker compose down
	@echo "$(GREEN)✅ Контейнеры остановлены$(NC)"

docker-build: ## Сборка Docker образов
	@echo "$(BLUE)🏗️  Сборка Docker образов...$(NC)"
	docker compose build --no-cache
	@echo "$(GREEN)✅ Образы собраны$(NC)"

docker-restart: docker-down docker-up ## Перезапуск Docker контейнеров

docker-logs: ## Просмотр логов всех контейнеров
	docker compose logs -f

docker-logs-backend: ## Логи backend контейнера
	docker compose logs -f backend

docker-logs-frontend: ## Логи frontend/nginx контейнера
	docker compose logs -f nginx

docker-logs-db: ## Логи базы данных
	docker compose logs -f db

docker-status: ## Статус Docker контейнеров
	@echo "$(BLUE)📊 Статус Docker контейнеров:$(NC)"
	@docker compose ps

docker-health: ## Проверка здоровья Docker системы
	@echo "$(BLUE)🏥 Проверка здоровья Docker системы...$(NC)"
	@echo "$(YELLOW)📊 Состояние контейнеров:$(NC)"
	@docker compose ps
	@echo ""
	@echo "$(YELLOW)🌐 Проверка веб-интерфейса:$(NC)"
	@curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost || echo "❌ Недоступен"
	@echo "$(YELLOW)📡 Проверка API:$(NC)"
	@curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost/api/health/ || echo "❌ Недоступен"

docker-clean: ## Мягкая очистка Docker системы
	@echo "$(BLUE)🧹 Мягкая очистка Docker системы...$(NC)"
	docker compose down
	@echo "$(GREEN)✅ Контейнеры остановлены$(NC)"

docker-clean-all: ## Полная очистка Docker системы
	@echo "$(BLUE)🧹 Полная очистка Docker системы...$(NC)"
	docker compose down -v
	docker system prune -f
	@echo "$(GREEN)✅ Система полностью очищена$(NC)"

docker-import-data: ## Импорт данных в Docker среде
	@echo "$(BLUE)📥 Импорт данных в Docker среде...$(NC)"
	docker compose exec backend python manage.py import_csv_data --table=all
	@echo "$(GREEN)✅ Данные импортированы$(NC)"

docker-backup: ## Создание backup в Docker среде
	@echo "$(BLUE)💾 Создание backup в Docker среде...$(NC)"
	docker compose exec -T db pg_dump -U strain_user strain_db | gzip > backups/docker_backup_$(shell date +%Y-%m-%d_%H-%M-%S).sql.gz
	@echo "$(GREEN)✅ Backup создан в папке backups/$(NC)"

docker-info: ## Информация о Docker развертывании
	@echo "$(BLUE)📋 Информация о Docker развертывании:$(NC)"
	@echo ""
	@echo "$(GREEN)🌐 URL адреса:$(NC)"
	@echo "  Веб-интерфейс: http://localhost"
	@echo "  Админ-панель: http://localhost/admin/"
	@echo "  API: http://localhost/api/"
	@echo ""
	@echo "$(GREEN)🐳 Docker контейнеры:$(NC)"
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "$(GREEN)💾 Директории:$(NC)"
	@echo "  Бэкапы: ./backups/"
	@echo "  Данные: ./data/"
	@echo "  Логи: ./logs/" 

# =============================================================================
# РЕЖИМ РАЗРАБОТКИ (только БД в Docker)
# =============================================================================

dev-setup: ## Настройка разработки (только БД в Docker)
	@echo "$(GREEN)🔧 Настройка режима разработки...$(NC)"
	@echo "📋 Копирование конфигурации для разработки..."
	@cp env_dev_example .env.dev || echo "Файл .env.dev уже существует"
	@echo "📦 Создание виртуальной среды для backend..."
	@cd backend && python3 -m venv strain_venv
	@echo "📥 Установка зависимостей backend..."
	@cd backend && . strain_venv/bin/activate && pip install -r requirements.txt
	@echo "📦 Установка зависимостей frontend..."
	@cd frontend && npm install
	@echo "🐘 Запуск PostgreSQL в Docker..."
	@docker compose -f docker compose.dev.yml up -d
	@echo "⏳ Ожидание готовности базы данных..."
	@sleep 10
	@echo "🔄 Применение миграций..."
	@cd backend && . strain_venv/bin/activate && python manage.py migrate
	@echo "📥 Импорт данных..."
	@cd backend && . strain_venv/bin/activate && python scripts/import_data.py || echo "⚠️ Данные уже импортированы"
	@echo "$(GREEN)✅ Режим разработки настроен!$(NC)"
	@echo ""
	@echo "$(BLUE)🚀 Для запуска используйте:$(NC)"
	@echo "  make dev-start  # Запустить backend + frontend"

dev-start: ## Запуск режима разработки (backend + frontend)
	@echo "$(GREEN)🚀 Запуск режима разработки...$(NC)"
	@echo "🐘 Запуск PostgreSQL..."
	@docker compose -f docker compose.dev.yml up -d
	@echo ""
	@echo "$(BLUE)🔧 Backend будет доступен на: http://localhost:8000$(NC)"
	@echo "$(BLUE)🎨 Frontend будет доступен на: http://localhost:3000$(NC)"
	@echo ""
	@echo "$(YELLOW)⚠️  Запустите в отдельных терминалах:$(NC)"
	@echo "  $(GREEN)make dev-backend$(NC)   # Для Django backend"
	@echo "  $(GREEN)make dev-frontend$(NC)  # Для React frontend"

dev-backend: ## Запуск Django backend локально (порт 8000)
	@echo "$(GREEN)🔧 Запуск Django backend на порту 8000...$(NC)"
	cd backend && . strain_venv/bin/activate && python manage.py runserver 0.0.0.0:8000

dev-frontend: ## Запуск React frontend локально (порт 3000)
	@echo "$(GREEN)🎨 Запуск React frontend на порту 3000...$(NC)"
	cd frontend && npm run dev

dev-stop: ## Остановка режима разработки
	@echo "$(RED)🛑 Остановка режима разработки...$(NC)"
	@docker compose -f docker compose.dev.yml down
	@echo "$(GREEN)✅ База данных остановлена$(NC)"
	@echo "$(YELLOW)💡 Backend и frontend остановите вручную (Ctrl+C)$(NC)"

dev-status: ## Проверка статуса разработки
	@echo "$(BLUE)📊 Статус режима разработки:$(NC)"
	@echo ""
	@echo "$(GREEN)🐘 PostgreSQL (Docker):$(NC)"
	@docker compose -f docker compose.dev.yml ps
	@echo ""
	@echo "$(GREEN)🌐 Проверка подключений:$(NC)"
	@echo -n "  Backend (8000): "
	@curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:8000/api/health/ || echo "❌ Недоступен"
	@echo ""
	@echo -n "  Frontend (3000): "
	@curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:3000 || echo "❌ Недоступен"
	@echo ""

dev-reset: ## Сброс режима разработки (очистка БД)
	@echo "$(YELLOW)⚠️  Сброс режима разработки...$(NC)"
	@docker compose -f docker compose.dev.yml down -v
	@echo "$(GREEN)✅ База данных сброшена$(NC)"
	@echo "$(BLUE)💡 Запустите 'make dev-setup' для повторной настройки$(NC)"

dev-db-shell: ## Подключение к PostgreSQL через psql
	@echo "$(BLUE)🐘 Подключение к PostgreSQL...$(NC)"
	@docker compose -f docker compose.dev.yml exec postgres psql -U strain_user -d strain_collection

dev-logs: ## Просмотр логов PostgreSQL
	@docker compose -f docker compose.dev.yml logs -f postgres

dev-admin: ## Создание суперпользователя в режиме разработки
	@echo "$(BLUE)👤 Создание суперпользователя...$(NC)"
	cd backend && . strain_venv/bin/activate && python manage.py createsuperuser

dev-migrate: ## Применение миграций в режиме разработки
	@echo "$(BLUE)🔄 Применение миграций...$(NC)"
	cd backend && . strain_venv/bin/activate && python manage.py makemigrations
	cd backend && . strain_venv/bin/activate && python manage.py migrate

dev-import: ## Импорт данных в режиме разработки
	@echo "$(GREEN)📥 Импорт данных...$(NC)"
	cd backend && . strain_venv/bin/activate && python scripts/import_data.py

dev-test: ## Тестирование в режиме разработки
	@echo "$(BLUE)🧪 Тестирование режима разработки...$(NC)"
	cd backend && . strain_venv/bin/activate && python manage.py test

dev-info: ## Информация о режиме разработки
	@echo "$(BLUE)📋 Режим разработки - Информация:$(NC)"
	@echo ""
	@echo "$(GREEN)🎯 КОНЦЕПЦИЯ:$(NC)"
	@echo "  • PostgreSQL работает в Docker (порт 5432)"
	@echo "  • Django backend запускается локально (порт 8000)"
	@echo "  • React frontend запускается локально (порт 3000)"
	@echo ""
	@echo "$(GREEN)⚡ ПРЕИМУЩЕСТВА:$(NC)"
	@echo "  • Быстрая перезагрузка при изменениях"
	@echo "  • Live reload для React"
	@echo "  • Django auto-reload для backend"
	@echo "  • Полный доступ к отладке"
	@echo ""
	@echo "$(GREEN)🛠️  КОМАНДЫ:$(NC)"
	@echo "  $(YELLOW)make dev-setup$(NC)    - Первоначальная настройка"
	@echo "  $(YELLOW)make dev-start$(NC)    - Запуск (показывает инструкции)"
	@echo "  $(YELLOW)make dev-backend$(NC)  - Django backend (отдельный терминал)"
	@echo "  $(YELLOW)make dev-frontend$(NC) - React frontend (отдельный терминал)"
	@echo "  $(YELLOW)make dev-status$(NC)   - Проверка статуса"
	@echo "  $(YELLOW)make dev-stop$(NC)     - Остановка PostgreSQL"
	@echo ""
	@echo "$(GREEN)🌐 URL АДРЕСА:$(NC)"
	@echo "  Backend API: http://localhost:8000/api/"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Админ-панель: http://localhost:8000/admin/"
	@echo "  pgAdmin: http://localhost:8080 (опционально)"

# =============================================================================
# DOCKER HUB РАЗВЕРТЫВАНИЕ
# =============================================================================

build-images: ## Сборка и публикация образов в Docker Hub
	@echo "$(BLUE)🐳 Сборка и публикация образов в Docker Hub...$(NC)"
	@chmod +x build_and_push_images.sh
	@./build_and_push_images.sh

create-ultra-minimal: ## Создание ультра-минимального пакета (Docker Hub)
	@echo "$(BLUE)📦 Создание ультра-минимального пакета (Docker Hub)...$(NC)"
	@chmod +x create_ultra_minimal_deploy.sh
	@./create_ultra_minimal_deploy.sh

deploy-hub: ## Развертывание из Docker Hub
	@echo "$(BLUE)🚀 Развертывание из Docker Hub...$(NC)"
	@chmod +x deploy_hub.sh
	@./deploy_hub.sh

hub-info: ## Информация о Docker Hub развертывании
	@echo "$(BLUE)📋 Docker Hub развертывание - Информация:$(NC)"
	@echo ""
	@echo "$(GREEN)🎯 КОНЦЕПЦИЯ:$(NC)"
	@echo "  • Образы публикуются в Docker Hub"
	@echo "  • Локально нужны только: docker compose.yml + данные + .env"
	@echo "  • Размер пакета: ~2MB (вместо 47MB)"
	@echo ""
	@echo "$(GREEN)⚡ ПРЕИМУЩЕСТВА:$(NC)"
	@echo "  • Минимальный размер для копирования"
	@echo "  • Образы загружаются автоматически"
	@echo "  • Всегда актуальная версия"
	@echo "  • Простое обновление: docker compose pull"
	@echo ""
	@echo "$(GREEN)🛠️  КОМАНДЫ:$(NC)"
	@echo "  $(YELLOW)make build-images$(NC)         - Сборка и публикация в Docker Hub"
	@echo "  $(YELLOW)make create-ultra-minimal$(NC) - Создание пакета ~2MB"
	@echo "  $(YELLOW)make deploy-hub$(NC)           - Развертывание из Docker Hub"
	@echo ""
	@echo "$(GREEN)📦 ПРОЦЕСС:$(NC)"
	@echo "  1. Сборка: make build-images"
	@echo "  2. Пакет: make create-ultra-minimal"
	@echo "  3. Копирование strain_ultra_minimal.tar.gz на сервер"
	@echo "  4. Развертывание: ./deploy_hub.sh"
	@echo ""
	@echo "$(GREEN)📊 СРАВНЕНИЕ РАЗМЕРОВ:$(NC)"
	@echo "  Полный пакет:        102MB"
	@echo "  Минимальный пакет:    47MB"
	@echo "  Ультра-минимальный:   ~2MB ⭐"

# =============================================================================
# FRONTEND MANAGEMENT COMMANDS
# =============================================================================

frontend-build: ## 🎨 Пересборка фронтенда с актуальными изменениями
	@echo "$(BLUE)🎨 Пересборка фронтенда...$(NC)"
	@echo "🗑️  Очистка старой сборки..."
	cd frontend && rm -rf dist
	@echo "🔨 Сборка с актуальными изменениями..."
	cd frontend && npm run build
	@echo "$(GREEN)✅ Фронтенд пересобран с актуальными изменениями$(NC)"

frontend-deploy: frontend-build ## 🚀 Быстрое обновление фронтенда в Docker
	@echo "$(BLUE)🚀 Обновление фронтенда в Docker...$(NC)"
	@echo "🐳 Пересборка nginx образа..."
	docker compose build nginx
	@echo "🔄 Перезапуск nginx контейнера..."
	docker compose restart nginx
	@echo "$(GREEN)✅ Фронтенд обновлен в Docker!$(NC)"
	@echo "$(YELLOW)💡 Откройте браузер и обновите страницу (Ctrl+F5)$(NC)"

frontend-dev: ## 🔧 Запуск фронтенда в dev режиме
	@echo "$(GREEN)🔧 Запуск фронтенда в режиме разработки...$(NC)"
	@echo "$(YELLOW)💡 Фронтенд будет доступен на http://localhost:3000$(NC)"
	@echo "$(YELLOW)💡 Изменения применяются автоматически$(NC)"
	cd frontend && npm run dev

frontend-check: ## 🔍 Проверка синхронизации фронтенда
	@echo "$(BLUE)🔍 Проверка синхронизации фронтенда...$(NC)"
	@echo "📅 Последние изменения в исходниках:"
	@find frontend/src -name "*.tsx" -o -name "*.ts" -o -name "*.css" | head -5 | xargs ls -la --time-style=long-iso | awk '{print "  " $$6 " " $$7 " " $$8}'
	@echo "📅 Дата сборки dist:"
	@ls -la --time-style=long-iso frontend/dist/ 2>/dev/null | head -2 | tail -1 | awk '{print "  " $$6 " " $$7 " dist/"}'
	@echo "🔍 Статус git (незафиксированные изменения):"
	@git status --porcelain frontend/src/ | head -5 | sed 's/^/  /'
	@echo "$(YELLOW)💡 Если есть незафиксированные изменения, используйте 'make frontend-deploy'$(NC)"

frontend-info: ## 📋 Информация о проблемах с фронтендом
	@echo "$(BLUE)📋 Решение проблем с дизайном фронтенда:$(NC)"
	@echo ""
	@echo "$(RED)🚨 ПРОБЛЕМА:$(NC)"
	@echo "  • В dev режиме (npm run dev) дизайн правильный"
	@echo "  • После npm run build + Docker restart дизайн меняется"
	@echo "  • Причина: десинхронизация исходников и собранной версии"
	@echo ""
	@echo "$(GREEN)✅ РЕШЕНИЕ:$(NC)"
	@echo "  1. $(YELLOW)make frontend-check$(NC)  - Проверить синхронизацию"
	@echo "  2. $(YELLOW)make frontend-deploy$(NC) - Обновить фронтенд в Docker"
	@echo "  3. Обновить браузер (Ctrl+F5)"
	@echo ""
	@echo "$(GREEN)🔧 КАК ЭТО РАБОТАЕТ:$(NC)"
	@echo "  • Docker nginx копирует файлы из frontend/dist/ в образ"
	@echo "  • При изменении исходников нужно пересобрать dist/"
	@echo "  • Затем пересобрать Docker образ nginx"
	@echo ""
	@echo "$(GREEN)💡 РЕКОМЕНДАЦИИ:$(NC)"
	@echo "  • Для разработки используйте 'make dev-frontend'"
	@echo "  • Перед коммитом всегда делайте 'make frontend-deploy'"
	@echo "  • Проверяйте синхронизацию с 'make frontend-check'"

# =============================================================================
# REMOTE SERVER UPDATE COMMANDS
# =============================================================================

update-docker-hub: ## 📤 Обновление образов на Docker Hub
	@echo "$(BLUE)🚀 Обновление образов на Docker Hub...$(NC)"
	@./scripts/update_docker_hub.sh

update-remote: ## 🔄 Обновление удаленного сервера (4feb)
	@echo "$(BLUE)🔄 Обновление удаленного сервера...$(NC)"
	@./scripts/update_remote_server.sh

# Полное обновление: локальная сборка -> Docker Hub -> удаленный сервер
full-update: frontend-build ## 🚀 Полное обновление (локально -> Docker Hub -> сервер)
	@echo "$(BLUE)🔄 Полное обновление системы...$(NC)"
	@echo "$(GREEN)📝 Этапы:$(NC)"
	@echo "  1. ✅ Фронтенд пересобран"
	@echo "  2. 🔄 Сборка Docker образов..."
	@docker build -t gimmyhat/strain-collection-backend:latest -f backend/Dockerfile backend/
	@docker build -t gimmyhat/strain-collection-frontend:latest -f frontend/Dockerfile frontend/
	@echo "  3. 🔄 Отправка на Docker Hub..."
	@./scripts/update_docker_hub.sh || (echo "$(RED)❌ Ошибка отправки на Docker Hub. Проверьте авторизацию: docker login --username gimmyhat$(NC)" && exit 1)
	@echo "  4. 🔄 Обновление удаленного сервера..."
	@./scripts/update_remote_server.sh
	@echo "$(GREEN)🎉 Полное обновление завершено!$(NC)"

remote-status: ## 📊 Проверка статуса удаленного сервера
	@echo "$(BLUE)📊 Статус удаленного сервера (4feb):$(NC)"
	@ssh 4feb "cd ~/strain_ultra_minimal && echo '📊 Статус контейнеров:' && docker compose ps"
	@echo ""
	@ssh 4feb "cd ~/strain_ultra_minimal && echo '💾 Использование диска:' && df -h ."
	@echo ""
	@ssh 4feb "cd ~/strain_ultra_minimal && echo '🐳 Docker образы:' && docker images | grep strain-collection"

remote-logs: ## 📝 Просмотр логов удаленного сервера
	@echo "$(BLUE)📝 Логи удаленного сервера:$(NC)"
	@ssh 4feb "cd ~/strain_ultra_minimal && docker compose logs --tail=20"

remote-restart: ## 🔄 Перезапуск сервисов на удаленном сервере
	@echo "$(BLUE)🔄 Перезапуск сервисов на удаленном сервере...$(NC)"
	@ssh 4feb "cd ~/strain_ultra_minimal && docker compose restart"
	@echo "$(GREEN)✅ Сервисы перезапущены$(NC)"

# Автоматизированный деплой
auto-deploy: ## 🤖 Автоматический деплой (интерактивный)
	@echo "$(BLUE)🤖 Запуск автоматического деплоя...$(NC)"
	@./scripts/auto_deploy.sh

auto-deploy-force: ## ⚡ Автоматический деплой (без подтверждений)
	@echo "$(BLUE)⚡ Запуск принудительного автодеплоя...$(NC)"
	@./scripts/auto_deploy.sh --force

auto-deploy-fast: ## 🚀 Быстрый деплой (без тестов)
	@echo "$(BLUE)🚀 Запуск быстрого деплоя...$(NC)"
	@./scripts/auto_deploy.sh --force --skip-tests

setup-git-hooks: ## 🔧 Настройка Git hooks для автодеплоя
	@echo "$(BLUE)🔧 Настройка Git hooks...$(NC)"
	@./scripts/setup_git_hooks.sh

update-info: ## 📋 Информация о системе обновления
	@echo "$(BLUE)📋 Система обновления strain-collection:$(NC)"
	@echo ""
	@echo "$(GREEN)🎯 АРХИТЕКТУРА:$(NC)"
	@echo "  • Локальная разработка: dev режим"
	@echo "  • Docker Hub: централизованное хранение образов"
	@echo "  • Удаленный сервер (4feb): продуктивная система"
	@echo ""
	@echo "$(GREEN)🔄 ПРОЦЕСС ОБНОВЛЕНИЯ:$(NC)"
	@echo "  1. Изменения в коде (фронтенд/бэкенд)"
	@echo "  2. Пересборка фронтенда: make frontend-build"
	@echo "  3. Сборка Docker образов локально"
	@echo "  4. Отправка образов на Docker Hub"
	@echo "  5. Обновление удаленного сервера"
	@echo ""
	@echo "$(GREEN)🤖 АВТОМАТИЗИРОВАННЫЙ ДЕПЛОЙ:$(NC)"
	@echo "  $(YELLOW)make auto-deploy$(NC)       - Полный автодеплой (с подтверждением)"
	@echo "  $(YELLOW)make auto-deploy-force$(NC) - Принудительный автодеплой"
	@echo "  $(YELLOW)make auto-deploy-fast$(NC)  - Быстрый деплой (без тестов)"
	@echo "  $(YELLOW)make setup-git-hooks$(NC)   - Git hooks для автодеплоя"
	@echo ""
	@echo "$(GREEN)🛠️  РУЧНЫЕ КОМАНДЫ:$(NC)"
	@echo "  $(YELLOW)make full-update$(NC)        - Полное обновление (все этапы)"
	@echo "  $(YELLOW)make update-docker-hub$(NC)  - Только отправка на Docker Hub"
	@echo "  $(YELLOW)make update-remote$(NC)      - Только обновление сервера"
	@echo "  $(YELLOW)make remote-status$(NC)      - Проверка статуса сервера"
	@echo "  $(YELLOW)make remote-logs$(NC)        - Просмотр логов сервера"
	@echo ""
	@echo "$(GREEN)📋 ТРЕБОВАНИЯ:$(NC)"
	@echo "  • Авторизация в Docker Hub: docker login --username gimmyhat"
	@echo "  • SSH доступ к серверу: ssh 4feb"
	@echo "  • Папка ~/strain_ultra_minimal на сервере"
	@echo ""
	@echo "$(GREEN)🌐 АДРЕСА:$(NC)"
	@echo "  • Удаленный сервер: http://89.169.171.236:8081"
	@echo "  • Docker Hub: https://hub.docker.com/r/gimmyhat/"