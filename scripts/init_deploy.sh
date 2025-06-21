#!/bin/bash

# =============================================================================
# Скрипт автоматической инициализации системы учета штаммов микроорганизмов
# =============================================================================

set -e  # Остановка при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Проверка требований
check_requirements() {
    log "🔍 Проверка системных требований..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        error "Docker не установлен. Пожалуйста, установите Docker."
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose не установлен. Пожалуйста, установите Docker Compose."
    fi
    
    # Проверка прав доступа к Docker
    if ! docker ps &> /dev/null; then
        error "Нет доступа к Docker. Убедитесь, что пользователь добавлен в группу docker."
    fi
    
    log "✅ Все системные требования выполнены"
}

# Создание .env файла
create_env_file() {
    log "📝 Создание конфигурационного файла .env..."
    
    if [ -f .env ]; then
        warn ".env файл уже существует. Пропускаем создание."
        return
    fi
    
    cat > .env << 'EOF'
# =============================================================================
# Конфигурация системы учета штаммов микроорганизмов
# =============================================================================

# База данных PostgreSQL
POSTGRES_DB=strain_db
POSTGRES_USER=strain_user
POSTGRES_PASSWORD=strain_secure_password_2024
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Django настройки
DJANGO_SECRET_KEY=your-very-secure-secret-key-change-in-production
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Безопасность (измените в продакшене)
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1

# Часовой пояс
TZ=Europe/Moscow
EOF
    
    log "✅ Файл .env создан"
}

# Создание необходимых директорий
create_directories() {
    log "📂 Создание необходимых директорий..."
    
    # Создаем директории для данных
    mkdir -p data/certbot/conf
    mkdir -p data/certbot/www
    mkdir -p backups
    mkdir -p logs
    
    # Устанавливаем права доступа
    chmod 755 data backups logs
    chmod 755 data/certbot data/certbot/conf data/certbot/www
    
    log "✅ Директории созданы"
}

# Проверка наличия данных для импорта
check_data_files() {
    log "📊 Проверка файлов данных для импорта..."
    
    required_files=(
        "data/Strains_Table.csv"
        "data/Samples_Table.csv"
        "data/Storage_Table.csv"
        "data/IndexLetters_Table.csv"
        "data/Sources_Table.csv"
        "data/Locations_Table.csv"
        "data/AppendixNotes_Table.csv"
        "data/Comments_Table.csv"
    )
    
    missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        warn "Отсутствуют следующие файлы данных:"
        for file in "${missing_files[@]}"; do
            warn "  - $file"
        done
        warn "Система будет развернута с пустой базой данных."
        warn "Вы можете добавить данные позже через веб-интерфейс или импортировать CSV файлы."
        return 1
    fi
    
    log "✅ Все файлы данных найдены"
    return 0
}

# Сборка и запуск контейнеров
deploy_containers() {
    log "🐳 Сборка и запуск Docker контейнеров..."
    
    # Останавливаем существующие контейнеры
    info "Остановка существующих контейнеров..."
    docker-compose down 2>/dev/null || true
    
    # Собираем образы
    info "Сборка Docker образов..."
    docker-compose build --no-cache
    
    # Запускаем контейнеры
    info "Запуск контейнеров..."
    docker-compose up -d
    
    # Ожидание готовности базы данных
    info "Ожидание готовности базы данных..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose exec -T db pg_isready -U $POSTGRES_USER -d $POSTGRES_DB &>/dev/null; then
            break
        fi
        sleep 2
        ((timeout-=2))
    done
    
    if [ $timeout -le 0 ]; then
        error "База данных не готова к работе. Проверьте логи: docker-compose logs db"
    fi
    
    log "✅ Контейнеры запущены и готовы к работе"
}

