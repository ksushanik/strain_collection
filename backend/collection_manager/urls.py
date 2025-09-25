"""
URL маршруты для API collection_manager с валидацией Pydantic
"""

from django.urls import path
from . import api

urlpatterns = [
    # Основные endpoint'ы
    path('', api.api_status, name='api_status'),
    path('health/', api.api_health, name='api_health'),
    path('stats/', api.api_stats, name='api_stats'),
    path('analytics/', api.analytics_data, name='analytics_data'),
    path('reference-data/', api.get_reference_data, name='get_reference_data'),
    path('reference-data/source-types/', api.get_source_types, name='get_source_types'),
    path('reference-data/organism-names/', api.get_organism_names, name='get_organism_names'),
    
    # CRUD операции с боксами
    path('reference-data/boxes/', api.get_boxes, name='get_boxes'),
    path('reference-data/boxes/create/', api.create_box, name='create_box'),
    path('reference-data/boxes/<str:box_id>/', api.get_box, name='get_box'),
    path('reference-data/boxes/<str:box_id>/detail/', api.get_box_detail, name='get_box_detail'),
    path('reference-data/boxes/<str:box_id>/update/', api.update_box, name='update_box'),
    path('reference-data/boxes/<str:box_id>/delete/', api.delete_box, name='delete_box'),
    
    # Операции с ячейками
    path('reference-data/boxes/<str:box_id>/cells/', api.get_box_cells, name='get_box_cells'),
    path('reference-data/boxes/<str:box_id>/cells/<str:cell_id>/assign/', api.assign_cell, name='assign_cell'),
    path('reference-data/boxes/<str:box_id>/cells/<str:cell_id>/clear/', api.clear_cell, name='clear_cell'),
    path('reference-data/boxes/<str:box_id>/cells/bulk-assign/', api.bulk_assign_cells, name='bulk_assign_cells'),
    
    # Работа со штаммами - перенесено в strain_management.urls
    
    # Работа с образцами - перенесено в sample_management.urls
    
    # Массовые операции - перенесены в соответствующие модули
    
    # Работа с хранилищами
    path('storage/', api.list_storage, name='list_storage'),
    path('storage/summary/', api.list_storage_summary, name='list_storage_summary'),
    path('storage/box/<str:box_id>/', api.get_box_details, name='get_box_details'),
]