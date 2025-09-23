"""
URL маршруты для API аудита и логирования
"""

from django.urls import path
from . import api

app_name = 'audit_logging'

urlpatterns = [
    # Журнал изменений
    path('logs/', api.list_change_logs, name='list_change_logs'),
    path('logs/create/', api.create_change_log, name='create_change_log'),
    path('logs/<int:log_id>/', api.get_change_log, name='get_change_log'),
    
    # История объектов
    path('history/<str:content_type>/<int:object_id>/', api.get_object_history, name='get_object_history'),
    
    # Пакетные операции
    path('batch/<str:batch_id>/', api.get_batch_operations, name='get_batch_operations'),
    
    # Статистика аудита
    path('stats/', api.get_audit_stats, name='get_audit_stats'),
    
    # Валидация данных
    path('logs/validate/', api.validate_change_log, name='validate_change_log'),
]