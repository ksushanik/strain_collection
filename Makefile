# ================================================================
# Strain-Collection — минимальный Makefile
# ================================================================
# Основные команды
#   make up            — запустить ВСЕ сервисы (БД + backend + frontend)
#   make down          — остановить ВСЕ сервисы
#   make db-up|db-down — старт / стоп PostgreSQL
#   make backend-up|backend-down   — старт / стоп Django backend
#   make frontend-up|frontend-down — старт / стоп React frontend
#   make deploy        — деплой (Docker build + up) в продакшн
# ================================================================

.PHONY: help up down db-up db-down backend-up backend-down frontend-up frontend-down deploy

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

# -------- Production deploy --------------------------------------------------

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
	@echo "  make deploy         — деплой Docker-продакшн";