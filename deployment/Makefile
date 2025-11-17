ifeq ($(OS),Windows_NT)
SHELL := C:/Progra~1/Git/bin/bash.exe
PY := py -3.11
VENV_DIR := ../strain_venv
VENV_BIN := $(VENV_DIR)/Scripts
KILL_BACKEND := taskkill /F /IM python.exe 2>/dev/null || echo "Backend уже остановлен"
else
PY := python3
VENV_DIR := ../strain_venv_wsl
VENV_BIN := $(VENV_DIR)/bin
KILL_BACKEND := pkill -f "manage.py runserver" 2>/dev/null || echo "Backend уже остановлен"
endif
export DOCKER_BUILDKIT ?= 1
export COMPOSE_DOCKER_CLI_BUILD ?= 1

# Репозиторий и имя workflow для ручного запуска деплоя через GitHub CLI
REPO ?= ksushanik/strain_collection
WORKFLOW_NAME ?= Deploy to Production
WORKFLOW_FILE ?= deploy.yml
GH_TOKEN_FILE ?= ../.github/gh.env

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

.PHONY: help up down db-up db-down backend-up backend-down frontend-up frontend-down test test-unit test-api test-coverage deploy deploy-no-bake deploy-prod build-images push-images update-remote status-prod logs-prod migrate-prod deploy-gh deploy-gh-status deploy-gh-logs deploy-gh-watch

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
	@# Проверка наличия интерпретатора Python
	@$(SHELL) -lc "command -v $(PY) >/dev/null 2>&1 || { echo '❌ Не найден интерпретатор $(PY).'; echo '   WSL/Ubuntu: sudo apt update && sudo apt install -y python3 python3-venv'; echo '   Windows: установите Python 3.11/3.12 и проверьте команду py -3.11'; exit 1; }"
	@if [ ! -d $(VENV_DIR) ]; then \
		$(PY) -m venv $(VENV_DIR) && \
		$(VENV_BIN)/pip install -r ../backend/requirements.txt; \
	fi
	@# Проверка, что venv создан и python доступен
	@$(SHELL) -lc "[ -x $(VENV_BIN)/python ] || { echo '❌ Виртуальное окружение не создано или повреждено: $(VENV_BIN)/python не найден.'; echo '   WSL/Ubuntu: убедитесь, что установлен пакет python3-venv: sudo apt update && sudo apt install -y python3-venv'; echo '   Затем удалите каталог '$(VENV_DIR)' и повторите make backend-up'; exit 1; }"
	@cd ../backend && \
	$(VENV_BIN)/python manage.py migrate
	@cd ../backend && \
	$(VENV_BIN)/python manage.py runserver 0.0.0.0:8000 &
	@echo "Backend доступен по адресу http://localhost:8000"

backend-down:
	@echo "Останавливаем Django backend..."
	@$(KILL_BACKEND)

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
	docker pull gimmyhat/strain-collection-backend:latest || true
	docker build -t gimmyhat/strain-collection-backend:latest --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from gimmyhat/strain-collection-backend:latest ../backend/
	docker pull gimmyhat/strain-collection-frontend:latest || true
	docker build -t gimmyhat/strain-collection-frontend:latest --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from gimmyhat/strain-collection-frontend:latest ../frontend/
	@echo "Сборка образов завершена"

build-images-buildx: build-frontend
	@echo "Собираем Docker образы (buildx + registry cache)..."
	@docker buildx ls >/dev/null 2>&1 || docker buildx create --use --name strain_builder
	@docker buildx use strain_builder || true
	docker buildx build -t gimmyhat/strain-collection-backend:latest --build-arg BUILDKIT_INLINE_CACHE=1 --cache-to=type=registry,ref=gimmyhat/strain-collection-backend:cache,mode=max --cache-from=type=registry,ref=gimmyhat/strain-collection-backend:cache --output=type=docker ../backend/
	docker buildx build -t gimmyhat/strain-collection-frontend:latest --build-arg BUILDKIT_INLINE_CACHE=1 --cache-to=type=registry,ref=gimmyhat/strain-collection-frontend:cache,mode=max --cache-from=type=registry,ref=gimmyhat/strain-collection-frontend:cache --output=type=docker ../frontend/
	@echo "Сборка образов (buildx) завершена"

push-images:
	@echo "Публикуем образы в Docker Hub..."
	docker push gimmyhat/strain-collection-backend:latest
	docker push gimmyhat/strain-collection-frontend:latest
	@echo "Публикация образов завершена"

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

# -------- GitHub Actions manual trigger -------------------------------------

