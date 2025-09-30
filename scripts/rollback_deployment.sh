#!/bin/bash

# Скрипт для отката деплоя в случае проблем
# Использование: ./scripts/rollback_deployment.sh [backup_folder]

set -e

REMOTE_HOST="4feb"
REMOTE_DIR="~/strain_ultra_minimal"

echo "🔄 Откат деплоя strain-collection на удаленном сервере..."
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

# Находим последний бэкап
echo "📂 Поиск последнего бэкапа..."
BACKUP_FOLDER=$(ssh $REMOTE_HOST "cd $REMOTE_DIR && ls -1t backups/ | head -1")

if [ -z "$BACKUP_FOLDER" ]; then
    echo "❌ Бэкапы не найдены!"
    exit 1
fi

echo "📦 Найден бэкап: $BACKUP_FOLDER"

# Остановка сервисов
echo "🛑 Остановка сервисов..."
run_remote "docker compose down"

# Восстановление конфигурации
echo "🔄 Восстановление конфигурации из бэкапа..."
run_remote "cp backups/$BACKUP_FOLDER/.env.backup .env"
run_remote "cp backups/$BACKUP_FOLDER/docker-compose.yml.backup docker-compose.yml"

# Возврат к предыдущим образам
echo "🔄 Возврат к предыдущим образам..."
run_remote "docker compose pull"

# Запуск системы
echo "🚀 Запуск системы с восстановленной конфигурацией..."
run_remote "docker compose up -d"

# Ожидание запуска
echo "⏳ Ожидание запуска сервисов (30 сек)..."
sleep 30

# Проверка состояния
echo "🔍 Проверка состояния после отката..."
run_remote "docker compose ps"

echo ""
echo "✅ Откат завершен!"
echo "🌐 Система доступна по адресу: http://89.169.171.236:8081"
echo "📋 Использованный бэкап: $BACKUP_FOLDER"