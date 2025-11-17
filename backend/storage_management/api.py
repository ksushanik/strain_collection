"""
API endpoints для управления хранилищами
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.openapi import AutoSchema
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional, Dict, List
from datetime import datetime
import logging

from sample_management.models import Sample, SampleStorageAllocation
from collection_manager.utils import log_change

from .models import Storage, StorageBox
from .utils import (
    ensure_cells_for_boxes,
    ensure_storage_cells,
    row_index_to_label,
)
from . import services as storage_services
from .services import StorageServiceError

logger = logging.getLogger(__name__)


LEGACY_DEPRECATIONS = {
    'assign_cell': {
        'message': 'Endpoint /assign/ is deprecated. Use POST /allocate/ with payload {"is_primary": true}.',
        'replacement': '/api/storage/boxes/{box_id}/cells/{cell_id}/allocate/',
    },
    'clear_cell': {
        'message': 'Endpoint /clear/ is deprecated. Use DELETE /unallocate/ instead.',
        'replacement': '/api/storage/boxes/{box_id}/cells/{cell_id}/unallocate/',
    },
    'bulk_assign_cells': {
        'message': 'Endpoint /bulk-assign/ is deprecated. Use /bulk-allocate/ with primary flag.',
        'replacement': '/api/storage/boxes/{box_id}/cells/bulk-allocate/',
    },
}


def _mark_legacy_deprecated(endpoint: str, response: Response, **context) -> Response:
    info = LEGACY_DEPRECATIONS.get(endpoint)
    if not info:
        return response

    message = info.get('message')
    replacement = info.get('replacement')
    logger.warning("Legacy storage endpoint %s called. %s", endpoint, message)

    response['X-Endpoint-Deprecated'] = 'true'
    response['X-Endpoint-Name'] = endpoint
    if message:
        response['X-Endpoint-Deprecated-Message'] = message
    if replacement:
        formatted_replacement = replacement.format(**context)
        response['X-Endpoint-Replacement'] = formatted_replacement
    else:
        formatted_replacement = None

    if isinstance(response.data, dict):
        response.data.setdefault('deprecated', True)
        if message:
            response.data.setdefault('deprecation_message', message)
        if formatted_replacement:
            response.data.setdefault('replacement_endpoint', formatted_replacement)

    return response


def _log_service_changes(request, log_entries):
    """Helper to persist audit records produced by service layer."""
    for entry in log_entries or []:
        try:
            log_change(request=request, **entry.as_kwargs())
        except Exception:  # pragma: no cover - defensive logging guard
            logger.exception("Failed to log storage change via service layer")


def _handle_service_error(error: StorageServiceError) -> Response:
    """Convert service exception to DRF response."""
    payload = error.as_response()
    return Response(payload, status=error.status_code)



def _generate_next_box_id() -> str:
    existing_ids = list(StorageBox.objects.values_list('box_id', flat=True))
    existing_ids += list(Storage.objects.values_list('box_id', flat=True).distinct())
    max_number = 0
    for candidate in existing_ids:
        try:
            number = int(str(candidate).strip())
        except (ValueError, TypeError):
            continue
        if number > max_number:
            max_number = number
    next_number = max_number + 1
    while (
        StorageBox.objects.filter(box_id=str(next_number)).exists()
        or Storage.objects.filter(box_id=str(next_number)).exists()
    ):
        next_number += 1
    return str(next_number)


def _ensure_box_id(box_id: Optional[str]) -> str:
    if box_id:
        normalized = box_id.strip()
        return normalized.upper() if normalized else _generate_next_box_id()
    return _generate_next_box_id()

class StorageSchema(BaseModel):
    """Схема валидации для ячеек хранения (Storage)"""

    id: Optional[int] = Field(None, ge=1, description="ID ячейки")
    box_id: str = Field(min_length=1, max_length=50, description="ID бокса")
    cell_id: str = Field(min_length=1, max_length=10, description="ID ячейки")

    @field_validator("box_id", "cell_id")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        return v.strip().upper()

    class Config:
        from_attributes = True


class CreateStorageSchema(BaseModel):
    """Схема для создания ячейки хранения без ID"""
    
    box_id: str = Field(min_length=1, max_length=50, description="ID бокса")
    cell_id: str = Field(min_length=1, max_length=10, description="ID ячейки")
    
    @field_validator("box_id", "cell_id")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        return v.strip().upper()


class StorageBoxSchema(BaseModel):
    """Схема валидации для боксов хранения (StorageBox)"""

    id: Optional[int] = Field(None, ge=1, description="ID бокса")
    box_id: str = Field(min_length=1, max_length=50, description="Уникальный ID бокса")
    rows: int = Field(ge=1, le=50, description="Количество рядов")
    cols: int = Field(ge=1, le=50, description="Количество колонок")
    description: Optional[str] = Field(None, max_length=500, description="Описание")
    created_at: Optional[datetime] = Field(None, description="Дата создания")

    @field_validator("box_id")
    @classmethod
    def validate_box_id(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    class Config:
        from_attributes = True


class CreateStorageBoxSchema(BaseModel):
    """Schema used to create a storage box. box_id is optional."""

    box_id: Optional[str] = Field(
        default=None, max_length=50, description="Custom box identifier (optional)"
    )
    rows: int = Field(ge=1, le=50, description="Number of rows")
    cols: int = Field(ge=1, le=50, description="Number of columns")
    description: Optional[str] = Field(None, max_length=500, description="Description")

    @field_validator("box_id")
    @classmethod
    def validate_box_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        value = v.strip()
        return value.upper() if value else None

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


class UpdateStorageBoxSchema(BaseModel):
    """Schema for updating storage box metadata."""

    description: Optional[str] = Field(None, max_length=500, description="Description")

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


class AllocationRequestSchema(BaseModel):
    sample_id: int = Field(gt=0, description="ID образца")
    is_primary: bool = Field(default=False, description="Основная ячейка")


class UnallocateRequestSchema(BaseModel):
    sample_id: int = Field(gt=0, description="ID образца")


class StorageSchema(BaseModel):
    """Схема валидации для ячеек хранения (Storage)"""

    id: Optional[int] = Field(None, ge=1, description="ID ячейки")
    box_id: str = Field(min_length=1, max_length=50, description="ID бокса")
    cell_id: str = Field(min_length=1, max_length=10, description="ID ячейки")

    @field_validator("box_id", "cell_id")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        return v.strip().upper()

    class Config:
        from_attributes = True


class CreateStorageSchema(BaseModel):
    """Схема для создания ячейки хранения без ID"""
    
    box_id: str = Field(min_length=1, max_length=50, description="ID бокса")
    cell_id: str = Field(min_length=1, max_length=10, description="ID ячейки")
    
    @field_validator("box_id", "cell_id")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        return v.strip().upper()


class StorageBoxSchema(BaseModel):
    """Схема валидации для боксов хранения (StorageBox)"""

    id: Optional[int] = Field(None, ge=1, description="ID бокса")
    box_id: str = Field(min_length=1, max_length=50, description="Уникальный ID бокса")
    rows: int = Field(ge=1, le=50, description="Количество рядов")
    cols: int = Field(ge=1, le=50, description="Количество колонок")
    description: Optional[str] = Field(None, max_length=500, description="Описание")
    created_at: Optional[datetime] = Field(None, description="Дата создания")

    @field_validator("box_id")
    @classmethod
    def validate_box_id(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    class Config:
        from_attributes = True


@extend_schema(
    operation_id="storage_list_storages",
    summary="List storage slots",
    description="Return paginated list of storage cells with optional search filters",
    parameters=[
        OpenApiParameter(name='page', type=int, description='Page number'),
        OpenApiParameter(name='limit', type=int, description='Items per page (max 1000)'),
        OpenApiParameter(name='search', type=str, description='Search by box_id or cell_id'),
        OpenApiParameter(name='box_id', type=str, description='Filter by box id'),
    ],
    responses={
        200: OpenApiResponse(description="Storage cells list"),
        500: OpenApiResponse(description="Server error"),
    }
)
@api_view(['GET'])
def list_storages(request):
    """Список всех ячеек хранения с поиском и пагинацией"""
    try:
        page = max(1, int(request.GET.get('page', 1)))
        limit = max(1, min(int(request.GET.get('limit', 50)), 1000))
        offset = (page - 1) * limit
        
        # Полнотекстовый поиск
        search_query = request.GET.get('search', '').strip()
        box_id_filter = request.GET.get('box_id', '').strip()
        
        queryset = Storage.objects.all()
        
        if search_query:
            queryset = queryset.filter(
                Q(box_id__icontains=search_query) |
                Q(cell_id__icontains=search_query)
            )
        
        if box_id_filter:
            queryset = queryset.filter(box_id__icontains=box_id_filter)
        
        total_count = queryset.count()
        storages = queryset[offset:offset + limit]
        
        data = []
        for storage in storages:
            storage_data = StorageSchema.model_validate(storage).model_dump()
            data.append(storage_data)
        
        return Response({
            'results': data,
            'count': total_count,
            'page': page,
            'limit': limit,
            'has_next': offset + limit < total_count,
            'has_prev': page > 1
        })
        
    except Exception as e:
        logger.error(f"Error in list_storages: {e}")
        return Response(
            {'error': f'Ошибка получения списка ячеек: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    operation_id="storage_get_storage",
    summary="Получение ячейки хранения",
    description="Получение детальной информации о конкретной ячейке хранения",
    responses={
        200: OpenApiResponse(description="Информация о ячейке хранения"),
        404: OpenApiResponse(description="Ячейка не найдена"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['GET'])
def get_storage(request, storage_id):
    """Получение детальной информации о ячейке хранения"""
    try:
        storage = Storage.objects.get(id=storage_id)
        
        storage_data = StorageSchema.model_validate(storage).model_dump()
        
        return Response(storage_data)
        
    except Storage.DoesNotExist:
        return Response(
            {'error': f'Ячейка с ID {storage_id} не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in get_storage: {e}")
        return Response(
            {'error': f'Ошибка получения ячейки: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    operation_id="storage_create_storage",
    summary="Создание ячейки хранения",
    description="Создание новой ячейки хранения с проверкой уникальности",
    responses={
        201: OpenApiResponse(description="Ячейка успешно создана"),
        400: OpenApiResponse(description="Ошибка валидации данных"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['POST'])
@csrf_exempt
def create_storage(request):
    """Создание новой ячейки хранения"""
    try:
        validated_data = CreateStorageSchema.model_validate(request.data)
        
        # Проверяем уникальность комбинации box_id и cell_id
        if Storage.objects.filter(box_id=validated_data.box_id, cell_id=validated_data.cell_id).exists():
            return Response({
                'error': f'Ячейка с ID "{validated_data.cell_id}" в боксе "{validated_data.box_id}" уже существует'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создаем ячейку
        with transaction.atomic():
            storage = Storage.objects.create(
                box_id=validated_data.box_id,
                cell_id=validated_data.cell_id
            )
            logger.info(f"Created storage: {storage.box_id}-{storage.cell_id} (ID: {storage.id})")
        
        return Response({
            'id': storage.id,
            'box_id': storage.box_id,
            'cell_id': storage.cell_id,
            'message': 'Ячейка хранения успешно создана'
        }, status=status.HTTP_201_CREATED)
    
    except ValidationError as e:
        return Response({
            'error': 'Ошибки валидации данных',
            'details': e.errors()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Unexpected error in create_storage: {e}")
        return Response({
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    operation_id="storage_update_storage",
    summary="Обновление ячейки хранения",
    description="Обновление информации о ячейке хранения",
    responses={
        200: OpenApiResponse(description="Ячейка успешно обновлена"),
        400: OpenApiResponse(description="Ошибка валидации данных"),
        404: OpenApiResponse(description="Ячейка не найдена"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['PUT'])
@csrf_exempt
def update_storage(request, storage_id):
    """Обновление ячейки хранения"""
    try:
        # Получаем ячейку хранения
        try:
            storage = Storage.objects.get(id=storage_id)
        except Storage.DoesNotExist:
            return Response({
                'error': f'Ячейка с ID {storage_id} не найдена'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Валидируем данные
        validated_data = CreateStorageSchema.model_validate(request.data)
        
        # Проверяем уникальность комбинации box_id и cell_id (исключая текущую ячейку)
        if Storage.objects.filter(
            box_id=validated_data.box_id, 
            cell_id=validated_data.cell_id
        ).exclude(id=storage_id).exists():
            return Response({
                'error': f'Ячейка с ID "{validated_data.cell_id}" в боксе "{validated_data.box_id}" уже существует'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Обновление ячейки хранения
        with transaction.atomic():
            storage.box_id = validated_data.box_id
            storage.cell_id = validated_data.cell_id
            storage.save()
            
            logger.info(f"Updated storage: {storage.box_id}-{storage.cell_id} (ID: {storage.id})")
        
        return Response({
            'id': storage.id,
            'box_id': storage.box_id,
            'cell_id': storage.cell_id,
            'message': 'Ячейка хранения успешно обновлена'
        })
    
    except ValidationError as e:
        return Response({
            'error': 'Ошибки валидации данных',
            'details': e.errors()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Unexpected error in update_storage: {e}")
        return Response({
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    operation_id="storage_delete_storage",
    summary="Удаление ячейки хранения",
    description="Удаление ячейки хранения из системы",
    responses={
        200: OpenApiResponse(description="Ячейка успешно удалена"),
        404: OpenApiResponse(description="Ячейка не найдена"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['DELETE'])
@csrf_exempt
def delete_storage(request, storage_id):
    """Удаление ячейки хранения"""
    try:
        # Получаем ячейку хранения
        try:
            storage = Storage.objects.get(id=storage_id)
        except Storage.DoesNotExist:
            return Response({
                'error': f'Ячейка с ID {storage_id} не найдена'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем, есть ли связанные образцы
        from sample_management.models import Sample
        related_samples = Sample.objects.filter(storage_id=storage_id).count()
        if related_samples > 0:
            return Response({
                'error': f'Нельзя удалить ячейку, так как в ней находится {related_samples} образцов',
                'related_samples_count': related_samples
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Сохраняем информацию о ячейке для ответа
        storage_info = {
            'id': storage.id,
            'box_id': storage.box_id,
            'cell_id': storage.cell_id
        }
        
        # Удаляем ячейку
        with transaction.atomic():
            storage.delete()
            logger.info(f"Deleted storage: {storage_info['box_id']}-{storage_info['cell_id']} (ID: {storage_info['id']})")
        
        return Response({
            'message': f"Ячейка '{storage_info['box_id']}-{storage_info['cell_id']}' успешно удалена",
            'deleted_storage': storage_info
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Unexpected error in delete_storage: {e}")
        return Response({
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# API для ящиков хранилища

@extend_schema(
    operation_id="list_storage_boxes",
    summary="Список боксов хранения",
    description="Получение списка всех боксов хранения с пагинацией",
    parameters=[
        OpenApiParameter(name='page', type=int, description='Номер страницы'),
        OpenApiParameter(name='limit', type=int, description='Количество элементов на странице'),
    ],
    responses={
        200: OpenApiResponse(description="Список боксов хранения"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['GET'])
def list_storage_boxes(request):
    """Список всех боксов хранения"""
    try:
        page = max(1, int(request.GET.get('page', 1)))
        limit = max(1, min(int(request.GET.get('limit', 50)), 1000))
        offset = (page - 1) * limit
        
        # Полнотекстовый поиск
        search_query = request.GET.get('search', '').strip()
        
        queryset = StorageBox.objects.all()
        
        if search_query:
            queryset = queryset.filter(
                Q(box_id__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        total_count = queryset.count()
        boxes = list(queryset[offset:offset + limit])

        if boxes:
            ensure_cells_for_boxes(boxes)
        
        data = []
        for box in boxes:
            box_data = {
                'id': box.id,
                'box_id': box.box_id,
                'rows': box.rows,
                'cols': box.cols,
                'description': box.description,
                'created_at': box.created_at.isoformat() if box.created_at else None
            }
            data.append(box_data)
        
        return Response({
            'results': data,
            'count': total_count,
            'page': page,
            'limit': limit,
            'has_next': offset + limit < total_count,
            'has_prev': page > 1
        })
        
    except Exception as e:
        logger.error(f"Error in list_storage_boxes: {e}")
        return Response(
            {'error': f'Ошибка получения списка боксов: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@extend_schema(
    operation_id="create_storage_box",
    summary="Create storage box",
    description="Creates a storage box, generates an identifier and pre-populates child cells",
    responses={
        201: OpenApiResponse(description="Storage box created"),
        400: OpenApiResponse(description="Validation error"),
        500: OpenApiResponse(description="Server error"),
    }
)
@api_view(['POST'])
@csrf_exempt
def create_storage_box(request):
    """Create a new storage box and generate all storage cells."""
    try:
        payload = CreateStorageBoxSchema.model_validate(request.data)
    except ValidationError as exc:
        return Response(
            {
                'error': 'Validation error',
                'details': exc.errors(),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with transaction.atomic():
            box_id = _ensure_box_id(payload.box_id)

            if StorageBox.objects.filter(box_id=box_id).exists() or Storage.objects.filter(box_id=box_id).exists():
                return Response(
                    {'error': f'Storage box with ID "{box_id}" already exists'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            box = StorageBox.objects.create(
                box_id=box_id,
                rows=payload.rows,
                cols=payload.cols,
                description=payload.description,
            )

            cells_created = ensure_storage_cells(box_id, payload.rows, payload.cols)

            log_change(
                request=request,
                content_type='storage',
                object_id=box.id,
                action='CREATE',
                new_values={
                    'box_id': box.box_id,
                    'rows': box.rows,
                    'cols': box.cols,
                    'description': box.description,
                    'cells_created': cells_created,
                },
            )

        return Response(
            {
                'message': f'Storage box "{box.box_id}" created',
                'box_id': box.box_id,
                'box': {
                    'box_id': box.box_id,
                    'rows': box.rows,
                    'cols': box.cols,
                    'description': box.description,
                    'created_at': box.created_at.isoformat() if box.created_at else None,
                    'cells_created': cells_created,
                    'generated_id': payload.box_id is None,
                },
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as exc:
        logger.error(f"Unexpected error in create_storage_box: {exc}")
        return Response(
            {'error': f'Failed to create storage box: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )




@extend_schema(
    operation_id="get_storage_box",
    summary="Get storage box",
    responses={
        200: OpenApiResponse(description="Storage box details"),
        404: OpenApiResponse(description="Storage box not found"),
        500: OpenApiResponse(description="Server error"),
    }
)
@api_view(['GET'])
def get_storage_box(request, box_id):
    """Return storage box metadata along with occupancy statistics."""
    try:
        box = StorageBox.objects.get(box_id=box_id)
    except StorageBox.DoesNotExist:
        return Response({'error': f'Storage box with ID {box_id} not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        total_cells = Storage.objects.filter(box_id=box_id).count()
        occupied_cells = Sample.objects.filter(
            storage__box_id=box_id,
        ).count()
        free_cells = max(total_cells - occupied_cells, 0)

        return Response(
            {
                'box_id': box.box_id,
                'rows': box.rows,
                'cols': box.cols,
                'description': box.description,
                'created_at': box.created_at.isoformat() if box.created_at else None,
                'statistics': {
                    'total_cells': total_cells,
                    'occupied_cells': occupied_cells,
                    'free_cells': free_cells,
                    'occupancy_percentage': round((occupied_cells / total_cells * 100) if total_cells else 0, 1),
                },
            }
        )
    except Exception as exc:
        logger.error(f"Unexpected error in get_storage_box: {exc}")
        return Response({'error': f'Failed to retrieve storage box: {exc}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    operation_id="update_storage_box",
    summary="Update storage box",
    responses={
        200: OpenApiResponse(description="Storage box updated"),
        400: OpenApiResponse(description="Validation error"),
        404: OpenApiResponse(description="Storage box not found"),
        500: OpenApiResponse(description="Server error"),
    }
)
@api_view(['PUT'])
@csrf_exempt
def update_storage_box(request, box_id):
    """Update storage box metadata."""
    try:
        box = StorageBox.objects.get(box_id=box_id)
    except StorageBox.DoesNotExist:
        return Response({'error': f'Storage box with ID {box_id} not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        payload = UpdateStorageBoxSchema.model_validate(request.data)
    except ValidationError as exc:
        return Response(
            {
                'error': 'Validation error',
                'details': exc.errors(),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with transaction.atomic():
            if payload.description is not None:
                box.description = payload.description
            box.save()

            log_change(
                request=request,
                content_type='storage',
                object_id=box.id,
                action='UPDATE',
                new_values={'description': box.description},
            )

        return Response(
            {
                'message': f'Storage box "{box.box_id}" updated',
                'box': {
                    'box_id': box.box_id,
                    'rows': box.rows,
                    'cols': box.cols,
                    'description': box.description,
                    'created_at': box.created_at.isoformat() if box.created_at else None,
                },
            }
        )
    except Exception as exc:
        logger.error(f"Unexpected error in update_storage_box: {exc}")
        return Response(
            {'error': f'Failed to update storage box: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    operation_id="delete_storage_box",
    summary="Delete storage box",
    description="Deletes a storage box. Supports force deletion for occupied cells via ?force=true",
    responses={
        200: OpenApiResponse(description="Storage box deleted"),
        404: OpenApiResponse(description="Storage box not found"),
        400: OpenApiResponse(description="Box contains occupied cells"),
        500: OpenApiResponse(description="Server error"),
    }
)
@api_view(['DELETE'])
@csrf_exempt
def delete_storage_box(request, box_id):
    """Delete storage box by identifier with optional force flag."""
    try:
        try:
            box = StorageBox.objects.get(box_id=box_id)
        except StorageBox.DoesNotExist:
            return Response(
                {'error': f'Storage box with ID {box_id} not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        occupied_cells = Sample.objects.filter(
            storage__box_id=box_id,
            strain_id__isnull=False,
        ).count()
        force_delete = request.GET.get('force', '').lower() == 'true'

        if occupied_cells > 0 and not force_delete:
            return Response(
                {
                    'error': f'Box contains {occupied_cells} occupied cells. Retry with ?force=true to proceed.',
                    'occupied_cells': occupied_cells,
                    'can_force_delete': True,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_cells = Storage.objects.filter(box_id=box_id).count()

        with transaction.atomic():
            if occupied_cells > 0:
                Sample.objects.filter(storage__box_id=box_id).update(storage=None)

            Storage.objects.filter(box_id=box_id).delete()
            box_pk = box.id
            box.delete()

            log_change(
                request=request,
                content_type='storage',
                object_id=box_pk,
                action='DELETE',
                old_values={
                    'box_id': box_id,
                    'total_cells_deleted': total_cells,
                    'occupied_cells_freed': occupied_cells,
                    'force_delete': force_delete,
                },
            )

        return Response(
            {
                'message': f'Storage box {box_id} deleted',
                'statistics': {
                    'cells_deleted': total_cells,
                    'samples_freed': occupied_cells,
                    'force_delete_used': force_delete,
                },
            }
        )
    except Exception as exc:
        logger.error(f"Unexpected error in delete_storage_box: {exc}")
        return Response(
            {'error': f'Failed to delete storage box: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    operation_id="storage_validate_storage",
    summary="Валидация данных ячейки хранения",
    description="Проверка корректности данных ячейки хранения без сохранения",
    responses={
        200: OpenApiResponse(description="Данные валидны"),
        400: OpenApiResponse(description="Ошибка валидации"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['POST'])
@csrf_exempt
def validate_storage(request):
    """Валидация данных хранилища без сохранения"""
    try:
        validated_data = CreateStorageSchema.model_validate(request.data)
        return Response({
            'valid': True,
            'data': validated_data.model_dump(),
            'message': 'Данные хранилища валидны'
        })
    except ValidationError as e:
        return Response({
            'valid': False,
            'errors': e.errors(),
            'message': 'Ошибки валидации данных'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def storage_overview(request):
    snapshot = storage_services.build_storage_snapshot()
    boxes_payload = []

    for box in snapshot['boxes']:
        stats = box['stats']
        cells_payload = []
        for cell in box.get('sorted_cells', []):
            primary = cell.get('primary_sample')
            cells_payload.append({
                'cell_id': cell.get('cell_id'),
                'storage_id': cell.get('storage_id'),
                'occupied': cell.get('occupied'),
                'sample_id': primary.get('sample_id') if primary else None,
                'strain_code': primary.get('strain_code') if primary else None,
                'is_free_cell': not cell.get('occupied'),
            })

        boxes_payload.append(
            {
                'box_id': box.get('box_id'),
                'rows': box.get('rows'),
                'cols': box.get('cols'),
                'description': box.get('description'),
                'cells': cells_payload,
                'occupied': stats['occupied_cells'],
                'total': stats['total_cells'],
                'total_cells': stats['total_cells'],
                'free_cells': stats['free_cells'],
            }
        )

    totals = snapshot['totals']
    return Response({
        'boxes': boxes_payload,
        'total_boxes': totals['total_boxes'],
        'total_cells': totals['total_cells'],
        'occupied_cells': totals['occupied_cells'],
        'free_cells': totals['free_cells'],
    })


@extend_schema(
    operation_id="storage_summary",
    summary="Сводка по хранилищу",
    description="Получение агрегированной информации о занятости ячеек по боксам",
    responses={
        200: OpenApiResponse(description="Сводка по хранилищу"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['GET'])
def storage_summary(request):
    snapshot = storage_services.build_storage_snapshot()
    boxes_payload = []
    for box in snapshot['boxes']:
        stats = box['stats']
        boxes_payload.append({
            'box_id': box.get('box_id'),
            'occupied': stats['occupied_cells'],
            'total': stats['total_cells'],
            'free_cells': stats['free_cells'],
        })

    totals = snapshot['totals']
    return Response({
        'boxes': boxes_payload,
        'total_boxes': totals['total_boxes'],
        'total_cells': totals['total_cells'],
        'occupied_cells': totals['occupied_cells'],
        'free_cells': totals['free_cells'],
    })





@extend_schema(
    operation_id="storage_box_details",
    summary="Storage box details grid",
    responses={
        200: OpenApiResponse(description="Grid of storage cells"),
        404: OpenApiResponse(description="Storage box not found"),
        500: OpenApiResponse(description="Server error"),
    }
)
@api_view(['GET'])
@csrf_exempt
def storage_box_details(request, box_id):
    box_key = str(box_id).strip().upper()
    snapshot = storage_services.build_storage_snapshot([box_key])
    box_map = snapshot.get('box_map', {})
    box_data = box_map.get(box_key)

    if box_data is None:
        return Response({'error': f'Storage box with ID {box_id} not found'}, status=status.HTTP_404_NOT_FOUND)

    stats = box_data['stats']
    if stats['total_cells'] == 0:
        return Response({'error': f'No cells registered for box {box_id}'}, status=status.HTTP_404_NOT_FOUND)

    rows = box_data.get('rows') or 0
    cols = box_data.get('cols') or 0
    if rows == 0 or cols == 0:
        return Response({'error': f'Unable to determine geometry for box {box_id}'}, status=status.HTTP_404_NOT_FOUND)

    cells_map = box_data.get('cells', {})
    cells_grid = []

    for r in range(1, rows + 1):
        row_label = row_index_to_label(r)
        row_cells = []
        for c in range(1, cols + 1):
            cell_id = f"{row_label}{c}"
            cell_info = cells_map.get(cell_id)
            if cell_info:
                occupied = bool(cell_info.get('occupied'))
                primary = cell_info.get('primary_sample')
                sample_info = None
                if occupied and primary:
                    sample_info = {
                        'sample_id': primary.get('sample_id'),
                        'strain_id': primary.get('strain_id'),
                        'strain_number': primary.get('strain_code'),
                        'comment': primary.get('comment'),
                        'total_samples': cell_info.get('total_samples', 0),
                    }
                elif occupied:
                    sample_info = {
                        'sample_id': None,
                        'strain_id': None,
                        'strain_number': None,
                        'comment': None,
                        'total_samples': cell_info.get('total_samples', 0),
                    }
                row_cells.append({
                    'row': r,
                    'col': c,
                    'cell_id': cell_id,
                    'storage_id': cell_info.get('storage_id'),
                    'is_occupied': occupied,
                    'sample_info': sample_info,
                })
            else:
                row_cells.append({
                    'row': r,
                    'col': c,
                    'cell_id': cell_id,
                    'storage_id': None,
                    'is_occupied': False,
                    'sample_info': None,
                })
        cells_grid.append(row_cells)

    occupancy_percentage = round(
        (stats['occupied_cells'] / stats['total_cells'] * 100) if stats['total_cells'] else 0,
        1,
    )

    return Response({
        'box_id': box_data.get('box_id'),
        'rows': rows,
        'cols': cols,
        'description': box_data.get('description'),
        'total_cells': stats['total_cells'],
        'occupied_cells': stats['occupied_cells'],
        'free_cells': stats['free_cells'],
        'occupancy_percentage': occupancy_percentage,
        'cells_grid': cells_grid,
    })


@api_view(['GET'])
def get_box_cells(request, box_id):
    search_query = (request.GET.get('search') or '').strip().lower()
    box_key = str(box_id).strip().upper()
    snapshot = storage_services.build_storage_snapshot([box_key])
    box_map = snapshot.get('box_map', {})
    box_data = box_map.get(box_key)

    if box_data is None:
        return Response({'error': f'Storage box with ID {box_id} not found'}, status=status.HTTP_404_NOT_FOUND)

    free_cells = box_data.get('free_cells_sorted', [])
    if search_query:
        free_cells = [
            cell
            for cell in free_cells
            if search_query in (cell.get('cell_id') or '').lower()
            or search_query in box_key.lower()
        ]

    limited_cells = free_cells[:100]

    return Response({
        'box_id': box_data.get('box_id'),
        'cells': [
            {
                'id': cell.get('storage_id'),
                'box_id': box_data.get('box_id'),
                'cell_id': cell.get('cell_id'),
                'display_name': f"Cell {cell.get('cell_id')}"
            }
            for cell in limited_cells
        ],
    })


@extend_schema(
    operation_id="assign_cell",
    summary="(Deprecated) Размещение образца в ячейке",
    deprecated=True,
    responses={
        200: OpenApiResponse(description="Размещение выполнено"),
        400: OpenApiResponse(description="Ошибка валидации"),
        404: OpenApiResponse(description="Образец или ячейка не найдены"),
        409: OpenApiResponse(description="Конфликт размещения"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['POST'])
@csrf_exempt
def assign_cell(request, box_id, cell_id):
    """Legacy endpoint. Use allocate_cell with is_primary=true instead."""
    try:
        class AssignCellSchema(BaseModel):
            sample_id: int = Field(gt=0, description="ID образца для размещения")

        try:
            validated_data = AssignCellSchema.model_validate(request.data)
        except ValidationError as e:
            response = Response({'errors': e.errors()}, status=status.HTTP_400_BAD_REQUEST)
            return _mark_legacy_deprecated('assign_cell', response, box_id=box_id, cell_id=cell_id)

        try:
            result = storage_services.assign_primary_cell(
                sample_id=validated_data.sample_id,
                box_id=box_id,
                cell_id=cell_id,
            )
        except StorageServiceError as exc:
            response = _handle_service_error(exc)
            return _mark_legacy_deprecated('assign_cell', response, box_id=box_id, cell_id=cell_id)

        _log_service_changes(request, result.logs)
        payload = result.payload.get('assignment', {})
        response = Response({
            'message': f'Образец размещён в ячейке {cell_id}',
            'assignment': payload,
        })
        return _mark_legacy_deprecated('assign_cell', response, box_id=box_id, cell_id=cell_id)
    except Exception as e:
        logger.error(f"Error in assign_cell: {e}")
        response = Response({'error': f'Ошибка при размещении: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return _mark_legacy_deprecated('assign_cell', response, box_id=box_id, cell_id=cell_id)


@extend_schema(
    operation_id="clear_cell",
    summary="(Deprecated) Очистка ячейки",
    deprecated=True,
    responses={
        200: OpenApiResponse(description="Ячейка освобождена"),
        404: OpenApiResponse(description="Ячейка не найдена"),
        409: OpenApiResponse(description="Ячейка уже свободна"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['DELETE'])
@csrf_exempt
def clear_cell(request, box_id, cell_id):
    """Legacy endpoint. Use unallocate_cell instead."""
    try:
        try:
            result = storage_services.clear_storage_cell(
                box_id=box_id,
                cell_id=cell_id,
            )
        except StorageServiceError as exc:
            response = _handle_service_error(exc)
            return _mark_legacy_deprecated('clear_cell', response, box_id=box_id, cell_id=cell_id)

        _log_service_changes(request, result.logs)
        response = Response({
            'message': f'Ячейка {cell_id} очищена',
            'freed_sample': result.payload.get('freed_sample'),
        })
        return _mark_legacy_deprecated('clear_cell', response, box_id=box_id, cell_id=cell_id)
    except Exception as e:
        logger.error(f"Error in clear_cell: {e}")
        response = Response({'error': f'Ошибка при очистке ячейки: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return _mark_legacy_deprecated('clear_cell', response, box_id=box_id, cell_id=cell_id)


@extend_schema(
    operation_id="bulk_assign_cells",
    summary="(Deprecated) Массовое размещение образцов",
    deprecated=True,
    responses={
        200: OpenApiResponse(description="Массовое размещение выполнено"),
        400: OpenApiResponse(description="Ошибка валидации"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['POST'])
@csrf_exempt
def bulk_assign_cells(request, box_id):
    """Legacy endpoint. Use bulk_allocate_cells instead."""
    try:
        class BulkAssignSchema(BaseModel):
            assignments: list = Field(description="Список назначений")

            class Assignment(BaseModel):
                cell_id: str = Field(description="ID ячейки")
                sample_id: int = Field(gt=0, description="ID образца")

        try:
            payload = BulkAssignSchema.model_validate(request.data)
        except ValidationError as e:
            response = Response({'errors': e.errors()}, status=status.HTTP_400_BAD_REQUEST)
            return _mark_legacy_deprecated('bulk_assign_cells', response, box_id=box_id)

        assignments: List[BulkAssignSchema.Assignment] = []
        for idx, raw_assignment in enumerate(payload.assignments, start=1):
            try:
                assignments.append(BulkAssignSchema.Assignment.model_validate(raw_assignment))
            except ValidationError as e:
                response = Response({'error': f'Ошибка в назначении #{idx}: {e.errors()}'}, status=status.HTTP_400_BAD_REQUEST)
                return _mark_legacy_deprecated('bulk_assign_cells', response, box_id=box_id)

        if not assignments:
            response = Response({'error': 'Список назначений пуст'}, status=status.HTTP_400_BAD_REQUEST)
            return _mark_legacy_deprecated('bulk_assign_cells', response, box_id=box_id)

        try:
            result = storage_services.bulk_assign_primary(
                box_id=box_id,
                assignments=[{'cell_id': item.cell_id, 'sample_id': item.sample_id} for item in assignments],
            )
        except StorageServiceError as exc:
            response = _handle_service_error(exc)
            return _mark_legacy_deprecated('bulk_assign_cells', response, box_id=box_id)

        _log_service_changes(request, result.logs)
        payload_data = result.payload
        response = Response({
            'message': 'Массовое размещение выполнено',
            'statistics': payload_data.get('statistics', {}),
            'successful_assignments': payload_data.get('successful_assignments', []),
            'errors': payload_data.get('errors', []),
        })
        return _mark_legacy_deprecated('bulk_assign_cells', response, box_id=box_id)
    except Exception as e:
        logger.error(f"Error in bulk_assign_cells: {e}")
        response = Response({'error': f'Ошибка при массовом размещении: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return _mark_legacy_deprecated('bulk_assign_cells', response, box_id=box_id)


@extend_schema(
    operation_id="bulk_allocate_cells",
    summary="Bulk allocate samples to cells",
    responses={
        200: OpenApiResponse(description="Bulk allocation completed"),
        400: OpenApiResponse(description="Validation error"),
        404: OpenApiResponse(description="Sample or cell not found"),
        409: OpenApiResponse(description="Allocation conflict"),
        500: OpenApiResponse(description="Server error"),
    }
)
@api_view(['POST'])
@csrf_exempt
def bulk_allocate_cells(request, box_id):
    try:
        class BulkAllocateSchema(BaseModel):
            assignments: list = Field(description="Список назначений")

            class Assignment(BaseModel):
                cell_id: str = Field(description="ID ячейки")
                sample_id: int = Field(gt=0, description="ID образца")

        try:
            payload = BulkAllocateSchema.model_validate(request.data)
        except ValidationError as e:
            return Response({'error': 'Ошибка валидации', 'details': e.errors()}, status=status.HTTP_400_BAD_REQUEST)

        assignments = []
        for idx, raw_assignment in enumerate(payload.assignments, start=1):
            try:
                assignments.append(BulkAllocateSchema.Assignment.model_validate(raw_assignment))
            except ValidationError as e:
                return Response({'error': f'Ошибка в назначении #{idx}: {e.errors()}'}, status=status.HTTP_400_BAD_REQUEST)

        if not assignments:
            return Response({'error': 'Список назначений пуст'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = storage_services.bulk_allocate_cells(
                box_id=box_id,
                assignments=[
                    {
                        'cell_id': assignment.cell_id,
                        'sample_id': assignment.sample_id,
                    }
                    for assignment in assignments
                ],
            )
        except StorageServiceError as exc:
            return _handle_service_error(exc)

        _log_service_changes(request, result.logs)
        payload_data = result.payload
        return Response({
            'message': 'Массовое распределение выполнено',
            'statistics': payload_data.get('statistics', {}),
            'successful_allocations': payload_data.get('successful_allocations', []),
            'errors': payload_data.get('errors', []),
        })
    except Exception as e:
        logger.error(f"Error in bulk_allocate_cells: {e}")
        return Response({'error': f'Ошибка при распределении: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    operation_id="allocate_cell",
    summary="Разместить образец в ячейке (мульти-ячейки)",
    description="Создаёт размещение образца в указанной ячейке. Поддерживает флаг is_primary для установки основной ячейки.",
    responses={
        200: OpenApiResponse(description="Размещение создано"),
        400: OpenApiResponse(description="Ошибка валидации / ячейка занята"),
        404: OpenApiResponse(description="Образец или ячейка не найдены"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
def allocate_cell(request, box_id, cell_id):
    try:
        try:
            payload = AllocationRequestSchema.model_validate(request.data)
        except ValidationError as e:
            return Response({'error': '�訡�� ������樨', 'details': e.errors()}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = storage_services.allocate_sample_to_cell(
                sample_id=payload.sample_id,
                box_id=box_id,
                cell_id=cell_id,
                is_primary=payload.is_primary,
            )
        except StorageServiceError as exc:
            return _handle_service_error(exc)

        _log_service_changes(request, result.logs)
        payload_data = result.payload.get('allocation', {})

        return Response({
            'message': '�����饭�� �믮�����',
            'allocation': payload_data
        })
    except Exception as e:
        logger.error(f"Error in allocate_cell: {e}")
        return Response({'error': f'�訡�� �� ࠧ��饭��: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    operation_id="unallocate_cell",
    summary="Удалить размещение образца из ячейки",
    description="Удаляет размещение образца из указанной ячейки. Если удаляется основная ячейка, поле sample.storage обнуляется.",
    responses={
        200: OpenApiResponse(description="Размещение удалено"),
        404: OpenApiResponse(description="Размещение не найдено"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['DELETE'])
@csrf_exempt
def unallocate_cell(request, box_id, cell_id):
    try:
        try:
            payload = UnallocateRequestSchema.model_validate(request.data)
        except ValidationError as e:
            return Response({'error': '�訡�� ������樨', 'details': e.errors()}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = storage_services.unallocate_sample_from_cell(
                sample_id=payload.sample_id,
                box_id=box_id,
                cell_id=cell_id,
            )
        except StorageServiceError as exc:
            return _handle_service_error(exc)

        _log_service_changes(request, result.logs)
        payload_data = result.payload.get('unallocation', {})

        return Response({
            'message': '�����饭�� 㤠����',
            'unallocated': payload_data
        })
    except Exception as e:
        logger.error(f"Error in unallocate_cell: {e}")
        return Response({'error': f'�訡�� �� 㤠����� ࠧ��饭��: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    operation_id="list_sample_cells",
    summary="Список всех ячеек размещения для образца",
    responses={
        200: OpenApiResponse(description="Список размещений"),
        404: OpenApiResponse(description="Образец не найден"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['GET'])
@csrf_exempt
def list_sample_cells(request, sample_id):
    try:
        try:
            sample = Sample.objects.get(id=sample_id)
        except Sample.DoesNotExist:
            return Response({'error': f'Образец с ID {sample_id} не найден'}, status=status.HTTP_404_NOT_FOUND)

        allocations = (
            SampleStorageAllocation.objects
            .filter(sample_id=sample_id)
            .select_related('storage')
            .order_by('allocated_at')
        )

        data = [
            {
                'storage_id': a.storage_id,
                'box_id': a.storage.box_id,
                'cell_id': a.storage.cell_id,
                'is_primary': a.is_primary,
                'allocated_at': a.allocated_at.isoformat() if a.allocated_at else None,
            }
            for a in allocations
        ]

        return Response({
            'sample_id': sample.id,
            'current_primary_storage_id': sample.storage_id,
            'allocations': data
        })
    except Exception as e:
        logger.error(f"Error in list_sample_cells: {e}")
        return Response({'error': f'Ошибка при получении списка размещений: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
