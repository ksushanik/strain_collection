#!/bin/bash

# Скрипт для безопасной очистки данных в продакшн базе данных
# Использование: ./scripts/clear_production_data.sh [--force]
# 
# ВНИМАНИЕ: Этот скрипт полностью очищает все данные в базе данных!
# Перед очисткой создается резервная копия.

set -e

REMOTE_HOST="4feb"
REMOTE_DIR="~/strain_ultra_minimal"
FORCE=${1:-""}

echo "🧹 ОЧИСТКА ДАННЫХ ПРОДАКШН БАЗЫ ДАННЫХ"
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

# Проверяем работу backend контейнера
echo "🐳 Проверка работы backend контейнера..."
if ! run_remote "docker compose ps backend | grep -q 'healthy\|running'"; then
    echo "❌ Backend контейнер не запущен или не готов"
    echo "💡 Запустите систему: make deploy-prod"
    exit 1
fi

# Показываем текущее состояние базы данных
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
echo "⚠️  ВНИМАНИЕ: ВСЕ ДАННЫЕ БУДУТ ПОЛНОСТЬЮ УДАЛЕНЫ!"
echo "📋 Будут очищены таблицы:"
echo "   - Штаммы (Strains)"
echo "   - Образцы (Samples)"
echo "   - Хранилище (Storage)"
echo "   - Источники (Sources)"
echo "   - Местоположения (Locations)"
echo "   - Комментарии (Comments)"
echo "   - Примечания (AppendixNotes)"
echo "   - Индексные буквы (IndexLetters)"

# Подтверждение без --force
if [ "$FORCE" != "--force" ]; then
    echo ""
    echo "🛑 Для продолжения введите 'ОЧИСТИТЬ ДАННЫЕ' (точно как написано):"
    read -r confirmation
    if [ "$confirmation" != "ОЧИСТИТЬ ДАННЫЕ" ]; then
        echo "❌ Операция отменена"
        exit 1
    fi
fi

# Создание резервной копии перед очисткой
echo ""
echo "📥 Создание полной резервной копии перед очисткой..."
BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_before_clear_${BACKUP_TIMESTAMP}.sql.gz"

run_remote "docker compose exec db pg_dump -U \$POSTGRES_USER \$POSTGRES_DB | gzip > backups/$BACKUP_NAME"

echo "✅ Резервная копия создана: $BACKUP_NAME"

# Очистка данных
echo ""
echo "🧹 Начинаю очистку данных..."

# Создаем Django команду для очистки данных
run_remote "docker compose exec backend python manage.py shell -c \"
from collection_manager.models import *
from django.db import transaction

print('🔄 Начинаю очистку данных...')

with transaction.atomic():
    # Очищаем в правильном порядке (учитывая внешние ключи)
    sample_count = Sample.objects.count()
    Sample.objects.all().delete()
    print(f'✅ Удалено образцов: {sample_count}')
    
    strain_count = Strain.objects.count()
    Strain.objects.all().delete()
    print(f'✅ Удалено штаммов: {strain_count}')
    
    storage_count = Storage.objects.count()
    Storage.objects.all().delete()
    print(f'✅ Удалено записей хранилища: {storage_count}')
    
    source_count = Source.objects.count()
    Source.objects.all().delete()
    print(f'✅ Удалено источников: {source_count}')
    
    location_count = Location.objects.count()
    Location.objects.all().delete()
    print(f'✅ Удалено местоположений: {location_count}')
    
    comment_count = Comment.objects.count()
    Comment.objects.all().delete()
    print(f'✅ Удалено комментариев: {comment_count}')
    
    appendix_count = AppendixNote.objects.count()
    AppendixNote.objects.all().delete()
    print(f'✅ Удалено примечаний: {appendix_count}')
    
    index_count = IndexLetter.objects.count()
    IndexLetter.objects.all().delete()
    print(f'✅ Удалено индексных букв: {index_count}')

print('🎉 Все данные успешно очищены!')
\""

# Сброс sequences для корректной работы auto-increment
echo ""
echo "🔄 Сброс sequences для корректной работы auto-increment..."
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
            # Сбрасываем sequence на 1
            cursor.execute(f\\\"ALTER SEQUENCE {sequence_name} RESTART WITH 1\\\")
            print(f'✅ Сброшен sequence для {table_name}')

print('🎉 Все sequences сброшены!')
\""

# Проверка результата
echo ""
echo "📊 Проверка результата очистки:"
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
echo "✅ ОЧИСТКА ДАННЫХ ЗАВЕРШЕНА УСПЕШНО!"
echo ""
echo "📋 Что было сделано:"
echo "   1. ✅ Создана резервная копия: $BACKUP_NAME"
echo "   2. ✅ Очищены все таблицы данных"
echo "   3. ✅ Сброшены sequences для корректной работы"
echo ""
echo "💡 Теперь пользователь может добавлять свои данные через веб-интерфейс:"
echo "   🌐 https://culturedb.elcity.ru"
echo "   🔑 Логин в админку: admin / admin123"
echo ""
echo "🔄 Для восстановления данных используйте:"
echo "   ./scripts/restore_production.sh /backups/$BACKUP_NAME"
echo ""
echo "📋 Команды для мониторинга:"
echo "   make status-prod"
echo "   make logs-prod" 