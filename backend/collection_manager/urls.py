"""
URL маршруты для API collection_manager с валидацией Pydantic
"""

from django.urls import path
from . import api

urlpatterns = [
    # Основные endpoint'ы
    path("", api.api_status, name="api_status"),
    path("health/", api.api_health, name="api_health"),
    path("stats/", api.api_stats, name="api_stats"),
    path("analytics/", api.analytics_data, name="analytics_data"),
]

