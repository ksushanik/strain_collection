#!/bin/bash

# Скрипт для безопасной очистки диска на продакшн сервере
# Использование: ./scripts/cleanup_disk_space.sh [--force]

set -e

REMOTE_HOST="4feb"
REMOTE_DIR="~/strain_ultra_minimal"
FORCE=${1:-""}

echo "🧹 ОЧИСТКА ДИСКА НА ПРОДАКШН СЕРВЕРЕ"
echo "📅 Дата: $(date '+%Y-%m-%d %H:%M:%S')"
echo "🌐 Сервер: $REMOTE_HOST"
echo ""

# Функция для выполнения команд на удаленном сервере
run_remote() {
    local cmd="$1"
    echo "🔧 Выполняю: $cmd"
    ssh $REMOTE_HOST "cd $REMOTE_DIR && $cmd"
}

# Проверяем доступность сервера
echo "🔍 Проверка подключения к серверу..."
if ! ssh -o ConnectTimeout=5 $REMOTE_HOST "echo 'Подключение успешно'" >/dev/null 2>&1; then
    echo "❌ Не удается подключиться к серверу $REMOTE_HOST"
    exit 1
fi

# Показываем текущее состояние диска
echo "📊 Текущее использование диска:"
run_remote "df -h | grep '/dev/vda2'"

echo ""
echo "🔍 Анализ Docker ресурсов:"
run_remote "docker system df"

if [ "$FORCE" != "--force" ]; then
    echo ""
    echo "⚠️  ВНИМАНИЕ: Будут выполнены следующие действия:"
    echo "   1. Удаление неиспользуемых Docker образов"
    echo "   2. Удаление неиспользуемых Docker volumes"
    echo "   3. Очистка Docker build cache"
    echo "   4. Очистка системных логов"
    echo "   5. Очистка кэша пакетов"
    echo ""
    echo "📋 СОХРАНЯТСЯ:"
    echo "   ✅ Все работающие контейнеры"
    echo "   ✅ Образы используемых приложений"
    echo "   ✅ Volumes с данными приложений"
    echo "   ✅ Конфигурационные файлы"
    echo ""
    read -p "Продолжить? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo "❌ Операция отменена"
        exit 0
    fi
fi

echo ""
echo "🚀 Начинаю очистку диска..."

# 1. Удаляем неиспользуемые Docker образы
echo ""
echo "1️⃣ Удаление неиспользуемых Docker образов..."
run_remote "docker image prune -f"

# 2. Удаляем неиспользуемые volumes
echo ""
echo "2️⃣ Удаление неиспользуемых Docker volumes..."
run_remote "docker volume prune -f"

# 3. Очищаем build cache
echo ""
echo "3️⃣ Очистка Docker build cache..."
run_remote "docker builder prune -f"

# 4. Очищаем системные логи (оставляем последние 7 дней)
echo ""
echo "4️⃣ Очистка системных логов..."
run_remote "sudo journalctl --vacuum-time=7d" || echo "⚠️ Не удалось очистить journalctl (требуются права sudo)"

# 5. Очищаем кэш пакетов
echo ""
echo "5️⃣ Очистка кэша пакетов..."
run_remote "sudo apt-get clean" || echo "⚠️ Не удалось очистить apt cache (требуются права sudo)"

# 6. Удаляем временные файлы
echo ""
echo "6️⃣ Удаление временных файлов..."
run_remote "sudo find /tmp -type f -atime +7 -delete" || echo "⚠️ Не удалось очистить /tmp (требуются права sudo)"

# 7. Проверяем крупные неиспользуемые образы
echo ""
echo "7️⃣ Проверка крупных образов..."
echo "📋 Образы размером более 500MB:"
run_remote "docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}' | grep -E '[0-9]+\.[0-9]+GB|[5-9][0-9][0-9]MB|[0-9][0-9][0-9][0-9]MB'"

echo ""
echo "📊 Состояние диска после очистки:"
run_remote "df -h | grep '/dev/vda2'"

echo ""
echo "🔍 Docker ресурсы после очистки:"
run_remote "docker system df"

echo ""
echo "✅ Очистка диска завершена!"
echo "💡 Для дополнительной очистки можно:"
echo "   - Удалить старые неиспользуемые образы: docker rmi <image_id>"
echo "   - Проверить большие файлы: du -sh /* | sort -hr"
echo "   - Очистить логи приложений в ~/*/logs/" 