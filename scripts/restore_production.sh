#!/bin/bash

# Скрипт для восстановления данных из резервной копии на продакшн сервере
# Использование: ./scripts/restore_production.sh <backup_file> [--force]
# Пример: ./scripts/restore_production.sh /backups/backup_before_clear_20250123_143022.sql.gz

set -e

REMOTE_HOST="4feb"
REMOTE_DIR="~/strain_ultra_minimal"
BACKUP_FILE="$1"
FORCE="$2"

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Не указан файл резервной копии"
    echo ""
    echo "📖 Использование: ./scripts/restore_production.sh <backup_file> [--force]"
    echo "📋 Примеры:"
    echo "   ./scripts/restore_production.sh /backups/backup_before_clear_20250123_143022.sql.gz"
    echo "   ./scripts/restore_production.sh /backups/backup_20250123_120000.sql.gz --force"
    echo ""
    echo "📂 Для просмотра доступных backup'ов используйте:"
    echo "   ssh $REMOTE_HOST 'ls -la ~/strain_ultra_minimal/backups/'"
    exit 1
fi

echo "🔄 ВОССТАНОВЛЕНИЕ ДАННЫХ ИЗ РЕЗЕРВНОЙ КОПИИ"
echo "📅 Дата: $(date '+%Y-%m-%d %H:%M:%S')"
echo "🌐 Сервер: $REMOTE_HOST"
echo "📁 Директория: $REMOTE_DIR"
echo "💾 Backup файл: $BACKUP_FILE"
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

# Проверяем существование backup файла
echo "📂 Проверка существования backup файла..."
if ! ssh $REMOTE_HOST "[ -f $REMOTE_DIR/$BACKUP_FILE ]"; then
    echo "❌ Файл $BACKUP_FILE не найден на сервере"
    echo ""
    echo "📂 Доступные backup файлы:"
    ssh $REMOTE_HOST "ls -la $REMOTE_DIR/backups/ | grep -E '\\.sql(\\.gz)?$' | tail -10"
    exit 1
fi

# Проверяем работу backend контейнера
echo "🐳 Проверка работы backend контейнера..."
if ! run_remote "docker compose ps backend | grep -q 'healthy\|running'"; then
    echo "❌ Backend контейнер не запущен или не готов"
    echo "💡 Запустите систему: make deploy-prod"
    exit 1
fi

# Показываем информацию о backup файле
echo "📊 Информация о backup файле:"
ssh $REMOTE_HOST "ls -lh $REMOTE_DIR/$BACKUP_FILE"

# Показываем текущее состояние базы данных
echo ""
echo "📊 Текущее состояние базы данных:"
run_remote "docker compose exec backend python manage.py shell -c \"
from collection_manager.models import *
print(f'Штаммы: {Strain.objects.count()}')
print(f'Образцы: {Sample.objects.count()}')
print(f'Хранилище: {Storage.objects.count()}')
print(f'Источники: {Source.objects.count()}')
print(f'Местоположения: {Location.objects.count()}')
\""

echo ""
echo "⚠️  ВНИМАНИЕ: ТЕКУЩИЕ ДАННЫЕ БУДУТ ЗАМЕНЕНЫ НА ДАННЫЕ ИЗ BACKUP'А!"
echo "📋 Будет выполнено:"
echo "   1. Создание backup'а текущего состояния"
echo "   2. Очистка всех таблиц"
echo "   3. Восстановление данных из backup'а"
echo "   4. Проверка результата"

# Подтверждение без --force
if [ "$FORCE" != "--force" ]; then
    echo ""
    echo "🛑 Для продолжения введите 'ВОССТАНОВИТЬ' (точно как написано):"
    read -r confirmation
    if [ "$confirmation" != "ВОССТАНОВИТЬ" ]; then
        echo "❌ Операция отменена"
        exit 1
    fi
fi

# Создание backup'а текущего состояния
echo ""
echo "📥 Создание backup'а текущего состояния..."
CURRENT_BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CURRENT_BACKUP_NAME="backup_before_restore_${CURRENT_BACKUP_TIMESTAMP}.sql.gz"

