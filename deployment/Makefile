# ================================================================
# Strain-Collection — минимальный Makefile
# ================================================================

# Настройка кодировки для корректного отображения русского текста
export LANG=ru_RU.UTF-8
export LC_ALL=ru_RU.UTF-8
# Основные команды
#   make up            — запустить ВСЕ сервисы (БД + backend + frontend)
#   make down          — остановить ВСЕ сервисы
#   make db-up|db-down — старт / стоп PostgreSQL
#   make backend-up|backend-down   — старт / стоп Django backend
#   make frontend-up|frontend-down — старт / стоп React frontend
#   make deploy        — деплой (Docker build + up) локально
#   make deploy-prod   — полный деплой на продакшн (сборка + отправка + обновление)
#   make build-images  — сборка Docker образов
#   make push-images   — отправка образов в Docker Hub
#   make update-remote — обновление удаленного сервера
# ================================================================

.PHONY: help up down db-up db-down backend-up backend-down frontend-up frontend-down deploy deploy-prod build-images push-images update-remote status-prod logs-prod migrate-prod

# -------- PostgreSQL ---------------------------------------------------------

db-up:
	@echo "🐘  Запуск PostgreSQL ..."
	docker compose -f docker-compose.dev.yml up -d postgres
	docker compose -f docker-compose.dev.yml ps

db-down:
	@echo "🛑  Остановка PostgreSQL ..."
	docker compose -f docker-compose.dev.yml stop postgres || true

# -------- Django backend -----------------------------------------------------

backend-up:
	@echo "🔧  Запуск Django backend ..."
	@cd backend && \
	if [ ! -d strain_venv ]; then \
		python -m venv strain_venv && \
		strain_venv/Scripts/pip install -r requirements.txt; \
	fi
	@cd backend && \
	DB_HOST=localhost DB_PORT=5433 DB_NAME=strain_collection DEBUG=True \
	strain_venv/Scripts/python.exe manage.py runserver 0.0.0.0:8000 &
	@echo "🔑  Backend запущен на http://localhost:8000"

backend-down:
	@echo "🛑  Остановка Django backend ..."
	@taskkill //F //IM python.exe 2>/dev/null || echo "Backend уже остановлен"

# -------- React frontend -----------------------------------------------------

frontend-up:
	@echo "🎨  Запуск React frontend ..."
	@cd frontend && npm install --silent && (npm run dev &) && echo $$! > ../frontend.pid
	@echo "🔑  Frontend запущен на http://localhost:3000"

frontend-down:
	@echo "🛑  Остановка React frontend ..."
	@-kill `cat frontend.pid 2>/dev/null` 2>/dev/null || taskkill //F //IM node.exe 2>/dev/null || echo "Frontend уже остановлен"
	@rm -f frontend.pid

# -------- Orchestrators ------------------------------------------------------

up: db-up backend-up frontend-up
	@echo "🚀  Система поднята:"
	@echo "  Backend  → http://localhost:8000/api/health/"
	@echo "  Frontend → http://localhost:3000"

down: frontend-down backend-down db-down
	@echo "✅  Все сервисы остановлены"

# -------- Production build & deployment --------------------------------------

build-frontend:
	@echo "🎯  Сборка React frontend..."
	cd frontend && npm run build

build-images: build-frontend
	@echo "📦  Сборка Docker образов..."
	docker build --no-cache -t gimmyhat/strain-collection-backend:latest backend/
	docker build --no-cache -t gimmyhat/strain-collection-frontend:latest frontend/
	@echo "✅  Образы собраны"

push-images:
	@echo "🚢  Отправка образов в Docker Hub..."
	@./scripts/update_docker_hub.sh

update-remote:
	@echo "🌐  Обновление удаленного сервера..."
	@./scripts/update_remote_server.sh

status-prod:
	@echo "🔍  Проверка статуса продакшн сервера..."
	@./scripts/check_production_status.sh

logs-prod:
	@echo "📝  Просмотр логов продакшн сервера..."
	@./scripts/logs_production.sh $(filter-out logs-prod,$(MAKECMDGOALS))

migrate-prod:
	@echo "🗄️  Применение миграций на продакшн сервере..."
	@./scripts/migrate_production.sh apply

deploy-prod: build-images push-images update-remote
	@echo "🎉  Полный деплой на продакшн завершен!"
	@echo "🌐  Система доступна: https://culturedb.elcity.ru"

# -------- Local production deploy --------------------------------------------

deploy:
	@echo "📦  Деплой (Docker build → up) ..."
	docker compose down --remove-orphans || true
	docker compose build --no-cache
	docker compose up -d
	@docker compose ps
	@echo "🌐  Продакшн доступен по вашему домену / http://localhost"

help:
	@echo "\nDostupnye komandy (Available commands):";
	@echo "  make up             - zapustit' VSE servisy (BD + backend + frontend)";
	@echo "  make down           - ostanovit' VSE servisy";
	@echo "  make db-up          - zapustit' tol'ko PostgreSQL";
	@echo "  make db-down        - ostanovit' PostgreSQL";
	@echo "  make backend-up     - zapustit' Django-backend";
	@echo "  make backend-down   - ostanovit' Django-backend";
	@echo "  make frontend-up    - zapustit' React-frontend";
	@echo "  make frontend-down  - ostanovit' React-frontend";
	@echo "  make deploy         - deploj Docker-prodakshn (lokal'no)";
	@echo "  make deploy-prod    - POLNYJ deploj na prodakshn server (sborka + otpravka + obnovlenie)";
	@echo "  make build-images   - sobrat' Docker obrazy";
	@echo "  make push-images    - otpravit' obrazy v Docker Hub";
	@echo "  make update-remote  - obnovit' udalennyj server";
	@echo "  make status-prod    - proverit' status prodakshn servera";
	@echo "  make logs-prod      - prosmotr logov prodakshn servera (make logs-prod backend 50)";
	@echo "  make migrate-prod   - primenit' migracii BD na prodakshn servere";

# Игнорировать аргументы для logs-prod
%:
	@: