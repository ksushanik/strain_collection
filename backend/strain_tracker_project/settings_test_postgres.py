from .settings import *

# Отключаем миграции для приложений и используем синхронизацию схемы по моделям
# Это позволяет создавать схему таблиц напрямую по текущим моделям,
# избегая старых миграций, конфликтующих с упрощённой моделью Source
MIGRATION_MODULES = {
    'reference_data': None,
    'sample_management': None,
    'strain_management': None,
    'storage_management': None,
    'collection_manager': None,
    'audit_logging': None,
}

# Тест-ориентированные настройки
DEBUG = True
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True

REST_FRAMEWORK["PAGE_SIZE"] = 20