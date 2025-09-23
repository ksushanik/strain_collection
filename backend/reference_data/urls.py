"""
URL маршруты для API справочных данных
"""

from django.urls import path
from . import api

urlpatterns = [
    path('', api.get_reference_data, name='get_reference_data'),
    path('source-types/', api.get_source_types, name='get_source_types'),
    path('organism-names/', api.get_organism_names, name='get_organism_names'),
]