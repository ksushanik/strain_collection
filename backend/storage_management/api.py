"""
API endpoints для управления хранилищами
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import connection, transaction, IntegrityError
from django.db.models import Count, Prefetch, Q
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.openapi import AutoSchema
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional, Dict
from datetime import datetime
import logging
import re

from sample_management.models import Sample
from collection_manager.utils import log_change, generate_batch_id

from .models import Storage, StorageBox
from .utils import (
    ensure_cells_for_boxes,
    ensure_storage_cells,
    label_to_row_index,
    row_index_to_label,
)

logger = logging.getLogger(__name__)




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
    """Return storage boxes with cell occupancy information."""
    boxes_meta = list(StorageBox.objects.all())
    meta_map = {box.box_id: box for box in boxes_meta}

    if boxes_meta:
        ensure_cells_for_boxes(boxes_meta)

    storages = Storage.objects.all().prefetch_related(
        Prefetch('sample_set', queryset=Sample.objects.select_related('strain'))
    )

    boxes_state: Dict[str, Dict[str, object]] = {}
    # Map of box_id -> { cell_id -> merged cell info }
    cells_by_box: Dict[str, Dict[str, dict]] = {}

    for storage in storages:
        meta_box = meta_map.get(storage.box_id)
        box_state = boxes_state.setdefault(
            storage.box_id,
            {
                'box_id': storage.box_id,
                'cells': [],
                'occupied': 0,
                'total': 0,
                'rows': meta_box.rows if meta_box else None,
                'cols': meta_box.cols if meta_box else None,
                'description': meta_box.description if meta_box else None,
            },
        )

        samples = list(storage.sample_set.all())
        sample = samples[0] if samples else None
        is_occupied = bool(samples)

        new_cell_info = {
            'cell_id': storage.cell_id,
            'storage_id': storage.id,
            'occupied': is_occupied,
            'sample_id': sample.id if sample else None,
            'strain_code': sample.strain.short_code if sample and sample.strain else None,
            'is_free_cell': not is_occupied,
        }

        cell_map = cells_by_box.setdefault(storage.box_id, {})
        existing = cell_map.get(storage.cell_id)
        if existing is None:
            cell_map[storage.cell_id] = new_cell_info
        else:
            # If duplicates exist for the same cell_id, prefer the one that has a sample
            if is_occupied and not existing['occupied']:
                existing['occupied'] = True
                existing['is_free_cell'] = False
                existing['sample_id'] = new_cell_info['sample_id']
                existing['strain_code'] = new_cell_info['strain_code']
                existing['storage_id'] = new_cell_info['storage_id']

    # Build final boxes list with deduplicated cells and corrected counts
    for box_id, box_state in boxes_state.items():
        cells_list = list(cells_by_box.get(box_id, {}).values())
        cells_list.sort(key=lambda x: x['cell_id'])
        box_state['cells'] = cells_list
        box_state['total'] = len(cells_list)
        box_state['occupied'] = sum(1 for c in cells_list if c['occupied'])

    for box_id, meta_box in meta_map.items():
        if box_id not in boxes_state:
            total_cells = (meta_box.rows or 0) * (meta_box.cols or 0)
            boxes_state[box_id] = {
                'box_id': box_id,
                'cells': [],
                'occupied': 0,
                'total': total_cells,
                'rows': meta_box.rows,
                'cols': meta_box.cols,
                'description': meta_box.description,
            }
        else:
            box_state = boxes_state[box_id]
            if box_state.get('rows') is None:
                box_state['rows'] = meta_box.rows
            if box_state.get('cols') is None:
                box_state['cols'] = meta_box.cols
            if box_state.get('description') is None:
                box_state['description'] = meta_box.description

    ordered_boxes = list(boxes_state.values())
    for box in ordered_boxes:
        total_cells = box.get('total') or 0
        rows = box.get('rows') or 0
        cols = box.get('cols') or 0
        if total_cells == 0 and rows and cols:
            total_cells = rows * cols
            box['total'] = total_cells
        box['total_cells'] = total_cells
        box['free_cells'] = max(total_cells - box['occupied'], 0)

    def _box_sort_key(item):
        box_id = str(item['box_id'])
        suffix_chars = []
        for ch in reversed(box_id):
            if ch.isdigit():
                suffix_chars.append(ch)
            else:
                break
        if suffix_chars:
            number = int(''.join(reversed(suffix_chars)))
            return (0, number)
        return (1, box_id)

    boxes = sorted(ordered_boxes, key=_box_sort_key)
    total_boxes = len(boxes)
    total_cells = 0
    occupied_cells = 0
    free_cells_total = 0

    for box in boxes:
        total_cells += box.get('total_cells', 0)
        occupied_cells += box.get('occupied', 0)
        free_cells_total += box.get('free_cells', 0)

    return Response({
        'boxes': boxes,
        'total_boxes': total_boxes,
        'total_cells': total_cells,
        'occupied_cells': occupied_cells,
        'free_cells': free_cells_total,
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
    """Return aggregated occupancy counts per box."""
    boxes_meta = list(StorageBox.objects.all())
    if boxes_meta:
        ensure_cells_for_boxes(boxes_meta)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                s.box_id,
                COUNT(DISTINCT s.cell_id) as total_cells,
                COUNT(DISTINCT CASE WHEN sam.id IS NOT NULL THEN s.cell_id ELSE NULL END) as occupied_cells
            FROM storage_management_storage s
            LEFT JOIN sample_management_sample sam ON s.id = sam.storage_id
            GROUP BY s.box_id
            ORDER BY s.box_id
            """
        )
        rows = cursor.fetchall()

    boxes = []
    total_boxes = 0
    total_cells = 0
    occupied_cells = 0
    free_cells_total = 0

    for box_id, total, occupied in rows:
        free_cells = max(total - occupied, 0)
        boxes.append({'box_id': box_id, 'occupied': occupied, 'total': total, 'free_cells': free_cells})
        total_boxes += 1
        total_cells += total
        occupied_cells += occupied
        free_cells_total += free_cells

    return Response({
        'boxes': boxes,
        'total_boxes': total_boxes,
        'total_cells': total_cells,
        'occupied_cells': occupied_cells,
        'free_cells': free_cells_total,
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
    """Detailed view of a storage box with a 2D grid."""
    rows = None
    cols = None
    description = None
    try:
        try:
            box = StorageBox.objects.get(box_id=box_id)
            rows = box.rows
            cols = box.cols
            description = box.description
        except StorageBox.DoesNotExist:
            box = None
            storages_qs = Storage.objects.filter(box_id=box_id).prefetch_related(
                Prefetch('sample_set', queryset=Sample.objects.select_related('strain'))
            )
            if not storages_qs.exists():
                return Response({'error': f'Storage box with ID {box_id} not found'}, status=status.HTTP_404_NOT_FOUND)
            storages = list(storages_qs)
        else:
            ensure_storage_cells(box.box_id, box.rows, box.cols)
            storages = list(Storage.objects.filter(box_id=box_id).prefetch_related(
                Prefetch('sample_set', queryset=Sample.objects.select_related('strain'))
            ))

        if not storages:
            return Response({'error': f'No cells registered for box {box_id}'}, status=status.HTTP_404_NOT_FOUND)

        # Deduplicate by cell_id, prefer occupied entries
        cell_map = {}
        for storage in storages:
            samples = list(storage.sample_set.all())
            sample = samples[0] if samples else None
            is_occupied = bool(samples)
            existing = cell_map.get(storage.cell_id)
            if existing is None:
                cell_map[storage.cell_id] = {
                    'storage_id': storage.id,
                    'occupied': is_occupied,
                    'sample_id': sample.id if sample else None,
                    'strain_id': (sample.strain.id if sample and getattr(sample, 'strain', None) else None),
                    'strain_number': (sample.strain.short_code if sample and getattr(sample, 'strain', None) else None),
                    'comment': (getattr(sample, 'comment', None) if sample else None),
                    'total_samples': len(samples),
                }
            else:
                if is_occupied and not existing['occupied']:
                    existing['occupied'] = True
                    existing['storage_id'] = storage.id
                    existing['sample_id'] = sample.id if sample else None
                    existing['strain_id'] = (sample.strain.id if sample and getattr(sample, 'strain', None) else None)
                    existing['strain_number'] = (sample.strain.short_code if sample and getattr(sample, 'strain', None) else None)
                    existing['comment'] = (getattr(sample, 'comment', None) if sample else None)
                    existing['total_samples'] = len(samples)

        # If box metadata missing, infer rows/cols from deduped cell ids
        if not (rows and cols):
            max_row_index = 0
            max_col_index = 0
            for cell_id in cell_map.keys():
                letters = ''.join(ch for ch in cell_id if ch.isalpha())
                digits = ''.join(ch for ch in cell_id if ch.isdigit())
                if letters:
                    max_row_index = max(max_row_index, label_to_row_index(letters))
                if digits:
                    try:
                        max_col_index = max(max_col_index, int(digits))
                    except ValueError:
                        continue
            rows = (rows or 0)
            cols = (cols or 0)
            rows = max(rows, max_row_index)
            cols = max(cols, max_col_index)
            description = description

        cells_grid = []
        occupied_count = 0

        for r in range(1, (rows or 0) + 1):
            row_label = row_index_to_label(r)
            row_cells = []
            for c in range(1, (cols or 0) + 1):
                cell_id = f"{row_label}{c}"
                cell_info = cell_map.get(cell_id)
                if cell_info:
                    occupied = bool(cell_info.get('occupied'))
                    if occupied:
                        occupied_count += 1
                    row_cells.append({
                        'row': r,
                        'col': c,
                        'cell_id': cell_id,
                        'storage_id': cell_info.get('storage_id'),
                        'is_occupied': occupied,
                        'sample_info': {
                            'sample_id': cell_info.get('sample_id'),
                            'strain_id': cell_info.get('strain_id'),
                            'strain_number': cell_info.get('strain_number'),
                            'comment': cell_info.get('comment'),
                            'total_samples': cell_info.get('total_samples') if cell_info.get('total_samples') is not None else (1 if occupied else 0),
                        } if occupied else None,
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

        total_cells = (rows or 0) * (cols or 0)
        if total_cells == 0:
            total_cells = len(cell_map)

        free_cells = max(total_cells - occupied_count, 0)
        occupancy_percentage = round((occupied_count / total_cells * 100) if total_cells else 0, 1)

        return Response(
            {
                'box_id': box_id,
                'rows': rows,
                'cols': cols,
                'description': description,
                'total_cells': total_cells,
                'occupied_cells': occupied_count,
                'free_cells': free_cells,
                'occupancy_percentage': occupancy_percentage,
                'cells_grid': cells_grid,
            }
        )
    except Exception as exc:
        logger.error(f"Unexpected error in storage_box_details: {exc}")
        return Response(
            {'error': f'Failed to load storage box details: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
def get_box_cells(request, box_id):
    """Получение списка свободных ячеек в указанном боксе"""
    try:
        search_query = request.GET.get('search', '').strip()

        box = StorageBox.objects.filter(box_id=box_id).first()
        if box:
            ensure_storage_cells(box.box_id, box.rows, box.cols)

        occupied_storage_ids = Sample.objects.filter(
            storage__box_id=box_id
        ).values_list('storage_id', flat=True)

        cells_qs = Storage.objects.filter(box_id=box_id).exclude(
            id__in=occupied_storage_ids
        )

        if search_query:
            cells_qs = cells_qs.filter(
                Q(cell_id__icontains=search_query) |
                Q(box_id__icontains=search_query)
            )

        cells = cells_qs.order_by('cell_id')[:100]

        return Response({
            'box_id': box_id,
            'cells': [
                {
                    'id': cell.id,
                    'box_id': cell.box_id,
                    'cell_id': cell.cell_id,
                    'display_name': f"Ячейка {cell.cell_id}"
                }
                for cell in cells
            ]
        })

    except Exception as e:
        logger.error(f"Unexpected error in get_box_cells: {e}")
        return Response({
            'error': f'Ошибка при получении ячеек бокса {box_id}: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@csrf_exempt
def assign_cell(request, box_id, cell_id):
    """Размещение образца в ячейке (с блокировками и полным логированием)"""
    try:
        class AssignCellSchema(BaseModel):
            sample_id: int = Field(gt=0, description="ID образца для размещения")

        # Валидация входных данных
        try:
            validated_data = AssignCellSchema.model_validate(request.data)
        except ValidationError as e:
            return Response({'errors': e.errors()}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Блокируем строку ячейки на время транзакции
            try:
                storage_cell = Storage.objects.select_for_update().get(box_id=box_id, cell_id=cell_id)
            except Storage.DoesNotExist:
                return Response({
                    'error': f'Ячейка {cell_id} в боксе {box_id} не найдена'
                }, status=status.HTTP_404_NOT_FOUND)

            # Блокируем строку образца на время транзакции
            try:
                sample = Sample.objects.select_for_update().get(id=validated_data.sample_id)
            except Sample.DoesNotExist:
                return Response({
                    'error': f'Образец с ID {validated_data.sample_id} не найден'
                }, status=status.HTTP_404_NOT_FOUND)

            # Проверяем, что ячейка свободна
            existing_sample_qs = Sample.objects.select_for_update().filter(storage=storage_cell)
            if existing_sample_qs.exists():
                existing_sample = existing_sample_qs.first()
                return Response({
                    'error': f'Ячейка {cell_id} уже занята образцом ID {existing_sample.id}',
                    'occupied_by': {
                        'sample_id': existing_sample.id,
                        'strain_code': existing_sample.strain.short_code if existing_sample.strain else None
                    }
                }, status=status.HTTP_409_CONFLICT)

            # Проверяем, что образец еще не размещен в другой ячейке
            if sample.storage_id is not None:
                return Response({
                    'error': f'Образец уже размещен в ячейке {sample.storage.cell_id} бокса {sample.storage.box_id}',
                    'current_location': {
                        'box_id': sample.storage.box_id,
                        'cell_id': sample.storage.cell_id
                    }
                }, status=status.HTTP_409_CONFLICT)

            # Выполняем назначение
            old_storage = sample.storage
            sample.storage = storage_cell
            try:
                with transaction.atomic():
                    sample.save()
            except IntegrityError as ie:
                return Response({
                    'error': 'Конфликт размещения: ячейка уже занята или образец уже размещен',
                    'details': str(ie),
                    'box_id': box_id,
                    'cell_id': cell_id,
                    'sample_id': sample.id
                }, status=status.HTTP_409_CONFLICT)

            # Логируем изменение как UPDATE с полными старыми/новыми значениями
            log_change(
                request=request,
                content_type='sample',
                object_id=sample.id,
                action='UPDATE',
                old_values={
                    'previous_box_id': old_storage.box_id if old_storage else None,
                    'previous_cell_id': old_storage.cell_id if old_storage else None,
                    'previous_storage_id': old_storage.id if old_storage else None
                },
                new_values={
                    'box_id': box_id,
                    'cell_id': cell_id,
                    'storage_id': storage_cell.id
                },
                comment='Assign cell: sample placed into storage cell'
            )

        return Response({
            'message': f'Образец успешно размещен в ячейке {cell_id}',
            'assignment': {
                'sample_id': sample.id,
                'box_id': box_id,
                'cell_id': cell_id,
                'strain_code': sample.strain.short_code if sample.strain else None
            }
        })

    except Exception as e:
        logger.error(f"Error in assign_cell: {e}")
        return Response({
            'error': f'Ошибка при размещении образца: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@csrf_exempt
def clear_cell(request, box_id, cell_id):
    """Освобождение ячейки (с блокировками и полным логированием)"""
    try:
        with transaction.atomic():
            # Блокируем строку ячейки на время транзакции
            try:
                storage_cell = Storage.objects.select_for_update().get(box_id=box_id, cell_id=cell_id)
            except Storage.DoesNotExist:
                return Response({
                    'error': f'Ячейка {cell_id} в боксе {box_id} не найдена'
                }, status=status.HTTP_404_NOT_FOUND)

            # Находим образец в ячейке с блокировкой
            sample_qs = Sample.objects.select_for_update().filter(storage=storage_cell)
            if not sample_qs.exists():
                return Response({
                    'error': f'Ячейка {cell_id} уже свободна'
                }, status=status.HTTP_409_CONFLICT)

            sample = sample_qs.first()
            sample_info = {
                'sample_id': sample.id,
                'strain_code': sample.strain.short_code if sample.strain else None
            }

            old_storage = sample.storage
            sample.storage = None
            sample.save()

            # Логируем как UPDATE: storage -> None
            log_change(
                request=request,
                content_type='sample',
                object_id=sample.id,
                action='UPDATE',
                old_values={
                    'previous_box_id': old_storage.box_id if old_storage else None,
                    'previous_cell_id': old_storage.cell_id if old_storage else None,
                    'previous_storage_id': old_storage.id if old_storage else None
                },
                new_values={
                    'box_id': None,
                    'cell_id': None,
                    'storage_id': None
                },
                comment='Clear cell: sample removed from storage cell'
            )

        return Response({
            'message': f'Ячейка {cell_id} успешно освобождена',
            'freed_sample': sample_info
        })

    except Exception as e:
        logger.error(f"Error in clear_cell: {e}")
        return Response({
            'error': f'Ошибка при освобождении ячейки: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@csrf_exempt
def bulk_assign_cells(request, box_id):
    """Массовое размещение образцов в ячейках (с блокировками, batch_id и полным логированием)"""
    try:
        class BulkAssignSchema(BaseModel):
            assignments: list = Field(description="Список назначений")
            
            class Assignment(BaseModel):
                cell_id: str = Field(description="ID ячейки")
                sample_id: int = Field(gt=0, description="ID образца")
        
        # Валидация входных данных
        try:
            validated_data = BulkAssignSchema.model_validate(request.data)
        except ValidationError as e:
            return Response({'errors': e.errors()}, status=status.HTTP_400_BAD_REQUEST)
        
        if not validated_data.assignments:
            return Response({
                'error': 'Список назначений не может быть пустым'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Валидируем каждое назначение
        assignments = []
        for i, assignment_data in enumerate(validated_data.assignments):
            try:
                assignment = BulkAssignSchema.Assignment.model_validate(assignment_data)
                assignments.append(assignment)
            except ValidationError as e:
                return Response({
                    'error': f'Ошибка в назначении #{i+1}: {e.errors()}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем все ячейки и образцы
        errors = []
        success_assignments = []
        batch_id = generate_batch_id()
        
        with transaction.atomic():
            for assignment in assignments:
                try:
                    # Блокируем ячейку
                    storage_cell = Storage.objects.select_for_update().get(box_id=box_id, cell_id=assignment.cell_id)
                    
                    # Блокируем образец
                    sample = Sample.objects.select_for_update().get(id=assignment.sample_id)
                    
                    # Проверяем доступность ячейки
                    existing_sample_qs = Sample.objects.select_for_update().filter(storage=storage_cell)
                    if existing_sample_qs.exists():
                        existing_sample = existing_sample_qs.first()
                        errors.append(f'Ячейка {assignment.cell_id} уже занята образцом ID {existing_sample.id}')
                        continue
                    
                    # Проверяем, что образец не размещен в другой ячейке
                    if sample.storage_id is not None:
                        errors.append(f'Образец {assignment.sample_id} уже размещен в ячейке {sample.storage.cell_id}')
                        continue
                    
                    # Размещаем образец
                    old_storage = sample.storage
                    sample.storage = storage_cell
                    try:
                        with transaction.atomic():
                            sample.save()
                    except IntegrityError as ie:
                        errors.append(f'Конфликт размещения для ячейки {assignment.cell_id} и образца {assignment.sample_id}: {str(ie)}')
                        continue

                    success_assignments.append({
                        'sample_id': sample.id,
                        'cell_id': assignment.cell_id,
                        'strain_code': sample.strain.short_code if sample.strain else None
                    })
                    
                    # Логируем размещение с batch_id
                    log_change(
                        request=request,
                        content_type='sample',
                        object_id=sample.id,
                        action='UPDATE',
                        old_values={
                            'previous_box_id': old_storage.box_id if old_storage else None,
                            'previous_cell_id': old_storage.cell_id if old_storage else None,
                            'previous_storage_id': old_storage.id if old_storage else None
                        },
                        new_values={
                            'box_id': box_id,
                            'cell_id': assignment.cell_id,
                            'storage_id': storage_cell.id
                        },
                        comment='Bulk assignment of sample to cell',
                        batch_id=batch_id
                    )
                    
                except Storage.DoesNotExist:
                    errors.append(f'Ячейка {assignment.cell_id} в боксе {box_id} не найдена')
                except Sample.DoesNotExist:
                    errors.append(f'Образец с ID {assignment.sample_id} не найден')
                except Exception as e:
                    errors.append(f'Ошибка при размещении образца {assignment.sample_id} в ячейке {assignment.cell_id}: {str(e)}')
        
        return Response({
            'message': f'Массовое размещение завершено',
            'statistics': {
                'total_requested': len(assignments),
                'successful': len(success_assignments),
                'failed': len(errors)
            },
            'successful_assignments': success_assignments,
            'errors': errors
        })
    
    except Exception as e:
        logger.error(f"Error in bulk_assign_cells: {e}")
        return Response({
            'error': f'Ошибка при массовом размещении: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
