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
import logging

from .models import Storage, StorageBox

logger = logging.getLogger(__name__)


class StorageSchema(BaseModel):
    """Схема валидации для хранилищ"""

    id: Optional[int] = Field(None, ge=1, description="ID хранилища")
    name: str = Field(min_length=1, max_length=200, description="Название хранилища")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")
    temperature: Optional[str] = Field(None, max_length=50, description="Температура")
    location: Optional[str] = Field(None, max_length=200, description="Местоположение")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("description", "temperature", "location")
    @classmethod
    def validate_optional_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    class Config:
        from_attributes = True


class CreateStorageSchema(BaseModel):
    """Схема для создания хранилища без ID"""
    
    name: str = Field(min_length=1, max_length=200, description="Название хранилища")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")
    temperature: Optional[str] = Field(None, max_length=50, description="Температура")
    location: Optional[str] = Field(None, max_length=200, description="Местоположение")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("description", "temperature", "location")
    @classmethod
    def validate_optional_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


class StorageBoxSchema(BaseModel):
    """Схема валидации для ящиков хранилища"""

    id: Optional[int] = Field(None, ge=1, description="ID ящика")
    storage_id: int = Field(ge=1, description="ID хранилища")
    name: str = Field(min_length=1, max_length=100, description="Название ящика")
    description: Optional[str] = Field(None, max_length=500, description="Описание")
    position: Optional[str] = Field(None, max_length=50, description="Позиция в хранилище")
    capacity: Optional[int] = Field(None, ge=1, description="Вместимость")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("description", "position")
    @classmethod
    def validate_optional_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    class Config:
        from_attributes = True


class CreateStorageBoxSchema(BaseModel):
    """Схема для создания ящика без ID"""
    
    storage_id: int = Field(ge=1, description="ID хранилища")
    name: str = Field(min_length=1, max_length=100, description="Название ящика")
    description: Optional[str] = Field(None, max_length=500, description="Описание")
    position: Optional[str] = Field(None, max_length=50, description="Позиция в хранилище")
    capacity: Optional[int] = Field(None, ge=1, description="Вместимость")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("description", "position")
    @classmethod
    def validate_optional_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