run_remote "docker compose exec db pg_dump -U \$POSTGRES_USER \$POSTGRES_DB | gzip > backups/$CURRENT_BACKUP_NAME"

echo "✅ Backup текущего состояния создан: $CURRENT_BACKUP_NAME"

# Восстановление данных
echo ""
echo "🔄 Начинаю восстановление данных..."

# Проверяем формат backup файла (сжатый или обычный)
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "📦 Распаковка сжатого backup файла..."
    RESTORE_CMD="gunzip -c $BACKUP_FILE | docker compose exec -T db psql -U \$POSTGRES_USER \$POSTGRES_DB"
else
    echo "📄 Восстановление из обычного SQL файла..."
    RESTORE_CMD="docker compose exec -T db psql -U \$POSTGRES_USER \$POSTGRES_DB < $BACKUP_FILE"
fi

# Очистка базы данных перед восстановлением
echo "🧹 Очистка базы данных..."
run_remote "docker compose exec backend python manage.py shell -c \"
from collection_manager.models import *
from django.db import transaction

print('🔄 Очищаю базу данных...')

with transaction.atomic():
    Sample.objects.all().delete()
    Strain.objects.all().delete()
    Storage.objects.all().delete()
    Source.objects.all().delete()
    Location.objects.all().delete()
    Comment.objects.all().delete()
    AppendixNote.objects.all().delete()
    IndexLetter.objects.all().delete()

print('✅ База данных очищена')
\""

# Восстановление данных
echo "📥 Восстановление данных из backup'а..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    run_remote "gunzip -c $BACKUP_FILE | docker compose exec -T db psql -U \$POSTGRES_USER \$POSTGRES_DB"
else
    run_remote "docker compose exec -T db psql -U \$POSTGRES_USER \$POSTGRES_DB < $BACKUP_FILE"
fi

# Сброс sequences для корректной работы
echo ""
echo "🔄 Сброс sequences..."
run_remote "docker compose exec backend python manage.py shell -c \"
from django.db import connection
from collection_manager.models import *

models = [Strain, Sample, Storage, Source, Location, Comment, AppendixNote, IndexLetter]

with connection.cursor() as cursor:
    for model in models:
        table_name = model._meta.db_table
        pk_column = model._meta.pk.column
        
        # Получаем имя sequence
        cursor.execute(\\\"SELECT pg_get_serial_sequence(%s, %s)\\\", [table_name, pk_column])
        sequence_name = cursor.fetchone()[0]
        
        if sequence_name:
            # Сбрасываем sequence на MAX(id) + 1
            cursor.execute(f\\\"SELECT setval('{sequence_name}', COALESCE((SELECT MAX({pk_column}) FROM {table_name}), 1) + 1, false)\\\")
            print(f'✅ Сброшен sequence для {table_name}')

print('🎉 Все sequences сброшены!')
\""

# Проверка результата восстановления
echo ""
echo "📊 Проверка результата восстановления:"
run_remote "docker compose exec backend python manage.py shell -c \"
from collection_manager.models import *
print(f'Штаммы: {Strain.objects.count()}')
print(f'Образцы: {Sample.objects.count()}')
print(f'Хранилище: {Storage.objects.count()}')
print(f'Источники: {Source.objects.count()}')
print(f'Местоположения: {Location.objects.count()}')
print(f'Комментарии: {Comment.objects.count()}')
print(f'Примечания: {AppendixNote.objects.count()}')
print(f'Индексные буквы: {IndexLetter.objects.count()}')
\""

echo ""
echo "✅ ВОССТАНОВЛЕНИЕ ДАННЫХ ЗАВЕРШЕНО УСПЕШНО!"
echo ""
echo "📋 Что было сделано:"
echo "   1. ✅ Создан backup текущего состояния: $CURRENT_BACKUP_NAME"
echo "   2. ✅ Очищена база данных"
echo "   3. ✅ Восстановлены данные из: $BACKUP_FILE"
echo "   4. ✅ Сброшены sequences для корректной работы"
echo ""
echo "🌐 Система доступна: https://culturedb.elcity.ru"
echo "🔑 Логин в админку: admin / admin123"
echo ""
echo "📋 Команды для мониторинга:"
echo "   make status-prod"
echo "   make logs-prod" 