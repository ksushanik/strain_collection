"""
URL маршруты для API справочных данных
"""

from django.urls import path
from . import api

urlpatterns = [
    path('', api.get_reference_data, name='get_reference_data'),
    path('source-types/', api.get_source_types, name='get_source_types'),
    path('source-categories/', api.get_source_categories, name='get_source_categories'),
    path('organism-names/', api.get_organism_names, name='get_organism_names'),
    path('growth-media/', api.growth_media_list, name='growth_media_list'),
    path('growth-media/<int:pk>/', api.growth_medium_detail, name='growth_medium_detail'),
]