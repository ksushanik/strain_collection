# Makefile для управления системой учета штаммов микроорганизмов

.PHONY: help setup start stop restart import clean test

# Цвета для вывода
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Показать справку
	@echo "$(BLUE)Система учета штаммов микроорганизмов$(NC)"
	@echo "=================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

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
	docker-compose up -d
	@echo "⏳ Ожидание запуска базы данных..."
	sleep 10

db-stop: ## Остановить PostgreSQL контейнер
	@echo "$(RED)🛑 Остановка PostgreSQL...$(NC)"
	docker-compose down

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
	docker-compose logs -f db

status: ## Проверить статус системы
	@echo "$(BLUE)📊 Статус системы:$(NC)"
	@echo "Docker контейнеры:"
	docker-compose ps
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