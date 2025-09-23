"""
URL маршруты для API аудита и логирования
"""

from django.urls import path
from . import api

app_name = 'audit_logging'

urlpatterns = [
    # Журнал изменений
    path('change-logs/', api.list_change_logs, name='list_change_logs'),
    path('change-logs/create/', api.create_change_log, name='create_change_log'),
    path('change-logs/<int:log_id>/', api.get_change_log, name='get_change_log'),
    
    # История объектов
    path('object-history/', api.get_object_history, name='get_object_history'),
    
    # Активность пользователей
    path('user-activity/<int:user_id>/', api.get_user_activity, name='get_user_activity'),
    
    # Пакетные операции
    path('batch-log/', api.create_batch_log, name='create_batch_log'),
    path('batch/<str:batch_id>/', api.get_batch_operations, name='get_batch_operations'),
    
    # Статистика аудита
    path('statistics/', api.get_audit_stats, name='get_audit_stats'),
    
    # Валидация данных
    path('validate/', api.validate_change_log, name='validate_change_log'),
]