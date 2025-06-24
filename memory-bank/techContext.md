# Технический контекст

## Технологический стек

### Backend
- **Python 3.10+**: Основной язык программирования backend
- **Django 4.2.7**: Web framework для создания API и админ-панели
- **Django REST Framework 3.14.0**: Для создания RESTful API
- **PostgreSQL 15+**: Основная база данных
- **Pydantic 2.11.7**: Валидация данных и схемы
- **psycopg2-binary 2.9.9**: PostgreSQL адаптер для Python

### Frontend
- **Node.js 18+**: JavaScript runtime для разработки
- **React 18+**: UI библиотека для создания интерфейса
- **TypeScript 5+**: Статическая типизация для JavaScript
- **Vite 6.3.5**: Инструмент сборки и dev server
- **React Router**: Клиентская маршрутизация
- **Axios**: HTTP клиент для API запросов

### Дополнительные библиотеки
- **django-cors-headers**: CORS поддержка для API
- **django-extensions**: Полезные расширения Django
- **django-filter**: Фильтрация данных в API
- **python-dotenv**: Управление переменными окружения
- **pandas**: Обработка данных для импорта/экспорта
- **openpyxl**: Работа с Excel файлами

## Структура проекта

### Backend структура
```
backend/
├── strain_tracker_project/          # Django проект
│   ├── settings.py                  # Настройки проекта
│   ├── urls.py                     # URL маршруты
│   ├── wsgi.py                     # WSGI конфигурация
│   └── asgi.py                     # ASGI конфигурация
├── collection_manager/              # Django приложение
│   ├── models.py                   # Модели данных
│   ├── api.py                      # API endpoints
│   ├── admin.py                    # Django admin настройки
│   ├── schemas.py                  # Pydantic схемы валидации
│   ├── migrations/                 # Миграции базы данных
│   └── tests.py                    # Тесты
├── strain_venv/                    # Виртуальное окружение Python
├── manage.py                       # Django management команды
└── requirements.txt                # Python зависимости
```

### Frontend структура
```
frontend/
├── src/
│   ├── components/                 # Переиспользуемые компоненты
│   │   ├── AddStrainForm.tsx      # Форма добавления штамма
│   │   ├── AddSampleForm.tsx      # Форма добавления образца
│   │   ├── BulkOperationsPanel.tsx # Массовые операции
│   │   ├── Navigation.tsx         # Навигационное меню
│   │   ├── Pagination.tsx         # Компонент пагинации
│   │   └── ScrollToTop.tsx        # Управление скроллом
│   ├── pages/                     # Страницы приложения
│   │   ├── Strains.tsx           # Список штаммов
│   │   ├── StrainDetail.tsx      # Детали штамма
│   │   ├── Samples.tsx           # Список образцов
│   │   ├── SampleDetail.tsx      # Детали образца
│   │   ├── Analytics.tsx         # Аналитика
│   │   └── Storage.tsx           # Управление хранилищем
│   ├── services/
│   │   └── api.ts                # HTTP клиент и API вызовы
│   ├── types/
│   │   └── index.ts              # TypeScript типы
│   ├── App.tsx                   # Главный компонент
│   └── main.tsx                  # Точка входа
├── package.json                   # Node.js зависимости
├── tsconfig.json                 # TypeScript конфигурация
├── vite.config.ts               # Vite конфигурация
└── eslint.config.js             # ESLint правила
```

## Среда разработки

### Инструменты разработки
- **VS Code**: Рекомендуемый редактор кода
- **Git**: Система контроля версий
- **Make**: Автоматизация команд через Makefile
- **Docker Compose**: Для развертывания зависимостей (если нужно)

### Настройка окружения

#### Backend setup
```bash
# Создание виртуального окружения
python -m venv strain_venv
source strain_venv/bin/activate  # Linux/Mac
# или strain_venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Настройка базы данных
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Запуск dev server
python manage.py runserver 8000
```

