#!/bin/sh

# Выход из скрипта при любой ошибке
set -e

echo "🔄 Ожидание готовности базы данных..."
# healthcheck в docker-compose уже выполнил эту роль, но дополнительная проверка не повредит
# Можно добавить здесь wait-for-it.sh или аналогичный скрипт для большей надежности

echo "✅ Применение миграций базы данных..."
python manage.py migrate

echo "✅ Сбор статических файлов..."
python manage.py collectstatic --noinput --clear

DB_COUNT=$(python manage.py shell -c 'from collection_manager.models import Strain; print(Strain.objects.count())')

if [ "$DB_COUNT" -eq 0 ]; then
  echo "🤔 База данных пуста. Запускаю первоначальный импорт..."
  python manage.py import_csv_data --table=all --force
  echo "✅ Первоначальный импорт данных завершен"
else
  echo "✅ База данных уже содержит данные. Импорт пропущен."
fi

echo "🚀 Запуск Gunicorn сервера..."
# exec заменяет текущий процесс (sh) на gunicorn, что правильно для Docker
exec gunicorn --bind 0.0.0.0:8000 --workers 3 --worker-class gthread --threads 2 --worker-connections 1000 --max-requests 1000 --max-requests-jitter 100 --timeout 30 --keep-alive 2 --access-logfile /dev/stdout --error-logfile /dev/stderr --log-level info strain_tracker_project.wsgi:application
