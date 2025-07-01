#!/bin/bash

# Скрипт для быстрой проверки статуса продакшн сервера
# Использование: ./scripts/check_production_status.sh

set -e

REMOTE_HOST="4feb"
REMOTE_DIR="~/strain_ultra_minimal"
PROD_URL="https://culturedb.elcity.ru"

echo "🔍 Проверка статуса продакшн сервера..."
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
if ! ssh -o ConnectTimeout=5 $REMOTE_HOST "echo '✅ Подключение успешно'"; then
    echo "❌ Не удается подключиться к серверу $REMOTE_HOST"
    exit 1
fi

# Показываем статус контейнеров
echo ""
echo "📊 Статус контейнеров:"
run_remote "docker compose ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}'"

# Проверяем использование ресурсов
echo ""
echo "💾 Использование ресурсов:"
run_remote "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'"

# Проверяем место на диске
echo ""
echo "💿 Место на диске:"
ssh $REMOTE_HOST "df -h | grep -E '(Filesystem|/$)'"

# Проверяем логи последних ошибок
echo ""
echo "📝 Последние ошибки в логах (если есть):"
echo "--- Backend ---"
if run_remote "docker compose logs --tail=20 backend | grep -i error || echo 'Ошибок не найдено'"; then :; fi
echo "--- Frontend ---"  
if run_remote "docker compose logs --tail=20 frontend | grep -i error || echo 'Ошибок не найдено'"; then :; fi

# Проверяем доступность API
echo ""
echo "🌐 Проверка доступности API..."
if curl -s -o /dev/null -w "%{http_code}" "$PROD_URL/api/health/" | grep -q "200"; then
    echo "✅ API доступен: $PROD_URL/api/health/"
else
    echo "❌ API недоступен: $PROD_URL/api/health/"
fi

# Проверяем доступность frontend
echo ""
echo "🎨 Проверка доступности frontend..."
if curl -s -o /dev/null -w "%{http_code}" "$PROD_URL/" | grep -q "200"; then
    echo "✅ Frontend доступен: $PROD_URL/"
else
    echo "❌ Frontend недоступен: $PROD_URL/"
fi

echo ""
echo "✅ Проверка завершена!"
echo "🌐 Система: $PROD_URL" 