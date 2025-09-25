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
from typing import Optional
from datetime import datetime
import logging
import re

from sample_management.models import Sample
from collection_manager.utils import log_change

from .models import Storage, StorageBox

logger = logging.getLogger(__name__)


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
    """Схема для создания бокса без ID"""
    
    box_id: str = Field(min_length=1, max_length=50, description="Уникальный ID бокса")
    rows: int = Field(ge=1, le=50, description="Количество рядов")
    cols: int = Field(ge=1, le=50, description="Количество колонок")
    description: Optional[str] = Field(None, max_length=500, description="Описание")
    
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


@extend_schema(
    operation_id="storage_list_storages",
    summary="Список всех ячеек хранения",
    description="Получение списка всех ячеек хранения с поддержкой поиска и пагинации",
    parameters=[
        OpenApiParameter(name='page', type=int, description='Номер страницы'),
        OpenApiParameter(name='limit', type=int, description='Количество элементов на странице'),
        OpenApiParameter(name='search', type=str, description='Поисковый запрос'),
        OpenApiParameter(name='box_id', type=str, description='Фильтр по ID бокса'),
    ],
    responses={
        200: OpenApiResponse(description="Список ячеек хранения"),
        500: OpenApiResponse(description="Ошибка сервера"),
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
    summary="Создание бокса хранения",
    description="Создание нового бокса хранения",
    responses={
        201: OpenApiResponse(description="Бокс хранения создан"),
        400: OpenApiResponse(description="Ошибка валидации"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['POST'])
@csrf_exempt
def create_storage_box(request):
    """Создание нового бокса хранения"""
    try:
        validated_data = CreateStorageBoxSchema.model_validate(request.data)
        
        # Проверяем уникальность box_id
        if StorageBox.objects.filter(box_id=validated_data.box_id).exists():
            return Response({
                'error': f'Бокс с ID "{validated_data.box_id}" уже существует'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создаем бокс
        with transaction.atomic():
            box = StorageBox.objects.create(
                box_id=validated_data.box_id,
                rows=validated_data.rows,
                cols=validated_data.cols,
                description=validated_data.description
            )
            logger.info(f"Created storage box: {box.box_id} (ID: {box.id})")
        
        return Response({
            'id': box.id,
            'box_id': box.box_id,
            'rows': box.rows,
            'cols': box.cols,
            'description': box.description,
            'created_at': box.created_at,
            'message': 'Бокс хранения успешно создан'
        }, status=status.HTTP_201_CREATED)
    
    except ValidationError as e:
        return Response({
            'error': 'Ошибки валидации данных',
            'details': e.errors()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Unexpected error in create_storage_box: {e}")
        return Response({
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    operation_id="delete_storage_box",
    summary="Удаление бокса хранения",
    description="Удаление бокса хранения по ID",
    responses={
        200: OpenApiResponse(description="Бокс хранения удален"),
        404: OpenApiResponse(description="Бокс не найден"),
        400: OpenApiResponse(description="Нельзя удалить бокс с ячейками"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['DELETE'])
@csrf_exempt
def delete_storage_box(request, box_id):
    """Удаление бокса хранения"""
    try:
        # Получаем бокс
        try:
            box = StorageBox.objects.get(id=box_id)
        except StorageBox.DoesNotExist:
            return Response({
                'error': f'Бокс с ID {box_id} не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем, есть ли связанные ячейки
        related_cells = Storage.objects.filter(box_id=box.box_id).count()
        if related_cells > 0:
            return Response({
                'error': f'Нельзя удалить бокс, так как в нем находится {related_cells} ячеек',
                'related_cells_count': related_cells
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Сохраняем информацию о боксе для ответа
        box_info = {
            'id': box.id,
            'box_id': box.box_id,
            'rows': box.rows,
            'cols': box.cols
        }
        
        # Удаляем бокс
        with transaction.atomic():
            box.delete()
            logger.info(f"Deleted storage box: {box_info['box_id']} (ID: {box_info['id']})")
        
        return Response({
            'message': f"Бокс '{box_info['box_id']}' успешно удален",
            'deleted_box': box_info
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Unexpected error in delete_storage_box: {e}")
        return Response({
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    """Return storage cells grouped by box with occupancy stats."""
    storages = Storage.objects.all().prefetch_related(
        Prefetch('sample_set', queryset=Sample.objects.select_related('strain'))
    )

    boxes = {}
    for storage in storages:
        box_state = boxes.setdefault(
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

    ordered_boxes = list(boxes.values())
    for box in ordered_boxes:
        box['cells'].sort(key=lambda x: x['cell_id'])

    def _box_sort_key(item):
        match = re.search(r'(\d+)$', str(item['box_id']))
        if match:
            return (0, int(match.group(1)))
        return (1, str(item['box_id']))

    ordered_boxes.sort(key=_box_sort_key)

    total_boxes = len(ordered_boxes)
    total_cells = sum(box['total'] for box in ordered_boxes)
    occupied_cells = sum(box['occupied'] for box in ordered_boxes)

    return Response({
        'boxes': ordered_boxes,
        'total_boxes': total_boxes,
        'total_cells': total_cells,
        'occupied_cells': occupied_cells,
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

    for box_id, total, occupied in rows:
        boxes.append({'box_id': box_id, 'occupied': occupied, 'total': total})
        total_boxes += 1
        total_cells += total
        occupied_cells += occupied

    return Response({
        'boxes': boxes,
        'total_boxes': total_boxes,
        'total_cells': total_cells,
        'occupied_cells': occupied_cells,
    })


@api_view(['GET'])
def storage_box_details(request, box_id):
    """Return detailed cell list for a specific box."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                s.id as storage_id,
                s.cell_id,
                sam.id as sample_id,
                st.short_code as strain_code,
                CASE WHEN sam.strain_id IS NOT NULL THEN true ELSE false END as occupied,
                CASE WHEN sam.id IS NULL THEN true ELSE false END as is_free_cell
            FROM storage_management_storage s
            LEFT JOIN sample_management_sample sam ON s.id = sam.storage_id
            LEFT JOIN strain_management_strain st ON sam.strain_id = st.id
            WHERE s.box_id = %s
            ORDER BY s.cell_id
            """,
            [box_id],
        )
        rows = cursor.fetchall()

    cells = []
    occupied_count = 0

    for storage_id, cell_id, sample_id, strain_code, occupied, is_free_cell in rows:
        occupied_flag = bool(occupied)
        cell_info = {
            'cell_id': cell_id,
            'storage_id': storage_id,
            'occupied': occupied_flag,
            'sample_id': sample_id,
            'strain_code': strain_code,
            'is_free_cell': bool(is_free_cell),
        }
        cells.append(cell_info)
        if occupied_flag:
            occupied_count += 1

    return Response({
        'box_id': box_id,
        'cells': cells,
        'total': len(cells),
        'occupied': occupied_count,
    })


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
