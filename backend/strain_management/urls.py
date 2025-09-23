"""
URL маршруты для API управления штаммами
"""

from django.urls import path
from . import api

app_name = 'strain_management'

urlpatterns = [
    # Список штаммов с поиском и пагинацией
    path('strains/', api.list_strains, name='list_strains'),
    
    # CRUD операции для штаммов
    path('strains/create/', api.create_strain, name='create_strain'),
    path('strains/<int:strain_id>/', api.get_strain, name='get_strain'),
    path('strains/<int:strain_id>/update/', api.update_strain, name='update_strain'),
    path('strains/<int:strain_id>/delete/', api.delete_strain, name='delete_strain'),
    
    # Валидация данных штамма
    path('strains/validate/', api.validate_strain, name='validate_strain'),
]