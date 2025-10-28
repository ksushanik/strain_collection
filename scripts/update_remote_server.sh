#!/bin/bash

# Скрипт для безопасного обновления системы на удаленном сервере
# Использование: ./scripts/update_remote_server.sh

set -e

REMOTE_HOST="${REMOTE_HOST:-4feb}"
REMOTE_DIR="${REMOTE_DIR:-~/strain_ultra_minimal}"
DEPLOY_WAIT_SECONDS="${DEPLOY_WAIT_SECONDS:-30}"

echo "🔄 Обновление системы strain-collection на удаленном сервере..."
echo "📅 Дата: $(date '+%Y-%m-%d %H:%M:%S')"
echo "🌐 Сервер: $REMOTE_HOST"
echo "📁 Директория: $REMOTE_DIR"
echo ""

# Функция для выполнения команд на удаленном сервере
run_remote() {
    local cmd="$1"
    echo "🔧 Выполняю: $cmd"
    ssh $REMOTE_HOST "cd $REMOTE_DIR && $cmd"
}

# Проверяем доступность сервера
echo "🔍 Проверка подключения к серверу..."
if ! ssh -o ConnectTimeout=5 $REMOTE_HOST "echo 'Подключение успешно'"; then
    echo "❌ Не удается подключиться к серверу $REMOTE_HOST"
    exit 1
fi

# Проверяем существование директории
echo "📂 Проверка директории проекта..."
if ! ssh $REMOTE_HOST "[ -d $REMOTE_DIR ]"; then
    echo "❌ Директория $REMOTE_DIR не найдена на сервере"
    exit 1
fi

# Показываем текущее состояние
echo "📊 Текущее состояние системы:"
run_remote "docker compose ps"

echo ""
echo "📥 Создание резервной копии конфигурации..."
run_remote "cp .env .env.backup.$(date +%Y%m%d_%H%M%S)"

# Остановка сервисов
echo "🛑 Остановка сервисов..."
run_remote "docker compose down"

# Скачивание новых образов
echo "🔽 Загрузка обновленных образов..."
run_remote "docker compose pull"

# Очистка старых образов
echo "🧹 Очистка старых образов..."
run_remote "docker image prune -f"

# Запуск обновленной системы
echo "🚀 Запуск обновленной системы..."
run_remote "docker compose up -d"

# Ожидание запуска сервисов
echo "⏳ Ожидание запуска сервисов (${DEPLOY_WAIT_SECONDS} сек)..."
sleep "${DEPLOY_WAIT_SECONDS}"

# Проверка и применение миграций базы данных
echo ""
echo "🗄️ Проверка миграций базы данных..."
echo "🔧 Выполняю: docker compose exec backend python manage.py showmigrations"
if run_remote "docker compose exec backend python manage.py showmigrations | grep -q '\[ \]'"; then
    echo "📋 Найдены неприменённые миграции, применяю..."
    run_remote "docker compose exec backend python manage.py migrate"
    echo "✅ Миграции применены успешно"
else
    echo "✅ Все миграции уже применены"
fi

# Проверка состояния сервисов
echo "🔍 Проверка состояния сервисов..."
run_remote "docker compose ps"

# Проверка health checks
echo "🏥 Проверка health статуса..."
run_remote "docker compose ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}'"

# Фиксация неуспешного деплоя при нездоровых сервисах
if run_remote "docker compose ps --format '{{.Name}} {{.Status}}' | grep -E '(unhealthy|Exit)'"; then
    echo "❌ Обнаружены нездоровые сервисы после деплоя"
    echo "💡 Проверьте логи: ssh $REMOTE_HOST 'cd $REMOTE_DIR && docker compose logs --tail=50'"
    exit 1
else
    echo "✅ Все сервисы запущены и здоровы"
fi

# Проверка логов последних 10 строк
echo "📝 Последние логи сервисов:"
echo "--- Backend ---"
run_remote "docker compose logs --tail=5 backend"
echo "--- Frontend ---"
run_remote "docker compose logs --tail=5 frontend"

echo ""
echo "✅ Обновление завершено!"
echo "🌐 Система доступна по адресу: http://89.169.171.236:8081"
echo ""
echo "📋 Команды для мониторинга:"
echo "ssh $REMOTE_HOST 'cd $REMOTE_DIR && docker compose ps'"
echo "ssh $REMOTE_HOST 'cd $REMOTE_DIR && docker compose logs -f'"
echo ""