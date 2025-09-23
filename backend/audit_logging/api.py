"""
API endpoints для аудита и логирования
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from .models import ChangeLog

logger = logging.getLogger(__name__)


class ChangeLogSchema(BaseModel):
    """Схема для записей журнала изменений"""

    id: int = Field(ge=1, description="ID записи")
    content_type: str = Field(description="Тип контента")
    object_id: int = Field(ge=1, description="ID объекта")
    action: str = Field(description="Действие")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Старые значения")
    new_values: Optional[Dict[str, Any]] = Field(None, description="Новые значения")
    user_info: Optional[str] = Field(None, description="Информация о пользователе")
    ip_address: Optional[str] = Field(None, description="IP адрес")
    user_agent: Optional[str] = Field(None, description="User Agent")
    comment: Optional[str] = Field(None, description="Комментарий")
    batch_id: Optional[str] = Field(None, description="ID пакета операций")
    timestamp: datetime = Field(description="Время изменения")

    class Config:
        from_attributes = True


class CreateChangeLogSchema(BaseModel):
    """Схема для создания записи в журнале изменений"""
    
    content_type: str = Field(min_length=1, max_length=50, description="Тип контента")
    object_id: int = Field(ge=1, description="ID объекта")
    action: str = Field(min_length=1, max_length=20, description="Действие")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Старые значения")
    new_values: Optional[Dict[str, Any]] = Field(None, description="Новые значения")
    user_info: Optional[str] = Field(None, max_length=200, description="Информация о пользователе")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP адрес")
    user_agent: Optional[str] = Field(None, max_length=500, description="User Agent")
    comment: Optional[str] = Field(None, max_length=1000, description="Комментарий")
    batch_id: Optional[str] = Field(None, max_length=100, description="ID пакета операций")
    
    @field_validator("content_type", "action")
    @classmethod
    def validate_required_fields(cls, v: str) -> str:
        return v.strip()

    @field_validator("user_info", "ip_address", "user_agent", "comment", "batch_id")
    @classmethod
    def validate_optional_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


@api_view(['GET'])
def list_change_logs(request):
    """Список записей журнала изменений с фильтрацией"""
    try:
        page = max(1, int(request.GET.get('page', 1)))
        limit = max(1, min(int(request.GET.get('limit', 100)), 1000))
        offset = (page - 1) * limit
        
        # Фильтры
        content_type = request.GET.get('content_type', '').strip()
        object_id = request.GET.get('object_id')
        action = request.GET.get('action', '').strip()
        user_info = request.GET.get('user_info', '').strip()
        batch_id = request.GET.get('batch_id', '').strip()
        
        # Фильтр по дате
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        # Поиск
        search_query = request.GET.get('search', '').strip()
        
        queryset = ChangeLog.objects.all().order_by('-timestamp')
        
        # Применяем фильтры
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        if object_id:
            try:
                queryset = queryset.filter(object_id=int(object_id))
            except ValueError:
                pass
        
        if action:
            queryset = queryset.filter(action=action)
        
        if user_info:
            queryset = queryset.filter(user_info__icontains=user_info)
        
        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)
        
        # Фильтр по дате
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__gte=date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__lte=date_to_obj)
            except ValueError:
                pass
        
        # Поиск
        if search_query:
            queryset = queryset.filter(
                Q(comment__icontains=search_query) |
                Q(user_info__icontains=search_query) |
                Q(batch_id__icontains=search_query)
            )
        
        total_count = queryset.count()
        logs = queryset[offset:offset + limit]
        
        data = [ChangeLogSchema.model_validate(log).model_dump() for log in logs]
        
        return Response({
            'logs': data,
            'total': total_count,
            'page': page,
            'limit': limit,
            'has_next': offset + limit < total_count,
            'has_prev': page > 1,
            'filters': {
                'content_type': content_type,
                'object_id': object_id,
                'action': action,
                'user_info': user_info,
                'batch_id': batch_id,
                'date_from': date_from,
                'date_to': date_to,
                'search': search_query
            }
        })
        
    except Exception as e:
        logger.error(f"Error in list_change_logs: {e}")
        return Response(
            {'error': f'Ошибка получения журнала изменений: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_change_log(request, log_id):
    """Получение записи журнала по ID"""
    try:
        log = ChangeLog.objects.get(id=log_id)
        data = ChangeLogSchema.model_validate(log).model_dump()
        return Response(data)
    except ChangeLog.DoesNotExist:
        return Response(
            {'error': f'Запись журнала с ID {log_id} не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in get_change_log: {e}")
        return Response(
            {'error': f'Ошибка получения записи журнала: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@csrf_exempt
def create_change_log(request):
    """Создание записи в журнале изменений"""
    try:
        validated_data = CreateChangeLogSchema.model_validate(request.data)
        
        # Создаем запись в журнале
        log = ChangeLog.objects.create(
            content_type=validated_data.content_type,
            object_id=validated_data.object_id,
            action=validated_data.action,
            old_values=validated_data.old_values,
            new_values=validated_data.new_values,
            user_info=validated_data.user_info,
            ip_address=validated_data.ip_address,
            user_agent=validated_data.user_agent,
            comment=validated_data.comment,
            batch_id=validated_data.batch_id
        )
        
        logger.info(f"Created change log: {log.content_type} {log.action} for object {log.object_id}")
        
        return Response({
            'id': log.id,
            'content_type': log.content_type,
            'object_id': log.object_id,
            'action': log.action,
            'timestamp': log.timestamp,
            'message': 'Запись в журнале изменений создана'
        }, status=status.HTTP_201_CREATED)
    
    except ValidationError as e:
        return Response({
            'error': 'Ошибки валидации данных',
            'details': e.errors()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Unexpected error in create_change_log: {e}")
        return Response({
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_object_history(request, content_type, object_id):
    """Получение истории изменений для конкретного объекта"""
    try:
        logs = ChangeLog.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).order_by('-timestamp')
        
        data = [ChangeLogSchema.model_validate(log).model_dump() for log in logs]
        
        return Response({
            'history': data,
            'content_type': content_type,
            'object_id': object_id,
            'total': len(data)
        })
        
    except Exception as e:
        logger.error(f"Error in get_object_history: {e}")
        return Response(
            {'error': f'Ошибка получения истории объекта: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_batch_operations(request, batch_id):
    """Получение всех операций в рамках одного пакета"""
    try:
        logs = ChangeLog.objects.filter(batch_id=batch_id).order_by('timestamp')
        
        data = [ChangeLogSchema.model_validate(log).model_dump() for log in logs]
        
        return Response({
            'operations': data,
            'batch_id': batch_id,
            'total': len(data)
        })
        
    except Exception as e:
        logger.error(f"Error in get_batch_operations: {e}")
        return Response(
            {'error': f'Ошибка получения операций пакета: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_audit_stats(request):
    """Получение статистики аудита"""
    try:
        # Статистика за последние 30 дней
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        recent_logs = ChangeLog.objects.filter(timestamp__gte=thirty_days_ago)
        
        # Группировка по типам действий
        action_stats = {}
        for action_choice in ChangeLog.ACTION_CHOICES:
            action = action_choice[0]
            count = recent_logs.filter(action=action).count()
            action_stats[action] = count
        
        # Группировка по типам контента
        content_type_stats = {}
        for content_type_choice in ChangeLog.CONTENT_TYPE_CHOICES:
            content_type = content_type_choice[0]
            count = recent_logs.filter(content_type=content_type).count()
            content_type_stats[content_type] = count
        
        # Общая статистика
        total_logs = ChangeLog.objects.count()
        recent_logs_count = recent_logs.count()
        
        return Response({
            'total_logs': total_logs,
            'recent_logs_count': recent_logs_count,
            'period_days': 30,
            'action_stats': action_stats,
            'content_type_stats': content_type_stats,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in get_audit_stats: {e}")
        return Response(
            {'error': f'Ошибка получения статистики аудита: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@csrf_exempt
def validate_change_log(request):
    """Валидация данных записи журнала без сохранения"""
    try:
        validated_data = CreateChangeLogSchema.model_validate(request.data)
        return Response({
            'valid': True,
            'data': validated_data.model_dump(),
            'message': 'Данные записи журнала валидны'
        })
    except ValidationError as e:
        return Response({
            'valid': False,
            'errors': e.errors(),
            'message': 'Ошибки валидации данных'
        }, status=status.HTTP_400_BAD_REQUEST)