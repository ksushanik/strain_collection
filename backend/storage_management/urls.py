"""
URL маршруты для API управления хранилищами
"""

from django.urls import path
from . import api

app_name = 'storage_management'

urlpatterns = [
    # Ячейки хранения (Storage)
    path('storages/', api.list_storages, name='list_storages'),
    path('storages/create/', api.create_storage, name='create_storage'),
    path('storages/<int:storage_id>/', api.get_storage, name='get_storage'),
    path('storages/<int:storage_id>/update/', api.update_storage, name='update_storage'),
    path('storages/<int:storage_id>/delete/', api.delete_storage, name='delete_storage'),
    
    # Боксы хранения (StorageBox)
    path('boxes/', api.list_storage_boxes, name='list_storage_boxes'),
    path('boxes/create/', api.create_storage_box, name='create_storage_box'),
    path('boxes/<int:box_id>/delete/', api.delete_storage_box, name='delete_storage_box'),
    
    # Валидация данных
    path('storages/validate/', api.validate_storage, name='validate_storage'),
]