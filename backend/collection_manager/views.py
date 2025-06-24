from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db import connection
import json
import logging

from .models import Strain, Sample, ReferenceSource, ReferenceLocation, StorageBox, StorageCell

logger = logging.getLogger(__name__)

# Health Check endpoint для CI/CD
def health_check(request):
    """Health check endpoint для мониторинга состояния API"""
    try:
        # Проверка подключения к базе данных
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        # Подсчет основных записей
        strains_count = Strain.objects.count()
        samples_count = Sample.objects.count()
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'counts': {
                'strains': strains_count,
                'samples': samples_count
            },
            'version': '1.0.0'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)

# Create your views here.