@api_view(['GET'])
def list_storages(request):
    """Список всех хранилищ с поиском и статистикой"""
    try:
        page = max(1, int(request.GET.get('page', 1)))
        limit = max(1, min(int(request.GET.get('limit', 50)), 1000))
        offset = (page - 1) * limit
        
        # Полнотекстовый поиск
        search_query = request.GET.get('search', '').strip()
        
        queryset = Storage.objects.annotate(
            boxes_count=Count('storagebox'),
            samples_count=Count('sample')
        )
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
        total_count = queryset.count()
        storages = queryset[offset:offset + limit]
        
        data = []
        for storage in storages:
            storage_data = StorageSchema.model_validate(storage).model_dump()
            storage_data['boxes_count'] = storage.boxes_count
            storage_data['samples_count'] = storage.samples_count
            data.append(storage_data)
        
        return Response({
            'storages': data,
            'total': total_count,
            'page': page,
            'limit': limit,
            'has_next': offset + limit < total_count,
            'has_prev': page > 1
        })
        
    except Exception as e:
        logger.error(f"Error in list_storages: {e}")
        return Response(
            {'error': f'Ошибка получения списка хранилищ: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_storage(request, storage_id):
    """Получение хранилища по ID с информацией о ящиках"""
    try:
        storage = Storage.objects.annotate(
            boxes_count=Count('storagebox'),
            samples_count=Count('sample')
        ).get(id=storage_id)
        
        data = StorageSchema.model_validate(storage).model_dump()
        data['boxes_count'] = storage.boxes_count
        data['samples_count'] = storage.samples_count
        
        # Добавляем информацию о ящиках
        boxes = StorageBox.objects.filter(storage_id=storage_id)
        data['boxes'] = [StorageBoxSchema.model_validate(box).model_dump() for box in boxes]
        
        return Response(data)
    except Storage.DoesNotExist:
        return Response(
            {'error': f'Хранилище с ID {storage_id} не найдено'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in get_storage: {e}")
        return Response(
            {'error': f'Ошибка получения хранилища: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@csrf_exempt
def create_storage(request):
    """Создание нового хранилища"""
    try:
        validated_data = CreateStorageSchema.model_validate(request.data)
        
        # Проверяем уникальность названия
        if Storage.objects.filter(name=validated_data.name).exists():
            return Response({
                'error': f'Хранилище с названием "{validated_data.name}" уже существует'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создаем хранилище
        with transaction.atomic():
            storage = Storage.objects.create(
                name=validated_data.name,
                description=validated_data.description,
                temperature=validated_data.temperature,
                location=validated_data.location
            )
            logger.info(f"Created storage: {storage.name} (ID: {storage.id})")
        
        return Response({
            'id': storage.id,
            'name': storage.name,
            'description': storage.description,
            'temperature': storage.temperature,
            'location': storage.location,
            'message': 'Хранилище успешно создано'
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
    """Обновление хранилища"""
    try:
        # Получаем хранилище
        try:
            storage = Storage.objects.get(id=storage_id)
        except Storage.DoesNotExist:
            return Response({
                'error': f'Хранилище с ID {storage_id} не найдено'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Валидируем данные
        validated_data = CreateStorageSchema.model_validate(request.data)
        
        # Проверяем уникальность названия (исключая текущее хранилище)
        if Storage.objects.filter(name=validated_data.name).exclude(id=storage_id).exists():
            return Response({
                'error': f'Хранилище с названием "{validated_data.name}" уже существует'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Обновление хранилища
        with transaction.atomic():
            storage.name = validated_data.name
            storage.description = validated_data.description
            storage.temperature = validated_data.temperature
            storage.location = validated_data.location
            storage.save()
            
            logger.info(f"Updated storage: {storage.name} (ID: {storage.id})")
        
        return Response({
            'id': storage.id,
            'name': storage.name,
            'description': storage.description,
            'temperature': storage.temperature,
            'location': storage.location,
            'message': 'Хранилище успешно обновлено'
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
    """Удаление хранилища"""
    try:
        # Получаем хранилище
        try:
            storage = Storage.objects.get(id=storage_id)
        except Storage.DoesNotExist:
            return Response({
                'error': f'Хранилище с ID {storage_id} не найдено'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем, есть ли связанные образцы
        from sample_management.models import Sample
        related_samples = Sample.objects.filter(storage_id=storage_id).count()
        if related_samples > 0:
            return Response({
                'error': f'Нельзя удалить хранилище, так как в нем находится {related_samples} образцов',
                'related_samples_count': related_samples
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем, есть ли ящики
        related_boxes = StorageBox.objects.filter(storage_id=storage_id).count()
        if related_boxes > 0:
            return Response({
                'error': f'Нельзя удалить хранилище, так как в нем находится {related_boxes} ящиков',
                'related_boxes_count': related_boxes
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Сохраняем информацию о хранилище для ответа
        storage_info = {
            'id': storage.id,
            'name': storage.name
        }
        
        # Удаляем хранилище
        with transaction.atomic():
            storage.delete()
            logger.info(f"Deleted storage: {storage_info['name']} (ID: {storage_info['id']})")
        
        return Response({
            'message': f"Хранилище '{storage_info['name']}' успешно удалено",
            'deleted_storage': storage_info
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Unexpected error in delete_storage: {e}")
        return Response({
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# API для ящиков хранилища

@api_view(['GET'])
def list_storage_boxes(request, storage_id):
    """Список ящиков в хранилище"""
    try:
        # Проверяем существование хранилища
        if not Storage.objects.filter(id=storage_id).exists():
            return Response({
                'error': f'Хранилище с ID {storage_id} не найдено'
            }, status=status.HTTP_404_NOT_FOUND)
        
        boxes = StorageBox.objects.filter(storage_id=storage_id)
        data = [StorageBoxSchema.model_validate(box).model_dump() for box in boxes]
        
        return Response({
            'boxes': data,
            'storage_id': storage_id,
            'total': len(data)
        })
        
    except Exception as e:
        logger.error(f"Error in list_storage_boxes: {e}")
        return Response(
            {'error': f'Ошибка получения списка ящиков: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@csrf_exempt
def create_storage_box(request):
    """Создание нового ящика в хранилище"""
    try:
        validated_data = CreateStorageBoxSchema.model_validate(request.data)
        
        # Проверяем существование хранилища
        if not Storage.objects.filter(id=validated_data.storage_id).exists():
            return Response({
                'error': f'Хранилище с ID {validated_data.storage_id} не найдено'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем уникальность названия ящика в рамках хранилища
        if StorageBox.objects.filter(
            storage_id=validated_data.storage_id, 
            name=validated_data.name
        ).exists():
            return Response({
                'error': f'Ящик с названием "{validated_data.name}" уже существует в этом хранилище'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создаем ящик
        with transaction.atomic():
            box = StorageBox.objects.create(
                storage_id=validated_data.storage_id,
                name=validated_data.name,
                description=validated_data.description,
                position=validated_data.position,
                capacity=validated_data.capacity
            )
            logger.info(f"Created storage box: {box.name} (ID: {box.id}) in storage {box.storage_id}")
        
        return Response({
            'id': box.id,
            'storage_id': box.storage_id,
            'name': box.name,
            'description': box.description,
            'position': box.position,
            'capacity': box.capacity,
            'message': 'Ящик успешно создан'
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
    """Удаление ящика"""
    try:
        # Получаем ящик
        try:
            box = StorageBox.objects.get(id=box_id)
        except StorageBox.DoesNotExist:
            return Response({
                'error': f'Ящик с ID {box_id} не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Сохраняем информацию о ящике для ответа
        box_info = {
            'id': box.id,
            'name': box.name,
            'storage_id': box.storage_id
        }
        
        # Удаляем ящик
        with transaction.atomic():
            box.delete()
            logger.info(f"Deleted storage box: {box_info['name']} (ID: {box_info['id']})")
        
        return Response({
            'message': f"Ящик '{box_info['name']}' успешно удален",
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