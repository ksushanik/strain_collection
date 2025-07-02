# ================================================================
# Strain-Collection — минимальный Makefile
# ================================================================
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
	cd backend && \
	if [ ! -d strain_venv ]; then \
	  python3 -m venv strain_venv && . strain_venv/bin/activate && pip install -r requirements.txt; \
	fi && \
	. strain_venv/bin/activate && \
	POSTGRES_HOST=localhost POSTGRES_PORT=5433 POSTGRES_DB=strain_collection DJANGO_DEBUG=True \
	python manage.py runserver 0.0.0.0:8000 & echo $$! > ../backend.pid
	@echo "🔑  PID backend сохранён в backend.pid"

backend-down:
	@echo "🛑  Остановка Django backend ..."
	-@kill `cat backend.pid 2>/dev/null` 2>/dev/null || pkill -f "manage.py runserver" || true
	@rm -f backend.pid

# -------- React frontend -----------------------------------------------------

frontend-up:
	@echo "🎨  Запуск React frontend ..."
	cd frontend && npm install --silent && (npm run dev --silent &) && echo $$! > ../frontend.pid
	@echo "🔑  PID frontend сохранён в frontend.pid"

frontend-down:
	@echo "🛑  Остановка React frontend ..."
	-@kill `cat frontend.pid 2>/dev/null` 2>/dev/null || pkill -f vite || true
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
	@echo "\nДоступные команды:";
	@echo "  make up             — запустить ВСЕ сервисы (БД + backend + frontend)";
	@echo "  make down           — остановить ВСЕ сервисы";
	@echo "  make db-up          — запустить только PostgreSQL";
	@echo "  make db-down        — остановить PostgreSQL";
	@echo "  make backend-up     — запустить Django-backend";
	@echo "  make backend-down   — остановить Django-backend";
	@echo "  make frontend-up    — запустить React-frontend";
	@echo "  make frontend-down  — остановить React-frontend";
	@echo "  make deploy         — деплой Docker-продакшн (локально)";
	@echo "  make deploy-prod    — ПОЛНЫЙ деплой на продакшн сервер (сборка + отправка + обновление)";
	@echo "  make build-images   — собрать Docker образы";
	@echo "  make push-images    — отправить образы в Docker Hub";
	@echo "  make update-remote  — обновить удаленный сервер";
	@echo "  make status-prod    — проверить статус продакшн сервера";
	@echo "  make logs-prod      — просмотр логов продакшн сервера (make logs-prod backend 50)";
	@echo "  make migrate-prod   — применить миграции БД на продакшн сервере";

# Игнорировать аргументы для logs-prod
%:
	@: