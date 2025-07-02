#!/bin/bash

# Скрипт для работы с миграциями Django на продакшн сервере
# Использование: ./scripts/migrate_production.sh [action]
# Действия:
#   check     - проверить статус миграций
#   apply     - применить неприменённые миграции
#   show      - показать все миграции с статусом
#   rollback  - откатить последнюю миграцию (осторожно!)

set -e

REMOTE_HOST="4feb"
REMOTE_DIR="~/strain_ultra_minimal"
ACTION=${1:-check}

echo "🗄️ Управление миграциями Django на продакшн сервере..."
echo "📅 Дата: $(date '+%Y-%m-%d %H:%M:%S')"
echo "🌐 Сервер: $REMOTE_HOST"
echo "🎯 Действие: $ACTION"
echo ""

# Функция для выполнения команд на удаленном сервере
run_remote() {
    local cmd="$1"
    echo "🔧 Выполняю: $cmd"
    ssh $REMOTE_HOST "cd $REMOTE_DIR && $cmd"
}

# Проверяем доступность сервера и backend контейнера
echo "🔍 Проверка подключения к серверу..."
if ! ssh -o ConnectTimeout=5 $REMOTE_HOST "echo 'OK'" >/dev/null 2>&1; then
    echo "❌ Не удается подключиться к серверу $REMOTE_HOST"
    exit 1
fi

echo "🐳 Проверка работы backend контейнера..."
if ! run_remote "docker compose ps backend | grep -q 'healthy\|running'"; then
    echo "❌ Backend контейнер не запущен или не готов"
    echo "💡 Запустите систему: make deploy-prod или ssh $REMOTE_HOST 'cd $REMOTE_DIR && docker compose up -d'"
    exit 1
fi

case $ACTION in
    "check")
        echo "📋 Проверка статуса миграций..."
        if run_remote "docker compose exec backend python manage.py showmigrations | grep '\[ \]'" 2>/dev/null; then
            echo ""
            echo "⚠️  Найдены неприменённые миграции!"
            echo "💡 Для применения используйте: make migrate-prod или ./scripts/migrate_production.sh apply"
        else
            echo "✅ Все миграции применены"
        fi
        ;;
        
    "show")
        echo "📋 Все миграции с их статусом:"
        run_remote "docker compose exec backend python manage.py showmigrations"
        ;;
        
    "apply")
        echo "📋 Проверка неприменённых миграций..."
        if run_remote "docker compose exec backend python manage.py showmigrations | grep '\[ \]'" 2>/dev/null; then
            echo ""
            echo "📥 Создание резервной копии базы данных..."
            run_remote "docker compose exec db pg_dump -U \$POSTGRES_USER \$POSTGRES_DB > backup_before_migrate_\$(date +%Y%m%d_%H%M%S).sql"
            
            echo "🚀 Применение миграций..."
            run_remote "docker compose exec backend python manage.py migrate"
            
            echo "✅ Миграции успешно применены!"
            echo "📊 Финальный статус миграций:"
            run_remote "docker compose exec backend python manage.py showmigrations | tail -10"
        else
            echo "✅ Все миграции уже применены, изменений не требуется"
        fi
        ;;
        
    "rollback")
        echo "⚠️  ВНИМАНИЕ: Откат миграций может привести к потере данных!"
        echo "📋 Последние применённые миграции:"
        run_remote "docker compose exec backend python manage.py showmigrations | grep '\[X\]' | tail -5"
        echo ""
        echo "❌ Автоматический откат не реализован в целях безопасности"
        echo "💡 Для отката свяжитесь с администратором базы данных"
        echo "📖 Документация: https://docs.djangoproject.com/en/stable/topics/migrations/#reversing-migrations"
        ;;
        
    *)
        echo "❌ Неизвестное действие: $ACTION"
        echo ""
        echo "📖 Доступные действия:"
        echo "  check     - проверить статус миграций (по умолчанию)"
        echo "  apply     - применить неприменённые миграции"
        echo "  show      - показать все миграции с статусом"
        echo "  rollback  - информация об откате миграций"
        echo ""
        echo "📋 Примеры использования:"
        echo "  ./scripts/migrate_production.sh check"
        echo "  ./scripts/migrate_production.sh apply"
        echo "  make migrate-prod"
        exit 1
        ;;
esac

echo ""
echo "✅ Операция завершена!"
echo "🌐 Система: https://culturedb.elcity.ru" 