deploy-gh:
	@echo "Запускаем GitHub Actions деплой вручную..."
	@echo "Репозиторий: $(REPO)"
	@echo "Workflow: $(WORKFLOW_NAME)"
	@TOKEN=$${GH_TOKEN}; \
	if [ -z "$$TOKEN" ] && [ -f "$(GH_TOKEN_FILE)" ]; then \
	  TOKEN=$$(grep -E '^GH_TOKEN=' "$(GH_TOKEN_FILE)" | sed -E 's/^GH_TOKEN=//' | tr -d '\r'); \
	  [ -n "$$TOKEN" ] && echo "GH_TOKEN загружен из $(GH_TOKEN_FILE)" || true; \
	fi; \
	if [ -z "$$TOKEN" ] && ! gh auth status -h github.com >/dev/null 2>&1; then \
	  echo "❌ gh не авторизован и GH_TOKEN не задан"; \
	  exit 1; \
	fi; \
	GH_TOKEN="$$TOKEN" gh workflow run "$(WORKFLOW_NAME)" -R $(REPO) --ref main || GH_TOKEN="$$TOKEN" gh workflow run $(WORKFLOW_FILE) -R $(REPO) --ref main
	@echo "Команда отправлена. Проверяйте статус в GitHub → Actions"

deploy-gh-status:
	@echo "Показываем статус последнего запуска деплоя..."
	@TOKEN=$${GH_TOKEN}; \
	if [ -z "$$TOKEN" ] && [ -f "$(GH_TOKEN_FILE)" ]; then \
	  TOKEN=$$(grep -E '^GH_TOKEN=' "$(GH_TOKEN_FILE)" | sed -E 's/^GH_TOKEN=//' | tr -d '\r'); \
	  [ -n "$$TOKEN" ] && echo "GH_TOKEN загружен из $(GH_TOKEN_FILE)" || true; \
	fi; \
	if [ -z "$$TOKEN" ] && ! gh auth status -h github.com >/dev/null 2>&1; then \
	  echo "❌ gh не авторизован и GH_TOKEN не задан"; \
	  exit 1; \
	fi; \
	RUN_ID=$$(GH_TOKEN="$$TOKEN" gh run list --workflow $(WORKFLOW_FILE) -R $(REPO) --limit 1 --json databaseId --jq '.[0].databaseId' || true); \
	if [ -z "$$RUN_ID" ]; then \
	  RUN_ID=$$(GH_TOKEN="$$TOKEN" gh run list --workflow "$(WORKFLOW_NAME)" -R $(REPO) --limit 1 --json databaseId --jq '.[0].databaseId' || true); \
	fi; \
	if [ -z "$$RUN_ID" ]; then \
	  echo "Не найден последний запуск workflow"; \
	  exit 1; \
	fi; \
	GH_TOKEN="$$TOKEN" gh run view $$RUN_ID -R $(REPO)

deploy-gh-logs:
	@echo "Показываем логи последнего запуска деплоя..."
	@TOKEN=$${GH_TOKEN}; \
	if [ -z "$$TOKEN" ] && [ -f "$(GH_TOKEN_FILE)" ]; then \
	  TOKEN=$$(grep -E '^GH_TOKEN=' "$(GH_TOKEN_FILE)" | sed -E 's/^GH_TOKEN=//' | tr -d '\r'); \
	  [ -n "$$TOKEN" ] && echo "GH_TOKEN загружен из $(GH_TOKEN_FILE)" || true; \
	fi; \
	if [ -z "$$TOKEN" ] && ! gh auth status -h github.com >/dev/null 2>&1; then \
	  echo "❌ gh не авторизован и GH_TOKEN не задан"; \
	  exit 1; \
	fi; \
	RUN_ID=$$(GH_TOKEN="$$TOKEN" gh run list --workflow $(WORKFLOW_FILE) -R $(REPO) --limit 1 --json databaseId --jq '.[0].databaseId' || true); \
	if [ -z "$$RUN_ID" ]; then \
	  RUN_ID=$$(GH_TOKEN="$$TOKEN" gh run list --workflow "$(WORKFLOW_NAME)" -R $(REPO) --limit 1 --json databaseId --jq '.[0].databaseId' || true); \
	fi; \
	if [ -z "$$RUN_ID" ]; then \
	  echo "Не найден последний запуск workflow"; \
	  exit 1; \
	fi; \
	GH_TOKEN="$$TOKEN" gh run view $$RUN_ID -R $(REPO) --log

deploy-gh-watch:
	@echo "Стримим логи последнего запуска деплоя до завершения..."
	@TOKEN=$${GH_TOKEN}; \
	if [ -z "$$TOKEN" ] && [ -f "$(GH_TOKEN_FILE)" ]; then \
	  TOKEN=$$(grep -E '^GH_TOKEN=' "$(GH_TOKEN_FILE)" | sed -E 's/^GH_TOKEN=//' | tr -d '\r'); \
	  [ -n "$$TOKEN" ] && echo "GH_TOKEN загружен из $(GH_TOKEN_FILE)" || true; \
	fi; \
	if [ -z "$$TOKEN" ] && ! gh auth status -h github.com >/dev/null 2>&1; then \
	  echo "❌ gh не авторизован и GH_TOKEN не задан"; \
	  exit 1; \
	fi; \
	RUN_ID=$$(GH_TOKEN="$$TOKEN" gh run list --workflow $(WORKFLOW_FILE) -R $(REPO) --limit 1 --json databaseId --jq '.[0].databaseId' || true); \
	if [ -z "$$RUN_ID" ]; then \
	  RUN_ID=$$(GH_TOKEN="$$TOKEN" gh run list --workflow "$(WORKFLOW_NAME)" -R $(REPO) --limit 1 --json databaseId --jq '.[0].databaseId' || true); \
	fi; \
	if [ -z "$$RUN_ID" ]; then \
	  echo "Не найден последний запуск workflow"; exit 1; \
	fi; \
	GH_TOKEN="$$TOKEN" gh run watch $$RUN_ID -R $(REPO) --exit-status

