#!/bin/bash

# Скрипт для просмотра логов продакшн сервера
# Использование: ./scripts/logs_production.sh [service] [lines]
# Примеры:
#   ./scripts/logs_production.sh backend 50
#   ./scripts/logs_production.sh frontend 20
#   ./scripts/logs_production.sh all 30

set -e

REMOTE_HOST="4feb"
REMOTE_DIR="~/strain_ultra_minimal"

SERVICE=${1:-all}
LINES=${2:-50}

echo "📝 Просмотр логов продакшн сервера..."
echo "📅 Дата: $(date '+%Y-%m-%d %H:%M:%S')"
echo "🌐 Сервер: $REMOTE_HOST"
echo "🔍 Сервис: $SERVICE"
echo "📊 Строк: $LINES"
echo ""

# Функция для выполнения команд на удаленном сервере
run_remote() {
    local cmd="$1"
    ssh $REMOTE_HOST "cd $REMOTE_DIR && $cmd"
}

# Проверяем доступность сервера
if ! ssh -o ConnectTimeout=5 $REMOTE_HOST "echo 'OK'" >/dev/null 2>&1; then
    echo "❌ Не удается подключиться к серверу $REMOTE_HOST"
    exit 1
fi

case $SERVICE in
    "backend")
        echo "🔧 Логи Backend:"
        run_remote "docker compose logs --tail=$LINES backend"
        ;;
    "frontend")
        echo "🎨 Логи Frontend:"
        run_remote "docker compose logs --tail=$LINES frontend"
        ;;
    "db"|"database")
        echo "🐘 Логи Database:"
        run_remote "docker compose logs --tail=$LINES db"
        ;;
    "all"|*)
        echo "📝 Логи всех сервисов:"
        echo ""
        echo "=== 🔧 Backend ==="
        run_remote "docker compose logs --tail=$LINES backend"
        echo ""
        echo "=== 🎨 Frontend ==="
        run_remote "docker compose logs --tail=$LINES frontend"
        echo ""
        echo "=== 🐘 Database ==="
        run_remote "docker compose logs --tail=$LINES db"
        ;;
esac

echo ""
echo "✅ Просмотр логов завершен!"
echo ""
echo "💡 Для просмотра логов в реальном времени используйте:"
echo "ssh $REMOTE_HOST 'cd $REMOTE_DIR && docker compose logs -f $SERVICE'" 