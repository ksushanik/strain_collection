"""
API endpoints для управления хранилищами
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import connection, transaction
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
from collection_manager.utils import log_change

from .models import Storage, StorageBox

logger = logging.getLogger(__name__)




def _row_index_to_label(index: int) -> str:
    label = ''
    current = index
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        label = chr(65 + remainder) + label
    return label




def _label_to_row_index(label: str) -> int:
    total = 0
    for ch in label.upper():
        if 'A' <= ch <= 'Z':
            total = total * 26 + (ord(ch) - 64)
        else:
            break
    return total if total else 0

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


def _create_storage_cells(box_id: str, rows: int, cols: int) -> int:
    cells = []
    for row_idx in range(1, rows + 1):
        row_label = _row_index_to_label(row_idx)
        for col_idx in range(1, cols + 1):
            cell_id = f"{row_label}{col_idx}"
            cells.append(Storage(box_id=box_id, cell_id=cell_id))
    Storage.objects.bulk_create(cells, batch_size=1000, ignore_conflicts=True)
    return len(cells)

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
        boxes = queryset[offset:offset + limit]
        
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

            cells_created = _create_storage_cells(box_id, payload.rows, payload.cols)

            log_change(
                request=request,
                content_type='StorageBox',
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
            strain_id__isnull=False,
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
                content_type='StorageBox',
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
                content_type='StorageBox',
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
    storages = Storage.objects.all().prefetch_related(
        Prefetch('sample_set', queryset=Sample.objects.select_related('strain'))
    )

    boxes_state: Dict[str, Dict[str, object]] = {}

    for storage in storages:
        box_state = boxes_state.setdefault(
            storage.box_id,
            {'box_id': storage.box_id, 'cells': [], 'occupied': 0, 'total': 0},
        )

        samples = [sample for sample in storage.sample_set.all() if sample.strain_id is not None]
        sample = samples[0] if samples else None
        is_occupied = sample is not None

        cell_info = {
            'cell_id': storage.cell_id,
            'storage_id': storage.id,
            'occupied': is_occupied,
            'sample_id': sample.id if sample else None,
            'strain_code': sample.strain.short_code if sample and sample.strain else None,
            'is_free_cell': not is_occupied,
        }
        box_state['cells'].append(cell_info)
        box_state['total'] += 1
        if is_occupied:
            box_state['occupied'] += 1

    if boxes_state:
        meta = {
            box.box_id: box
            for box in StorageBox.objects.filter(box_id__in=list(boxes_state.keys()))
        }
    else:
        meta = {}

    ordered_boxes = list(boxes_state.values())
    for box in ordered_boxes:
        meta_box = meta.get(box['box_id'])
        if meta_box:
            box['rows'] = meta_box.rows
            box['cols'] = meta_box.cols
            box['description'] = meta_box.description
        else:
            box['rows'] = None
            box['cols'] = None
            box['description'] = None
        box['cells'].sort(key=lambda x: x['cell_id'])
        box['total_cells'] = box['total']
        box['free_cells'] = max(box['total'] - box['occupied'], 0)

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

    ordered_boxes.sort(key=_box_sort_key)

    total_boxes = len(ordered_boxes)
    total_cells = sum(box['total'] for box in ordered_boxes)
    occupied_cells = sum(box['occupied'] for box in ordered_boxes)

    return Response(
        {
            'boxes': ordered_boxes,
            'total_boxes': total_boxes,
            'total_cells': total_cells,
            'occupied_cells': occupied_cells,
        }
    )


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
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                s.box_id,
                COUNT(*) as total_cells,
                COUNT(CASE WHEN sam.strain_id IS NOT NULL THEN 1 ELSE NULL END) as occupied_cells
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
    try:
        try:
            box = StorageBox.objects.get(box_id=box_id)
            rows = box.rows
            cols = box.cols
            description = box.description
        except StorageBox.DoesNotExist:
            box = None
            existing_cells = Storage.objects.filter(box_id=box_id)
            if not existing_cells.exists():
                return Response({'error': f'Storage box with ID {box_id} not found'}, status=status.HTTP_404_NOT_FOUND)
            max_row = 0
            max_col = 0
            for cell in existing_cells:
                label_part = ''.join(ch for ch in cell.cell_id if ch.isalpha())
                digit_part = ''.join(ch for ch in cell.cell_id if ch.isdigit())
                if label_part:
                    max_row = max(max_row, _label_to_row_index(label_part))
                if digit_part:
                    try:
                        max_col = max(max_col, int(digit_part))
                    except ValueError:
                        continue
            rows = max_row or 0
            cols = max_col or 0
            description = None
            storage_cells = list(existing_cells)
        else:
            storage_cells = list(Storage.objects.filter(box_id=box_id))

        if not storage_cells:
            return Response({'error': f'No cells registered for box {box_id}'}, status=status.HTTP_404_NOT_FOUND)

        storage_by_cell = {cell.cell_id: cell for cell in storage_cells}
        samples = Sample.objects.filter(storage__box_id=box_id).select_related('strain')
        samples_by_storage = {}
        for sample in samples:
            samples_by_storage.setdefault(sample.storage_id, []).append(sample)

        cells_grid = []
        occupied_count = 0
        total_cells = len(storage_cells)

        if not rows or not cols:
            max_row_index = 0
            max_col_index = 0
            for cell_id in storage_by_cell.keys():
                letters = ''.join(ch for ch in cell_id if ch.isalpha())
                digits = ''.join(ch for ch in cell_id if ch.isdigit())
                if letters:
                    max_row_index = max(max_row_index, _label_to_row_index(letters))
                if digits:
                    try:
                        max_col_index = max(max_col_index, int(digits))
                    except ValueError:
                        continue
            rows = max(rows, max_row_index)
            cols = max(cols, max_col_index)

        for row_idx in range(1, max(rows, 0) + 1):
            row_label = _row_index_to_label(row_idx)
            row_cells = []
            for col_idx in range(1, max(cols, 0) + 1):
                cell_id = f"{row_label}{col_idx}"
                storage_cell = storage_by_cell.get(cell_id)
                sample_list = samples_by_storage.get(storage_cell.id if storage_cell else None, []) if storage_cell else []
                is_occupied = bool(sample_list)
                if is_occupied:
                    occupied_count += 1
                    primary_sample = sample_list[0]
                    sample_info = {
                        'sample_id': primary_sample.id,
                        'strain_id': primary_sample.strain_id,
                        'strain_number': primary_sample.strain.short_code if primary_sample.strain else None,
                        'comment': primary_sample.comment if primary_sample.comment else None,
                        'total_samples': len(sample_list),
                    }
                else:
                    sample_info = None
                row_cells.append(
                    {
                        'row': row_idx,
                        'col': col_idx,
                        'cell_id': cell_id,
                        'storage_id': storage_cell.id if storage_cell else None,
                        'is_occupied': is_occupied,
                        'sample_info': sample_info,
                    }
                )
            cells_grid.append(row_cells)

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
        
        # Получаем занятые storage_id (ячейки с образцами, у которых есть штамм)
        occupied_storage_ids = Sample.objects.filter(
            storage__box_id=box_id,
            strain_id__isnull=False
        ).values_list('storage_id', flat=True)

        # Получаем свободные ячейки в указанном боксе (ячейки без образцов или с образцами без штамма)
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
    """Размещение образца в ячейке"""
    try:
        class AssignCellSchema(BaseModel):
            sample_id: int = Field(gt=0, description="ID образца для размещения")
            
        # Валидация входных данных
        try:
            validated_data = AssignCellSchema.model_validate(request.data)
        except ValidationError as e:
            return Response({'errors': e.errors()}, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем существование ячейки
        try:
            storage_cell = Storage.objects.get(box_id=box_id, cell_id=cell_id)
        except Storage.DoesNotExist:
            return Response({
                'error': f'Ячейка {cell_id} в боксе {box_id} не найдена'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем существование образца
        try:
            sample = Sample.objects.get(id=validated_data.sample_id)
        except Sample.DoesNotExist:
            return Response({
                'error': f'Образец с ID {validated_data.sample_id} не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем, что ячейка свободна
        existing_sample = Sample.objects.filter(storage=storage_cell).first()
        if existing_sample:
            return Response({
                'error': f'Ячейка {cell_id} уже занята образцом ID {existing_sample.id}',
                'occupied_by': {
                    'sample_id': existing_sample.id,
                    'strain_code': existing_sample.strain.short_code if existing_sample.strain else None
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем, что образец еще не размещен в другой ячейке
        if sample.storage:
            return Response({
                'error': f'Образец уже размещен в ячейке {sample.storage.cell_id} бокса {sample.storage.box_id}',
                'current_location': {
                    'box_id': sample.storage.box_id,
                    'cell_id': sample.storage.cell_id
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Размещаем образец
        with transaction.atomic():
            sample.storage = storage_cell
            sample.save()
            
            # Логируем размещение
            log_change(
                request=request,
                content_type='Sample',
                object_id=sample.id,
                action='ASSIGN_CELL',
                new_values={
                    'box_id': box_id,
                    'cell_id': cell_id,
                    'storage_id': storage_cell.id
                },
                comment='Sample assigned to cell'
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
    """Освобождение ячейки"""
    try:
        # Проверяем существование ячейки
        try:
            storage_cell = Storage.objects.get(box_id=box_id, cell_id=cell_id)
        except Storage.DoesNotExist:
            return Response({
                'error': f'Ячейка {cell_id} в боксе {box_id} не найдена'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Находим образец в ячейке
        sample = Sample.objects.filter(storage=storage_cell).first()
        if not sample:
            return Response({
                'error': f'Ячейка {cell_id} уже свободна'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Освобождаем ячейку
        with transaction.atomic():
            sample_info = {
                'sample_id': sample.id,
                'strain_code': sample.strain.short_code if sample.strain else None
            }
            
            sample.storage = None
            sample.save()
            
            # Логируем освобождение
            log_change(
                request=request,
                content_type='Sample',
                object_id=sample.id,
                action='CLEAR_CELL',
                old_values={
                    'box_id': box_id,
                    'cell_id': cell_id,
                    'freed_sample_id': sample.id
                },
                comment='Cell cleared, sample removed'
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
    """Массовое размещение образцов в ячейках"""
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
        
        with transaction.atomic():
            for assignment in assignments:
                try:
                    # Проверяем ячейку
                    storage_cell = Storage.objects.get(box_id=box_id, cell_id=assignment.cell_id)
                    
                    # Проверяем образец
                    sample = Sample.objects.get(id=assignment.sample_id)
                    
                    # Проверяем доступность ячейки
                    existing_sample = Sample.objects.filter(storage=storage_cell).first()
                    if existing_sample:
                        errors.append(f'Ячейка {assignment.cell_id} уже занята образцом ID {existing_sample.id}')
                        continue
                    
                    # Проверяем, что образец не размещен в другой ячейке
                    if sample.storage:
                        errors.append(f'Образец {assignment.sample_id} уже размещен в ячейке {sample.storage.cell_id}')
                        continue
                    
                    # Размещаем образец
                    sample.storage = storage_cell
                    sample.save()
                    
                    success_assignments.append({
                        'sample_id': sample.id,
                        'cell_id': assignment.cell_id,
                        'strain_code': sample.strain.short_code if sample.strain else None
                    })
                    
                    # Логируем размещение
                    log_change(
                        request=request,
                        content_type='Sample',
                        object_id=sample.id,
                        action='BULK_ASSIGN_CELL',
                        new_values={
                            'box_id': box_id,
                            'cell_id': assignment.cell_id,
                            'storage_id': storage_cell.id
                        },
                        comment='Bulk assignment of sample to cell'
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
