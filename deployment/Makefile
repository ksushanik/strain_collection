ifeq ($(OS),Windows_NT)
SHELL := C:/Progra~1/Git/bin/bash.exe
endif

# Основные команды Makefile
#   make up            Запустить все сервисы (БД + backend + frontend)
#   make down          Остановить все локальные сервисы
#   make db-up|db-down Запустить / остановить PostgreSQL
#   make backend-up|backend-down   Запустить / остановить Django backend
#   make frontend-up|frontend-down Запустить / остановить React frontend
#   make test          Запустить все тесты проекта
#   make test-unit     Запустить только unit тесты
#   make test-api      Запустить только API тесты
#   make test-coverage Запустить тесты с отчётом по покрытию
#   make deploy        Локальный деплой (Docker build + up)
#   make deploy-prod   Полный деплой на прод (сборка + публикация + обновление)
#   make build-images  Собрать Docker образы
#   make push-images   Отправить образы в Docker Hub
#   make update-remote Обновить удалённый сервер
# ================================================================

.PHONY: help up down db-up db-down backend-up backend-down frontend-up frontend-down test test-unit test-api test-coverage deploy deploy-prod build-images push-images update-remote status-prod logs-prod migrate-prod

# -------- PostgreSQL ---------------------------------------------------------

db-up:
	@echo "Запускаем PostgreSQL..."
	docker compose -f docker-compose.dev.yml up -d postgres
	docker compose -f docker-compose.dev.yml ps

db-down:
	@echo "Останавливаем PostgreSQL..."
	docker compose -f docker-compose.dev.yml stop postgres || true

# -------- Django backend -----------------------------------------------------

backend-up:
	@echo "Запускаем Django backend..."
	@if [ ! -d ../strain_venv ]; then \
		cd .. && python -m venv strain_venv && \
		strain_venv/Scripts/pip install -r backend/requirements.txt; \
	fi
	@cd ../backend && \
	../strain_venv/Scripts/python.exe manage.py migrate
	@cd ../backend && \
	../strain_venv/Scripts/python.exe manage.py runserver 0.0.0.0:8000 &
	@echo "Backend доступен по адресу http://localhost:8000"

backend-down:
	@echo "Останавливаем Django backend..."
	@taskkill /F /IM python.exe 2>/dev/null || echo "Backend уже остановлен"

# -------- React frontend -----------------------------------------------------

frontend-up:
	@echo "Запускаем React frontend..."
	@cd ../frontend && npm install --silent && (npm run dev &) && echo $$! > ../deployment/frontend.pid
	@echo "Frontend доступен по адресу http://localhost:3000"

frontend-down:
	@echo "Останавливаем React frontend..."
	@$(SHELL) -lc "kill `cat frontend.pid 2>/dev/null` 2>/dev/null || taskkill /F /IM node.exe 2>/dev/null || echo 'Frontend уже остановлен'"
	@$(SHELL) -lc "rm -f frontend.pid"

# -------- Orchestrators ------------------------------------------------------

up: db-up backend-up frontend-up
	@echo "Все сервисы запущены:"
	@echo "  Backend -> http://localhost:8000/api/health/"
	@echo "  Frontend -> http://localhost:3000"

down: frontend-down backend-down db-down
	@echo "Все локальные сервисы остановлены"

# -------- Production build & deployment --------------------------------------

build-frontend:
	@echo "Собираем React frontend..."
	cd ../frontend && npm run build

build-images: build-frontend
	@echo "Собираем Docker образы..."
	docker build --no-cache -t gimmyhat/strain-collection-backend:latest ../backend/
	docker build --no-cache -t gimmyhat/strain-collection-frontend:latest ../frontend/
	@echo "Сборка образов завершена"

push-images:
	@echo "Публикуем образы в Docker Hub..."
	@../scripts/update_docker_hub.sh

update-remote:
	@echo "Обновляем удалённый сервер..."
	@../scripts/update_remote_server.sh

status-prod:
	@echo "Проверяем состояние сервисов на проде..."
	@../scripts/check_production_status.sh

logs-prod:
	@echo "Просматриваем логи продакшн-сервисов..."
	@../scripts/logs_production.sh $(filter-out logs-prod,$(MAKECMDGOALS))

migrate-prod:
	@echo "Применяем миграции БД на проде..."
	@../scripts/migrate_production.sh apply

deploy-prod: build-images push-images update-remote
	@echo "Продакшн окружение обновлено!"
	@echo "Сайт доступен: https://culturedb.elcity.ru"

# -------- Local production deploy --------------------------------------------

deploy: build-frontend
	@echo "Локальный деплой (frontend build + docker build + up)..."
	docker compose down --remove-orphans || true
	docker compose build --no-cache
	docker compose up -d
	@docker compose ps
	@echo "Стек поднят, приложения доступны на http://localhost"

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
	@echo "  make test           - zapustit' vse testy";
	@echo "  make test-unit      - zapustit' tol'ko unit testy";
	@echo "  make test-api       - zapustit' tol'ko API testy";
	@echo "  make test-coverage  - zapustit' testy s otchetom pokrytiya";
	@echo "  make status-prod    - proverit' status prodakshn servera";
	@echo "  make logs-prod      - prosmotr logov prodakshn servera (make logs-prod backend 50)";
	@echo "  make migrate-prod   - primenit' migracii BD na prodakshn servere";

# -------- Testing -------------------------------------------------------------

test:
	@echo "Запускаем полный набор тестов..."
	@if [ ! -d ../strain_venv ]; then \
		cd .. && python -m venv strain_venv && \
		strain_venv/Scripts/pip install -r backend/requirements.txt; \
	fi
	@cd ../backend && \
	ENV_FILE=../backend/.env.test \
	../strain_venv/Scripts/python.exe -m pytest -v

test-unit:
	@echo "Запускаем unit-тесты..."
	@cd ../backend && \
	ENV_FILE=../backend/.env.test \
	../strain_venv/Scripts/python.exe -m pytest -v -m unit

test-api:
	@echo "Запускаем API-тесты..."
	@cd ../backend && \
	ENV_FILE=../backend/.env.test \
	../strain_venv/Scripts/python.exe -m pytest -v -m api

test-coverage:
	@echo "Запускаем тесты с отчётом по покрытию..."
	@cd ../backend && \
	ENV_FILE=../backend/.env.test \
	../strain_venv/Scripts/python.exe -m pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "HTML-отчёт доступен по пути ../backend/htmlcov/index.html"

# Заглушка для целей logs-prod
%:
	@:

