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
    
    # Работа со штаммами
    path('strains/', api.list_strains, name='list_strains'),
    path('strains/create/', api.create_strain, name='create_strain'),
    path('strains/<int:strain_id>/', api.get_strain, name='get_strain'),
    path('strains/<int:strain_id>/update/', api.update_strain, name='update_strain'),
    path('strains/<int:strain_id>/delete/', api.delete_strain, name='delete_strain'),
    path('strains/validate/', api.validate_strain, name='validate_strain'),
    
    # Работа с образцами
    path('samples/', api.list_samples, name='list_samples'),
    path('samples/create/', api.create_sample, name='create_sample'),
    path('samples/<int:sample_id>/', api.get_sample, name='get_sample'),
    path('samples/<int:sample_id>/update/', api.update_sample, name='update_sample'),
    path('samples/<int:sample_id>/delete/', api.delete_sample, name='delete_sample'),
    path('samples/<int:sample_id>/photos/', api.upload_sample_photos, name='upload_sample_photos'),
    path('samples/<int:sample_id>/photos/<int:photo_id>/', api.delete_sample_photo, name='delete_sample_photo'),
    path('samples/validate/', api.validate_sample, name='validate_sample'),
    
    # Массовые операции с образцами
    path('samples/bulk-delete/', api.bulk_delete_samples, name='bulk_delete_samples'),
    path('samples/bulk-update/', api.bulk_update_samples, name='bulk_update_samples'),
    path('samples/export/', api.bulk_export_samples, name='bulk_export_samples'),
    
    # Массовые операции со штаммами
    path('strains/bulk-delete/', api.bulk_delete_strains, name='bulk_delete_strains'),
    path('strains/bulk-update/', api.bulk_update_strains, name='bulk_update_strains'),
    path('strains/export/', api.bulk_export_strains, name='bulk_export_strains'),
    
    # Работа с хранилищами
    path('storage/', api.list_storage, name='list_storage'),
    path('storage/summary/', api.list_storage_summary, name='list_storage_summary'),
    path('storage/box/<str:box_id>/', api.get_box_details, name='get_box_details'),
] 