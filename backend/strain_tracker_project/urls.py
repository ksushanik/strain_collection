"""
URL Configuration для strain_tracker_project
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def home(request):
    return JsonResponse({
        'project': 'Strain Tracker',
        'status': 'Running',
        'admin': '/admin/',
        'api': '/api/',
        'validation': 'Pydantic 2.x enabled'
    })

urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),
    path('api/', include('collection_manager.urls')),
]