#### Frontend setup
```bash
# Установка зависимостей
npm install

# Запуск dev server
npm run dev  # Порт 3000

# Сборка для продакшена
npm run build
```

### Переменные окружения

#### Backend (.env)
```bash
# Database настройки
DATABASE_NAME=strain_collection
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Django настройки
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS настройки
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

#### Frontend (.env)
```bash
# API конфигурация
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_TITLE=Strain Collection Manager
```

## База данных

### PostgreSQL конфигурация
```sql
-- Создание базы данных
CREATE DATABASE strain_collection;
CREATE USER strain_user WITH PASSWORD 'strain_password';
GRANT ALL PRIVILEGES ON DATABASE strain_collection TO strain_user;

-- Настройки для разработки
ALTER USER strain_user CREATEDB;  -- Для тестов
```

### Миграции
```bash
# Создание новой миграции
python manage.py makemigrations

# Применение миграций
python manage.py migrate

# Откат миграции
python manage.py migrate collection_manager 0001
```

## API конфигурация

### Основные endpoints
```
GET  /api/strains/              # Список штаммов
POST /api/strains/create/       # Создание штамма
GET  /api/strains/{id}/         # Детали штамма
PUT  /api/strains/{id}/update/  # Обновление штамма
DELETE /api/strains/{id}/delete/ # Удаление штамма

GET  /api/samples/              # Список образцов
POST /api/samples/create/       # Создание образца
GET  /api/samples/{id}/         # Детали образца

GET  /api/stats/                # Статистика системы
GET  /api/health/               # Статус системы
```

### CORS настройки
```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

## Автоматизация

### Makefile команды
```makefile
# Основные команды разработки
start-backend:      # Запуск Django server
start-frontend:     # Запуск React dev server
setup-db:          # Настройка базы данных
migrate:           # Применение миграций
test:              # Запуск тестов
lint:              # Проверка кода

# Команды управления данными
import-data:       # Импорт данных из CSV
export-data:       # Экспорт данных
backup-create:     # Создание backup
backup-restore:    # Восстановление из backup

# Команды развертывания
build:             # Сборка frontend
deploy:            # Развертывание приложения
```

## Производительность

### Database индексы
```sql
-- Индексы для быстрого поиска
CREATE INDEX idx_strains_code ON collection_manager_strain(strain_code);
CREATE INDEX idx_strains_species ON collection_manager_strain(species_id);
CREATE INDEX idx_samples_box ON collection_manager_sample(box_id);

-- Полнотекстовый поиск
CREATE INDEX idx_strain_search ON collection_manager_strain 
USING gin(to_tsvector('english', strain_code || ' ' || COALESCE(comments, '')));
```

### Frontend оптимизации
```typescript
// Debounce для поиска
const useDebounce = (value: string, delay: number) => {
    const [debouncedValue, setDebouncedValue] = useState(value);
    
    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);
        
        return () => clearTimeout(handler);
    }, [value, delay]);
    
    return debouncedValue;
};

// Мемоизация компонентов
const StrainRow = React.memo(({ strain, onSelect }) => {
    return <tr onClick={() => onSelect(strain.id)}>...</tr>;
});
```

## Безопасность

### Django настройки
```python
# Безопасность в production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000

# CSRF защита
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
```

### Валидация данных
```python
# Pydantic схемы для всех входящих данных
class StrainCreateSchema(BaseModel):
    strain_code: str = Field(..., min_length=1, max_length=50)
    species_id: int = Field(..., gt=0)
    
    @validator('strain_code')
    def validate_strain_code(cls, v):
        if not re.match(r'^[A-Z0-9-]+$', v):
            raise ValueError('Invalid strain code format')
        return v
```

## Мониторинг и логирование

### Логирование
```python
# Django logging настройки
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'strain_collection.log',
        },
    },
    'loggers': {
        'collection_manager': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Мониторинг производительности
```python
# Middleware для логирования медленных запросов
class SlowRequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        if duration > 0.5:  # Логируем запросы >500ms
            logger.warning(f"Slow request: {request.path} took {duration:.2f}s")
        
        return response
