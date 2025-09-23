"""
URL маршруты для API управления образцами
"""

from django.urls import path
from . import api

app_name = 'sample_management'

urlpatterns = [
    # Список образцов с поиском и фильтрацией
    path('samples/', api.list_samples, name='list_samples'),
    
    # CRUD операции для образцов
    path('samples/create/', api.create_sample, name='create_sample'),
    path('samples/<int:sample_id>/', api.get_sample, name='get_sample'),
    path('samples/<int:sample_id>/update/', api.update_sample, name='update_sample'),
    path('samples/<int:sample_id>/delete/', api.delete_sample, name='delete_sample'),
    
    # Валидация данных образца
    path('samples/validate/', api.validate_sample, name='validate_sample'),
]