# -------- Local production deploy --------------------------------------------

deploy: build-frontend
	@echo "Локальный деплой (frontend build + docker build + up)..."
	docker compose down --remove-orphans || true
	docker compose build
	docker compose up -d
	@docker compose ps
	@echo "Стек поднят, приложения доступны на http://localhost"

deploy-backend:
	@echo "Деплой только backend..."
	docker compose build backend
	docker compose up -d backend
	@docker compose ps

deploy-frontend: build-frontend
	@echo "Деплой только frontend..."
	docker compose build frontend
	docker compose up -d frontend
	@docker compose ps

deploy-%:
	@echo "Деплой только $*..."
	docker compose build $*
	docker compose up -d $*
	@docker compose ps

# Альтернативный деплой с отключением BuildKit/Bake (обход ошибки 'failed to execute bake')
deploy-no-bake: build-frontend
	@echo "Локальный деплой без BuildKit/Bake (обход bake-ошибки)..."
	docker compose down --remove-orphans || true
	COMPOSE_DOCKER_CLI_BUILD=0 DOCKER_BUILDKIT=0 docker compose build
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
	@echo "  make deploy-no-bake - lokal'nyj deploj s OTKLYuChyonnym BuildKit/Bake (obhod oshibki bake)";
	@echo "  make deploy-prod    - POLNYJ deploj na prodakshn server (sborka + otpravka + obnovlenie)";
	@echo "  make build-images   - sobrat' Docker obrazy";
	@echo "  make build-images-buildx - buildx sborka s registry cache";
	@echo "  make push-images    - otpravit' obrazy v Docker Hub";
	@echo "  make update-remote  - obnovit' udalennyj server";
	@echo "  make deploy-backend  - deploj tol'ko backend";
	@echo "  make deploy-frontend - deploj tol'ko frontend";
	@echo "  make deploy-<service> - deploj ukazannogo servisa (pattern)";
	@echo "  make deploy-gh      - zapustit' GitHub Actions deploy (ruchnoj trigger)";
	@echo "  make deploy-gh-status- pokazat' status poslednego zapuska GA deploya";
	@echo "  make deploy-gh-logs  - pokazat' logi poslednego zapuska GA deploya";
	@echo "  make deploy-gh-watch - strimit' logi poslednego zapuska GA deploya do zaversheniya";
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
	@# Проверка наличия интерпретатора Python
	@$(SHELL) -lc "command -v $(PY) >/dev/null 2>&1 || { echo '❌ Не найден интерпретатор $(PY).'; echo '   WSL/Ubuntu: sudo apt update && sudo apt install -y python3 python3-venv'; echo '   Windows: установите Python 3.11/3.12 и проверьте команду py -3.11'; exit 1; }"
	@if [ ! -d $(VENV_DIR) ]; then \
		$(PY) -m venv $(VENV_DIR) && \
		$(VENV_BIN)/pip install -r ../backend/requirements.txt; \
	fi
	@# Проверка, что venv создан и python доступен
	@$(SHELL) -lc "[ -x $(VENV_BIN)/python ] || { echo '❌ Виртуальное окружение не создано или повреждено: $(VENV_BIN)/python не найден.'; echo '   WSL/Ubuntu: убедитесь, что установлен пакет python3-venv: sudo apt update && sudo apt install -y python3-venv'; echo '   Затем удалите каталог '$(VENV_DIR)' и повторите make test'; exit 1; }"
	@cd ../backend && \
	ENV_FILE=../backend/.env.test \
	$(VENV_BIN)/python -m pytest -v

test-unit:
	@echo "Запускаем unit-тесты..."
	@cd ../backend && \
	ENV_FILE=../backend/.env.test \
	$(VENV_BIN)/python -m pytest -v -m unit

test-api:
	@echo "Запускаем API-тесты..."
	@cd ../backend && \
	ENV_FILE=../backend/.env.test \
	$(VENV_BIN)/python -m pytest -v -m api

test-coverage:
	@echo "Запускаем тесты с отчётом по покрытию..."
	@cd ../backend && \
	ENV_FILE=../backend/.env.test \
	$(VENV_BIN)/python -m pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "HTML-отчёт доступен по пути ../backend/htmlcov/index.html"

# Заглушка для целей logs-prod
%:
	@:

