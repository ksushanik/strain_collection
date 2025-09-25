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
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.openapi import AutoSchema

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
    created_at: datetime = Field(description="Время изменения")

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


@extend_schema(
    operation_id="audit_change_logs_list",
    summary="Список записей журнала изменений",
    description="Получение списка записей журнала изменений с фильтрацией",
    parameters=[
        OpenApiParameter(name='content_type', type=str, description='Тип контента'),
        OpenApiParameter(name='object_id', type=int, description='ID объекта'),
        OpenApiParameter(name='action', type=str, description='Тип действия'),
        OpenApiParameter(name='page', type=int, description='Номер страницы'),
        OpenApiParameter(name='limit', type=int, description='Количество элементов на странице'),
    ],
    responses={
        200: OpenApiResponse(description="Список записей журнала"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['GET'])
def list_change_logs(request):
    """Список записей журнала изменений с фильтрацией"""
    try:
        queryset = ChangeLog.objects.all()
        
        # Фильтрация по типу контента
        content_type = request.GET.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        # Фильтрация по ID объекта
        object_id = request.GET.get('object_id')
        if object_id:
            try:
                object_id = int(object_id)
                queryset = queryset.filter(object_id=object_id)
            except ValueError:
                return Response(
                    {'error': 'object_id должен быть числом'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Фильтрация по действию
        action = request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Фильтрация по пользователю
        user_info = request.GET.get('user_info')
        if user_info:
            queryset = queryset.filter(user_info__icontains=user_info)
        
        # Фильтрация по batch_id
        batch_id = request.GET.get('batch_id')
        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)
        
        # Фильтрация по дате
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        if date_from:
            try:
                date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                queryset = queryset.filter(created_at__gte=date_from)
            except ValueError:
                return Response(
                    {'error': 'Неверный формат date_from'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if date_to:
            try:
                date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                queryset = queryset.filter(created_at__lte=date_to)
            except ValueError:
                return Response(
                    {'error': 'Неверный формат date_to'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Поиск по тексту
        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(comment__icontains=search) |
                Q(user_info__icontains=search) |
                Q(old_values__icontains=search) |
                Q(new_values__icontains=search)
            )
        
        # Сортировка
        queryset = queryset.order_by('-created_at')
        
        # Пагинация
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        logs = queryset[start:end]
        
        # Сериализация
        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'content_type': log.content_type,
                'object_id': log.object_id,
                'action': log.action,
                'old_values': log.old_values,
                'new_values': log.new_values,
                'user_info': log.user_info,
                'ip_address': log.ip_address,
                'comment': log.comment,
                'batch_id': log.batch_id,
                'created_at': log.created_at.isoformat() if log.created_at else None
            })
        
        return Response(data)
        
    except Exception as e:
        logger.error(f"Error in list_change_logs: {e}")
        return Response(
            {'error': f'Ошибка получения журнала изменений: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    operation_id="audit_change_log_detail",
    summary="Получение записи журнала",
    description="Получение записи журнала изменений по ID",
    responses={
        200: OpenApiResponse(description="Запись журнала"),
        404: OpenApiResponse(description="Запись не найдена"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
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
            'created_at': log.created_at.isoformat() if log.created_at else None,
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
def get_object_history(request):
    """Получение истории изменений для конкретного объекта"""
    try:
        content_type = request.GET.get('content_type')
        object_id = request.GET.get('object_id')
        
        if not content_type or not object_id:
            return Response(
                {'error': 'content_type и object_id обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            object_id = int(object_id)
        except ValueError:
            return Response(
                {'error': 'object_id должен быть числом'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logs = ChangeLog.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).order_by('-created_at')
        
        data = [ChangeLogSchema.model_validate(log).model_dump() for log in logs]
        
        return Response(data)
        
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
        logs = ChangeLog.objects.filter(batch_id=batch_id).order_by('created_at')
        
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
        
        recent_logs = ChangeLog.objects.filter(created_at__gte=thirty_days_ago)
        
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
        
        # Получаем последние 10 записей для recent_activity
        recent_activity = ChangeLog.objects.order_by('-created_at')[:10]
        recent_activity_data = [ChangeLogSchema.model_validate(log).model_dump() for log in recent_activity]
        
        return Response({
            'total_changes': total_logs,
            'recent_changes_count': recent_logs_count,
            'period_days': 30,
            'changes_by_action': action_stats,
            'changes_by_table': content_type_stats,
            'recent_activity': recent_activity_data,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in get_audit_stats: {e}")
        return Response(
            {'error': f'Ошибка получения статистики аудита: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_user_activity(request, user_id):
    """Получение активности пользователя"""
    try:
        # Получаем пользователя для поиска по username
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(id=user_id)
            # Ищем записи по username или по ID
            logs = ChangeLog.objects.filter(
                Q(user_info__icontains=user.username) | 
                Q(user_info__icontains=str(user_id))
            ).order_by('-created_at')[:50]
        except User.DoesNotExist:
            # Если пользователь не найден, ищем только по ID
            logs = ChangeLog.objects.filter(user_info__icontains=str(user_id)).order_by('-created_at')[:50]
        
        logs_data = []
        for log in logs:
            logs_data.append({
                'id': log.id,
                'content_type': log.content_type,
                'object_id': log.object_id,
                'action': log.action,
                'timestamp': log.created_at.isoformat(),
                'user_info': log.user_info,
                'comment': log.comment
            })
        
        return Response(logs_data)
    except Exception as e:
        logger.error(f"Ошибка получения активности пользователя {user_id}: {str(e)}")
        return Response(
            {'error': f'Ошибка получения активности пользователя: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@csrf_exempt
def create_batch_log(request):
    """Создание пакетной записи в журнале"""
    try:
        batch_data = request.data
        batch_id = batch_data.get('batch_id')
        operations = batch_data.get('operations', [])
        
        if not batch_id:
            # Генерируем batch_id автоматически
            import uuid
            batch_id = str(uuid.uuid4())
        
        created_logs = []
        for operation in operations:
            log_data = {
                'content_type': operation.get('content_type'),
                'object_id': operation.get('object_id'),
                'action': operation.get('action'),
                'old_values': operation.get('old_values'),
                'new_values': operation.get('new_values'),
                'user_info': operation.get('user_info'),
                'batch_id': batch_id,
                'comment': operation.get('comment')
            }
            
            validated_data = CreateChangeLogSchema.model_validate(log_data)
            change_log = ChangeLog.objects.create(**validated_data.model_dump())
            created_logs.append(change_log.id)
        
        return Response({
            'batch_id': batch_id,
            'created_logs': created_logs,
            'count': len(created_logs),
            'message': f'Создано {len(created_logs)} записей в пакете {batch_id}'
        }, status=status.HTTP_201_CREATED)
        
    except ValidationError as e:
        return Response({
            'error': 'Ошибки валидации данных',
            'details': e.errors()
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Ошибка создания пакетной записи: {str(e)}")
        return Response(
            {'error': f'Ошибка создания пакетной записи: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@csrf_exempt
def validate_change_log(request):
    """Валидация данных записи журнала без сохранения"""
    try:
        validated_data = CreateChangeLogSchema.model_validate(request.data)
        return Response({
            'is_valid': True,
            'data': validated_data.model_dump(),
            'message': 'Данные записи журнала валидны'
        })
    except ValidationError as e:
        return Response({
            'is_valid': False,
            'errors': e.errors(),
            'message': 'Ошибки валидации данных'
        }, status=status.HTTP_400_BAD_REQUEST)