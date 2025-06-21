# --- 1. Этап сборки зависимостей ---
FROM python:3.10-slim as builder

WORKDIR /app

# Добавляем netcat для скрипта wait-for-it и curl для healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev netcat-openbsd curl && \
    rm -rf /var/lib/apt/lists/*

# Создаем виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- 2. Финальный образ ---
FROM python:3.10-slim

WORKDIR /app

# Копируем виртуальное окружение с зависимостями из builder'а
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем Gunicorn для запуска приложения
RUN pip install --no-cache-dir gunicorn

# Устанавливаем во второй стейдж тоже, т.к. он нужен для runtime
RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd curl && rm -rf /var/lib/apt/lists/*

# Копируем и делаем исполняемым скрипт ожидания
COPY ./docker/wait-for-it.sh /usr/local/bin/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh

# Копируем код приложения
COPY . .

# Открываем порт, на котором будет работать gunicorn
EXPOSE 8000

# Команда для запуска приложения
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "strain_tracker_project.wsgi:application"] 