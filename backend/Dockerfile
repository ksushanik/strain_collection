# hadolint ignore=DL3007,DL3008
# --- 1. Этап сборки зависимостей ---
FROM python:3.10-slim as builder
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Добавляем netcat для скрипта wait-for-it и curl для healthcheck
RUN . /etc/os-release && \
    echo "deb https://deb.debian.org/debian ${VERSION_CODENAME} main" > /etc/apt/sources.list && \
    echo "deb https://deb.debian.org/debian ${VERSION_CODENAME}-updates main" >> /etc/apt/sources.list && \
    echo "deb https://deb.debian.org/debian-security ${VERSION_CODENAME}-security main" >> /etc/apt/sources.list && \
    apt-get update -o Acquire::Retries=5 -o Acquire::http::Timeout=30 && \
    apt-get install -y --no-install-recommends ca-certificates gcc libpq-dev netcat-openbsd curl && \
    rm -rf /var/lib/apt/lists/*

# Создаем виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- 2. Финальный образ ---
FROM python:3.10-slim
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Копируем виртуальное окружение с зависимостями из builder'а
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем Gunicorn для запуска приложения
RUN pip install --no-cache-dir gunicorn

# Устанавливаем во второй стейдж тоже, т.к. он нужен для runtime
RUN . /etc/os-release && \
    echo "deb https://deb.debian.org/debian ${VERSION_CODENAME} main" > /etc/apt/sources.list && \
    echo "deb https://deb.debian.org/debian ${VERSION_CODENAME}-updates main" >> /etc/apt/sources.list && \
    echo "deb https://deb.debian.org/debian-security ${VERSION_CODENAME}-security main" >> /etc/apt/sources.list && \
    apt-get update -o Acquire::Retries=5 -o Acquire::http::Timeout=30 && \
    apt-get install -y --no-install-recommends ca-certificates netcat-openbsd curl && \
    rm -rf /var/lib/apt/lists/*

# Копируем и делаем исполняемым скрипт ожидания
COPY ./docker/wait-for-it.sh /usr/local/bin/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh

# Копируем код приложения
COPY . .

# Открываем порт, на котором будет работать gunicorn
EXPOSE 8000

# Команда для запуска приложения
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "strain_tracker_project.wsgi:application"]