``` 

## Система разработки (Development Environment)

### Архитектура разработки
```yaml
# docker-compose.dev.yml - Только база данных в Docker
version: '3.8'
services:
  postgres:
    image: postgres:14
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: strain_collection
      POSTGRES_USER: strain_user
      POSTGRES_PASSWORD: strain_password
    volumes:
      - postgres_data_dev:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U strain_user -d strain_collection"]
      interval: 10s
      timeout: 5s
      retries: 5

  pgadmin:
    image: dpage/pgadmin4:latest
    ports:
      - "8080:80"
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@strain.local
      PGADMIN_DEFAULT_PASSWORD: admin
    profiles: ["tools"]  # Опционально с --profile tools
```

### Конфигурация разработки
```bash
# .env.dev - Настройки для локальной разработки
DEBUG=True
SECRET_KEY=your-dev-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# База данных (PostgreSQL в Docker)
DATABASE_URL=postgresql://strain_user:strain_password@localhost:5432/strain_collection
DB_HOST=localhost
DB_PORT=5432

# CORS для React на порту 3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOW_ALL_ORIGINS=True

# Логирование
LOG_LEVEL=DEBUG
```

### Команды автоматизации разработки
```makefile
# Первоначальная настройка среды разработки
dev-setup:
	@cp env_dev_example .env.dev
	@cd backend && python3 -m venv strain_venv
	@cd backend && . strain_venv/bin/activate && pip install -r requirements.txt
	@cd frontend && npm install
	@docker-compose -f docker-compose.dev.yml up -d
	@sleep 10
	@cd backend && . strain_venv/bin/activate && python manage.py migrate
	@cd backend && . strain_venv/bin/activate && python scripts/import_data.py

# Запуск компонентов разработки
dev-start:          # Запуск PostgreSQL + инструкции
dev-backend:        # Django локально (порт 8000)
dev-frontend:       # React локально (порт 3000)
dev-stop:           # Остановка PostgreSQL
dev-status:         # Проверка состояния
dev-reset:          # Сброс базы данных
dev-logs:           # Логи PostgreSQL
```

### Преимущества архитектуры разработки

**⚡ Максимальная скорость итерации:**
- Django auto-reload при изменениях Python кода
- React hot-reload при изменениях JavaScript/TypeScript
- Только PostgreSQL в Docker (минимальные накладные расходы)
- Прямой доступ к отладчикам

**🔧 Гибкость разработки:**
- Полный контроль над средой Python
- Возможность использования IDE отладчиков
- Быстрое тестирование изменений
- Легкое профилирование производительности

**🐳 Изоляция инфраструктуры:**
- База данных изолирована в контейнере
- Консистентная среда PostgreSQL
- Легкий сброс/восстановление данных
- Опциональный pgAdmin для управления БД

### Переключение между режимами

**Разработка → Продакшн:**
```bash
make dev-stop       # Остановить PostgreSQL
make quick-deploy   # Полная система в Docker
```

**Продакшн → Разработка:**
```bash
make docker-down    # Остановить Docker систему  
make dev-start      # Вернуться к разработке
```

### Безопасность разработки

**Git безопасность:**
```gitignore
# Файлы конфигурации
.env*
.env.local
.env.production

# Python кэш
__pycache__/
*.pyc
*.pyo

# Логи и backup'ы
logs/
*.log
backups/
*.sql.gz

# Docker volumes
data/postgres/
data/certbot/

# IDE файлы
.vscode/
.idea/
*.swp

# Временные файлы
tmp/
temp/
*_backup.*
```

**Защита конфиденциальных данных:**
- Все .env файлы исключены из git
- Шаблоны конфигурации (env_dev_example, env_example)
- Автоматическая очистка git от __pycache__ и логов
- Backup файлы автоматически игнорируются