# Инициализация базы данных
init_database() {
    log "🗄️  Инициализация базы данных..."
    
    # Применение миграций
    info "Применение миграций Django..."
    docker-compose exec -T backend python manage.py migrate
    
    # Создание суперпользователя (если не существует)
    info "Создание административного пользователя..."
    docker-compose exec -T backend python manage.py shell << 'EOF'
from django.contrib.auth.models import User
import os

username = 'admin'
email = 'admin@strain-system.local'
password = 'admin123'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Создан суперпользователь: {username}")
    print(f"Пароль: {password}")
    print("ВАЖНО: Измените пароль после первого входа!")
else:
    print(f"Суперпользователь {username} уже существует")
EOF
    
    log "✅ База данных инициализирована"
}

# Импорт данных
import_data() {
    if check_data_files; then
        log "📥 Импорт данных из CSV файлов..."
        
        # Импорт всех данных
        docker-compose exec -T backend python manage.py import_csv_data --table=all
        
        # Проверка результатов импорта
        info "Проверка результатов импорта..."
        docker-compose exec -T backend python manage.py shell << 'EOF'
from collection_manager.models import Strain, Sample, Storage

strains_count = Strain.objects.count()
samples_count = Sample.objects.count()
storage_count = Storage.objects.count()

print(f"Импортировано:")
print(f"  - Штаммы: {strains_count}")
print(f"  - Образцы: {samples_count}")
print(f"  - Хранилище: {storage_count}")
EOF
        
        log "✅ Данные успешно импортированы"
    else
        warn "Импорт данных пропущен из-за отсутствующих файлов"
    fi
}

# Проверка состояния системы
health_check() {
    log "🏥 Проверка состояния системы..."
    
    # Проверка контейнеров
    info "Состояние контейнеров:"
    docker-compose ps
    
    # Проверка доступности веб-интерфейса
    info "Проверка доступности веб-интерфейса..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|301\|302"; then
            log "✅ Веб-интерфейс доступен на http://localhost"
            break
        fi
        sleep 2
        ((timeout-=2))
    done
    
    if [ $timeout -le 0 ]; then
        warn "Веб-интерфейс недоступен. Проверьте логи: docker-compose logs nginx"
    fi
    
    # Проверка API
    info "Проверка API..."
    if curl -s http://localhost/api/health | grep -q "healthy"; then
        log "✅ API работает корректно"
    else
        warn "API недоступен. Проверьте логи: docker-compose logs backend"
    fi
}

# Отображение информации о системе
show_system_info() {
    log "📋 Информация о развернутой системе:"
    echo
    echo -e "${BLUE}🌐 Веб-интерфейс:${NC} http://localhost"
    echo -e "${BLUE}🔧 Админ-панель:${NC} http://localhost/admin/"
    echo -e "${BLUE}📡 API документация:${NC} http://localhost/api/"
    echo
    echo -e "${BLUE}👤 Административный доступ:${NC}"
    echo -e "   Логин: ${YELLOW}admin${NC}"
    echo -e "   Пароль: ${YELLOW}admin123${NC}"
    echo -e "   ${RED}⚠️  ВАЖНО: Измените пароль после первого входа!${NC}"
    echo
    echo -e "${BLUE}🗄️  База данных PostgreSQL:${NC}"
    echo -e "   Хост: localhost:5433"
    echo -e "   База: strain_db"
    echo -e "   Пользователь: strain_user"
    echo
    echo -e "${BLUE}📂 Важные директории:${NC}"
    echo -e "   Бэкапы: ./backups/"
    echo -e "   Данные: ./data/"
    echo -e "   Логи: ./logs/"
    echo
    echo -e "${GREEN}🎉 Система успешно развернута!${NC}"
}

# Основная функция
main() {
    echo -e "${BLUE}"
    echo "============================================================================="
    echo "    Автоматическое развертывание системы учета штаммов микроорганизмов"
    echo "============================================================================="
    echo -e "${NC}"
    
    check_requirements
    create_env_file
    create_directories
    deploy_containers
    init_database
    import_data
    health_check
    show_system_info
}

# Запуск скрипта
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi 