"""
API endpoints для управления хранилищами
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional
from datetime import datetime
import logging

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