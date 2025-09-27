"""
URL маршруты для API управления образцами
"""

from django.urls import path
from . import api

app_name = 'sample_management'

urlpatterns = [
    # Список образцов с поиском и фильтрацией
    path('', api.list_samples, name='list_samples'),
    
    # CRUD операции для образцов
    path('create/', api.create_sample, name='create_sample'),
    path('<int:sample_id>/', api.get_sample, name='get_sample'),
    path('<int:sample_id>/update/', api.update_sample, name='update_sample'),
    path('<int:sample_id>/delete/', api.delete_sample, name='delete_sample'),
    
    # Валидация данных образца
    path('validate/', api.validate_sample, name='validate_sample'),
    
    # Работа с фотографиями образцов
    path('<int:sample_id>/photos/upload/', api.upload_sample_photos, name='upload_sample_photos'),
    path('<int:sample_id>/photos/<int:photo_id>/delete/', api.delete_sample_photo, name='delete_sample_photo'),
]