"""
URL маршруты для API управления хранилищами
"""

from django.urls import path
from . import api

app_name = 'storage_management'

urlpatterns = [
    path('', api.storage_overview, name='storage_overview'),
    path('summary/', api.storage_summary, name='storage_summary'),
    # Ячейки хранения (Storage)
    path('storages/', api.list_storages, name='list_storages'),
    path('storages/create/', api.create_storage, name='create_storage'),
    path('storages/<int:storage_id>/', api.get_storage, name='get_storage'),
    path('storages/<int:storage_id>/update/', api.update_storage, name='update_storage'),
    path('storages/<int:storage_id>/delete/', api.delete_storage, name='delete_storage'),
    
    # Боксы хранения (StorageBox)
    path('boxes/', api.list_storage_boxes, name='list_storage_boxes'),
    path('boxes/create/', api.create_storage_box, name='create_storage_box'),
    path('boxes/<str:box_id>/', api.get_storage_box, name='get_storage_box'),
    path('boxes/<str:box_id>/detail/', api.storage_box_details, name='storage_box_details'),
    path('boxes/<str:box_id>/update/', api.update_storage_box, name='update_storage_box'),
    path('boxes/<str:box_id>/delete/', api.delete_storage_box, name='delete_storage_box'),
    
    # Валидация данных
    path('storages/validate/', api.validate_storage, name='validate_storage'),
    
    # Операции с ячейками
    path('boxes/<str:box_id>/cells/', api.get_box_cells, name='get_box_cells'),
    path('boxes/<str:box_id>/cells/<str:cell_id>/assign/', api.assign_cell, name='assign_cell'),
    path('boxes/<str:box_id>/cells/<str:cell_id>/clear/', api.clear_cell, name='clear_cell'),
    path('boxes/<str:box_id>/cells/bulk-assign/', api.bulk_assign_cells, name='bulk_assign_cells'),
]
