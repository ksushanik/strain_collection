"""
URL Configuration для strain_tracker_project
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def home(request):
    return JsonResponse(
        {
            "project": "Strain Tracker",
            "status": "Running",
            "admin": "/admin/",
            "api": "/api/",
            "docs": "/docs/",
            "redoc": "/redoc/",
            "schema": "/api/schema/",
            "validation": "Pydantic 2.x enabled",
        }
    )


urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    
    # Новые модульные API (более специфичные паттерны первыми)
    path("api/reference/", include("reference_data.urls")),
    path("api/samples/", include("sample_management.urls")),  # More specific pattern first
    path("api/strains/", include("strain_management.urls")),
    path("api/storage/", include("storage_management.urls")),
    path("api/audit/", include("audit_logging.urls")),
    
    # Оригинальное API (для обратной совместимости)
    path("api/", include("collection_manager.urls")),  # General pattern last for backward compatibility
    
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]


# Добавляем поддержку статических файлов для админки
if settings.DEBUG or True:  # Всегда включаем для админки
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )

# Добавляем поддержку медиа файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
