from .settings import *

# Используем SQLite для тестов, чтобы не требовать PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "test_db.sqlite3"),
    }
}

# Отключаем миграции для приложений и используем синхронизацию схемы по моделям
MIGRATION_MODULES = {
    'reference_data': None,
    'sample_management': None,
    'strain_management': None,
    'storage_management': None,
    'collection_manager': None,
    'audit_logging': None,
}

# Ускоряем тесты: отключаем лишние проверки/опции
DEBUG = True
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True

# Уменьшаем пагинацию для тестов
REST_FRAMEWORK["PAGE_SIZE"] = 20