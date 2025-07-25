"""
URL Configuration для strain_tracker_project
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def home(request):
    return JsonResponse(
        {
            "project": "Strain Tracker",
            "status": "Running",
            "admin": "/admin/",
            "api": "/api/",
            "validation": "Pydantic 2.x enabled",
        }
    )


urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/", include("collection_manager.urls")),
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
