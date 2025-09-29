"""
API endpoints для управления образцами
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction, connection, IntegrityError
from django.db.models import Q, Prefetch
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional, List
from datetime import datetime
import logging
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.openapi import AutoSchema

from .models import Sample, SampleGrowthMedia, SamplePhoto, SampleCharacteristic, SampleCharacteristicValue
from reference_data.models import IndexLetter, IUKColor, AmylaseVariant, GrowthMedium, Source, Location
from strain_management.models import Strain
from storage_management.models import Storage
from collection_manager.schemas import SampleCharacteristicSchema, SampleCharacteristicValueSchema

logger = logging.getLogger(__name__)


def reset_sequence(model_class):
    """Сброс последовательности автоинкремента для модели"""
    table_name = model_class._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), COALESCE(MAX(id), 1)) FROM {table_name};")


class SampleSchema(BaseModel):
    """Схема валидации для образцов"""

    id: Optional[int] = Field(None, ge=1, description="ID образца")
    index_letter_id: Optional[int] = Field(None, ge=1, description="ID индексной буквы")
    strain_id: Optional[int] = Field(None, ge=1, description="ID штамма")
    storage_id: Optional[int] = Field(None, ge=1, description="ID хранилища")
    original_sample_number: Optional[str] = Field(None, max_length=100, description="Оригинальный номер образца")
    source_id: Optional[int] = Field(None, ge=1, description="ID источника")
    location_id: Optional[int] = Field(None, ge=1, description="ID местоположения")
    appendix_note: Optional[str] = Field(None, max_length=1000, description="Текст примечания")
    comment: Optional[str] = Field(None, max_length=1000, description="Текст комментария")
    has_photo: bool = Field(default=False, description="Есть ли фото")
    iuk_color_id: Optional[int] = Field(None, ge=1, description="ID цвета ИУК")
    amylase_variant_id: Optional[int] = Field(None, ge=1, description="ID варианта амилазы")
    growth_media_ids: Optional[List[int]] = Field(None, description="Список ID сред роста")
    characteristics: Optional[dict] = Field(None, description="Динамические характеристики образца")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")

    @field_validator("original_sample_number", "appendix_note", "comment")
    @classmethod
    def validate_text_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    @field_validator("growth_media_ids")
    @classmethod
    def validate_growth_media_ids(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is not None:
            v = list(set(filter(None, v)))
            return v if v else None
        return v

    class Config:
        from_attributes = True


class CreateSampleSchema(BaseModel):
    """Схема для создания образца без ID"""
    
    index_letter_id: Optional[int] = Field(None, ge=1, description="ID индексной буквы")
    strain_id: Optional[int] = Field(None, ge=1, description="ID штамма")
    storage_id: Optional[int] = Field(None, ge=1, description="ID хранилища")
    original_sample_number: Optional[str] = Field(None, max_length=100, description="Оригинальный номер образца")
    source_id: Optional[int] = Field(None, ge=1, description="ID источника")
    location_id: Optional[int] = Field(None, ge=1, description="ID местоположения")
    appendix_note: Optional[str] = Field(None, max_length=1000, description="Текст примечания")
    comment: Optional[str] = Field(None, max_length=1000, description="Текст комментария")
    has_photo: bool = Field(default=False, description="Есть ли фото")
    iuk_color_id: Optional[int] = Field(None, ge=1, description="ID цвета ИУК")
    amylase_variant_id: Optional[int] = Field(None, ge=1, description="ID варианта амилазы")
    growth_media_ids: Optional[List[int]] = Field(None, description="Список ID сред роста")
    characteristics: Optional[dict] = Field(None, description="Динамические характеристики образца")
    
    @field_validator("original_sample_number", "appendix_note", "comment")
    @classmethod
    def validate_text_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    @field_validator("growth_media_ids")
    @classmethod
    def validate_growth_media_ids(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is not None:
            v = list(set(filter(None, v)))
            return v if v else None
        return v


class UpdateSampleSchema(BaseModel):
    """Схема для обновления образца без поля has_photo (управляется автоматически)"""
    
    index_letter_id: Optional[int] = Field(None, ge=1, description="ID индексной буквы")
    strain_id: Optional[int] = Field(None, ge=1, description="ID штамма")
    storage_id: Optional[int] = Field(None, ge=1, description="ID хранилища")
    original_sample_number: Optional[str] = Field(None, max_length=100, description="Оригинальный номер образца")
    source_id: Optional[int] = Field(None, ge=1, description="ID источника")
    location_id: Optional[int] = Field(None, ge=1, description="ID местоположения")
    appendix_note: Optional[str] = Field(None, max_length=1000, description="Текст примечания")
    comment: Optional[str] = Field(None, max_length=1000, description="Текст комментария")
    # has_photo исключено - управляется автоматически через сигналы при операциях с фото
    iuk_color_id: Optional[int] = Field(None, ge=1, description="ID цвета ИУК")
    amylase_variant_id: Optional[int] = Field(None, ge=1, description="ID варианта амилазы")
    growth_media_ids: Optional[List[int]] = Field(None, description="Список ID сред роста")
    characteristics: Optional[dict] = Field(None, description="Динамические характеристики образца")
    
    @field_validator("original_sample_number", "appendix_note", "comment")
    @classmethod
    def validate_text_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    @field_validator("growth_media_ids")
    @classmethod
    def validate_growth_media_ids(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is not None:
            v = list(set(filter(None, v)))
            return v if v else None
        return v


@extend_schema(
    methods=['GET'],
    operation_id="samples_list",
    summary="Список образцов",
    description="Получение списка всех образцов с поиском и фильтрацией",
    parameters=[
        OpenApiParameter(name='search', type=str, description='Поисковый запрос'),
        OpenApiParameter(name='strain_id', type=int, description='ID штамма'),
        OpenApiParameter(name='storage_id', type=int, description='ID хранилища'),
        OpenApiParameter(name='page', type=int, description='Номер страницы'),
        OpenApiParameter(name='limit', type=int, description='Количество элементов на странице'),
    ],
    responses={
        200: OpenApiResponse(description="Список образцов"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@extend_schema(
    methods=['POST'],
    operation_id="samples_create",
    summary="Создание образца",
    description="Создание нового образца",
    responses={
        201: OpenApiResponse(description="Образец создан"),
        400: OpenApiResponse(description="Ошибка валидации"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['GET', 'POST'])
def list_samples(request):
    """Список всех образцов с поиском и фильтрацией (GET) или создание нового образца (POST)"""
    if request.method == 'POST':
        # POST request - создание нового образца
        try:
            validated_data = CreateSampleSchema.model_validate(request.data)
            
            # Проверяем существование связанных объектов
            if validated_data.index_letter_id and not IndexLetter.objects.filter(id=validated_data.index_letter_id).exists():
                return Response({'error': f'Индексная буква с ID {validated_data.index_letter_id} не найдена'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            if validated_data.strain_id and not Strain.objects.filter(id=validated_data.strain_id).exists():
                return Response({'error': f'Штамм с ID {validated_data.strain_id} не найден'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            if validated_data.storage_id and not Storage.objects.filter(id=validated_data.storage_id).exists():
                return Response({'error': f'Хранилище с ID {validated_data.storage_id} не найдено'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            if validated_data.source_id and not Source.objects.filter(id=validated_data.source_id).exists():
                return Response({'error': f'Источник с ID {validated_data.source_id} не найден'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            if validated_data.location_id and not Location.objects.filter(id=validated_data.location_id).exists():
                return Response({'error': f'Местоположение с ID {validated_data.location_id} не найдено'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            if validated_data.iuk_color_id and not IUKColor.objects.filter(id=validated_data.iuk_color_id).exists():
                return Response({'error': f'Цвет ИУК с ID {validated_data.iuk_color_id} не найден'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            if validated_data.amylase_variant_id and not AmylaseVariant.objects.filter(id=validated_data.amylase_variant_id).exists():
                return Response({'error': f'Вариант амилазы с ID {validated_data.amylase_variant_id} не найден'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Создаем образец
            with transaction.atomic():
                sample = Sample.objects.create(
                    index_letter_id=validated_data.index_letter_id,
                    strain_id=validated_data.strain_id,
                    storage_id=validated_data.storage_id,
                    original_sample_number=validated_data.original_sample_number,
                    source_id=validated_data.source_id,
                    location_id=validated_data.location_id,
                    appendix_note=validated_data.appendix_note,
                    comment=validated_data.comment,
                    has_photo=validated_data.has_photo,
                    iuk_color_id=validated_data.iuk_color_id,
                    amylase_variant_id=validated_data.amylase_variant_id
                )
                
                # Добавляем среды роста
                if validated_data.growth_media_ids:
                    for medium_id in validated_data.growth_media_ids:
                        if GrowthMedium.objects.filter(id=medium_id).exists():
                            SampleGrowthMedia.objects.create(sample=sample, growth_medium_id=medium_id)
                
                logger.info(f"Created sample: ID {sample.id}")
                
                # Возвращаем данные созданного образца
                sample_data = {
                    'id': sample.id,
                    'original_sample_number': sample.original_sample_number,
                    'strain': {
                        'id': sample.strain.id,
                        'short_code': sample.strain.short_code,
                        'identifier': sample.strain.identifier
                    } if sample.strain else None,
                    'strain_code': sample.strain.short_code if sample.strain else None,
                    'storage': {'id': sample.storage.id, 'name': str(sample.storage)} if sample.storage else None,
                    'storage_name': str(sample.storage) if sample.storage else None,
                    'appendix_note': sample.appendix_note,
                    'comment': sample.comment,
                    'has_photo': sample.has_photo,
                    'created_at': sample.created_at.isoformat() if sample.created_at else None,
                    'updated_at': sample.updated_at.isoformat() if sample.updated_at else None,
                    'growth_media': [
                        {
                            'id': gm.growth_medium.id,
                            'name': gm.growth_medium.name
                        } for gm in sample.growth_media.all()
                    ]
                }
                
                return Response(sample_data, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            return Response({
                'error': 'Ошибки валидации данных',
                'details': e.errors()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Unexpected error in create_sample: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # GET request - список образцов
    try:
        page = max(1, int(request.GET.get('page', 1)))
        limit = max(1, min(int(request.GET.get('limit', 50)), 1000))
        offset = (page - 1) * limit
        
        # Полнотекстовый поиск
        search_query = request.GET.get('search', '').strip()
        
        # Фильтры
        strain_id = request.GET.get('strain_id')
        storage_id = request.GET.get('storage_id')
        source_id = request.GET.get('source_id')
        location_id = request.GET.get('location_id')
        has_photo = request.GET.get('has_photo')
        
        # Параметры сортировки
        sort_by = request.GET.get('sort_by', 'id')
        sort_direction = request.GET.get('sort_direction', 'asc')
        
        # Маппинг полей для сортировки
        sort_fields_mapping = {
            'id': 'id',
            'original_sample_number': 'original_sample_number',
            'strain': 'strain__short_code',
            'storage': 'storage__box_id',
            'source': 'source__organism_name',
            'location': 'location__name',
            'created_at': 'created_at',
            'updated_at': 'updated_at'
        }
        
        # Проверяем валидность поля сортировки
        if sort_by not in sort_fields_mapping:
            sort_by = 'id'
        
        # Формируем строку сортировки
        sort_field = sort_fields_mapping[sort_by]
        if sort_direction.lower() == 'desc':
            sort_field = f'-{sort_field}'
        
        queryset = Sample.objects.select_related(
            'index_letter', 'strain', 'storage', 'source', 'location',
            'iuk_color', 'amylase_variant'
        ).prefetch_related(
            Prefetch('growth_media', queryset=SampleGrowthMedia.objects.select_related('growth_medium'))
        )
        
        if search_query:
            queryset = queryset.filter(
                Q(original_sample_number__icontains=search_query) |
                Q(appendix_note__icontains=search_query) |
                Q(comment__icontains=search_query) |
                Q(strain__short_code__icontains=search_query) |
                Q(strain__identifier__icontains=search_query)
            )
        
        # Применяем фильтры
        if strain_id:
            queryset = queryset.filter(strain_id=strain_id)
        if storage_id:
            queryset = queryset.filter(storage_id=storage_id)
        if source_id:
            queryset = queryset.filter(source_id=source_id)
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        has_photo_value = None
        if has_photo is not None:
            has_photo_value = has_photo.lower() == 'true'
            queryset = queryset.filter(has_photo=has_photo_value)

        # Применяем сортировку
        queryset = queryset.order_by(sort_field)

        total_count = queryset.count()
        samples = queryset[offset:offset + limit]
        
        # Формируем данные с дополнительной информацией
        data = []
        for sample in samples:
            sample_data = SampleSchema.model_validate(sample).model_dump()
            
            # Добавляем информацию о связанных объектах
            sample_data['index_letter'] = sample.index_letter.letter_value if sample.index_letter else None
            sample_data['strain_code'] = sample.strain.short_code if sample.strain else None
            sample_data['strain'] = {'id': sample.strain.id, 'short_code': sample.strain.short_code} if sample.strain else None
            if sample.storage:
                storage_display = str(sample.storage)
                sample_data['storage_name'] = storage_display
                sample_data['storage'] = {
                    'id': sample.storage.id,
                    'box_id': sample.storage.box_id,
                    'cell_id': sample.storage.cell_id,
                    'name': storage_display
                }
            else:
                sample_data['storage_name'] = None
                sample_data['storage'] = None
            sample_data['source_name'] = sample.source.organism_name if sample.source else None
            sample_data['location_name'] = sample.location.name if sample.location else None
            sample_data['iuk_color_name'] = sample.iuk_color.name if sample.iuk_color else None
            sample_data['amylase_variant_name'] = sample.amylase_variant.name if sample.amylase_variant else None
            
            # Добавляем среды роста
            growth_media = [sgm.growth_medium.name for sgm in sample.growth_media.all()]
            sample_data['growth_media'] = growth_media
            
            # Добавляем поля времени
            sample_data['created_at'] = sample.created_at.isoformat() if sample.created_at else None
            sample_data['updated_at'] = sample.updated_at.isoformat() if sample.updated_at else None
            
            data.append(sample_data)

        has_next = offset + limit < total_count
        has_prev = page > 1
        shown = len(data)
        total_pages = (total_count + limit - 1) // limit if limit else 0
        pagination = {
            'total': total_count,
            'shown': shown,
            'page': page,
            'limit': limit,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_previous': has_prev,
            'offset': offset
        }
        filters_applied = {
            key: value for key, value in {
                'strain_id': strain_id,
                'storage_id': storage_id,
                'source_id': source_id,
                'location_id': location_id,
                'has_photo': has_photo_value,
            }.items() if value not in (None, '')
        }

        return Response({
            'results': data,
            'samples': data,
            'total': total_count,
            'page': page,
            'limit': limit,
            'has_next': has_next,
            'has_prev': has_prev,
            'has_previous': has_prev,
            'pagination': pagination,
            'shown': shown,
            'search_query': search_query or None,
            'filters_applied': filters_applied or None,
            'sort_by': sort_by,
            'sort_direction': sort_direction
        })
        
    except Exception as e:
        logger.error(f"Error in list_samples: {e}")
        return Response(
            {'error': f'Ошибка получения списка образцов: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    operation_id="sample_detail",
    summary="Получение образца",
    description="Получение образца по ID",
    responses={
        200: OpenApiResponse(description="Данные образца"),
        404: OpenApiResponse(description="Образец не найден"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['GET'])
def get_sample(request, sample_id):
    """Получение образца по ID"""
    try:
        sample = Sample.objects.select_related(
            'index_letter', 'strain', 'storage', 'source', 'location',
            'iuk_color', 'amylase_variant'
        ).prefetch_related(
            Prefetch('growth_media', queryset=SampleGrowthMedia.objects.select_related('growth_medium')),
            'photos'
        ).get(id=sample_id)
        
        # Создаем правильную структуру данных для фронтенда
        data = {
            'id': sample.id,
            'original_sample_number': sample.original_sample_number,
            'appendix_note': sample.appendix_note,
            'comment': sample.comment,
            'has_photo': sample.has_photo,
        }
        
        # Добавляем связанные объекты в правильном формате
        if sample.index_letter:
            data['index_letter'] = {
                'id': sample.index_letter.id,
                'letter_value': sample.index_letter.letter_value
            }
        else:
            data['index_letter'] = None
            
        if sample.strain:
            data['strain'] = {
                'id': sample.strain.id,
                'short_code': sample.strain.short_code,
                'identifier': sample.strain.identifier,
                'rrna_taxonomy': sample.strain.rrna_taxonomy
            }
        else:
            data['strain'] = None
            
        if sample.storage:
            data['storage'] = {
                'id': sample.storage.id,
                'box_id': sample.storage.box_id,
                'cell_id': sample.storage.cell_id
            }
        else:
            data['storage'] = None
            
        if sample.source:
            data['source'] = {
                'id': sample.source.id,
                'organism_name': sample.source.organism_name,
                'source_type': sample.source.source_type.name,
                'category': sample.source.category.name
            }
        else:
            data['source'] = None
            
        if sample.location:
            data['location'] = {
                'id': sample.location.id,
                'name': sample.location.name
            }
        else:
            data['location'] = None
            
        if sample.iuk_color:
            data['iuk_color'] = {
                'id': sample.iuk_color.id,
                'name': sample.iuk_color.name,
                'hex_code': sample.iuk_color.hex_code
            }
        else:
            data['iuk_color'] = None
            
        if sample.amylase_variant:
            data['amylase_variant'] = {
                'id': sample.amylase_variant.id,
                'name': sample.amylase_variant.name,
                'description': sample.amylase_variant.description
            }
        else:
            data['amylase_variant'] = None
        
        # Добавляем среды роста
        growth_media = []
        for sgm in sample.growth_media.all():
            growth_media.append({
                'id': sgm.growth_medium.id,
                'name': sgm.growth_medium.name,
                'description': sgm.growth_medium.description
            })
        data['growth_media'] = growth_media
        
        # Добавляем временные метки
        data['created_at'] = sample.created_at.isoformat() if sample.created_at else None
        data['updated_at'] = sample.updated_at.isoformat() if sample.updated_at else None
        
        # Добавляем фотографии
        photos = []
        for photo in sample.photos.all():
            photos.append({
                'id': photo.id,
                'image': photo.image.url if photo.image else None,
                'uploaded_at': photo.uploaded_at.isoformat() if photo.uploaded_at else None
            })
        data['photos'] = photos
        
        # Добавляем характеристики
        characteristics = {}
        sample_characteristics = SampleCharacteristicValue.objects.filter(
            sample=sample
        ).select_related('characteristic')
        
        for char_value in sample_characteristics:
            char = char_value.characteristic
            value_data = {
                'characteristic_id': char.id,
                'characteristic_name': char.name,
                'characteristic_type': char.characteristic_type,
            }
            
            # Добавляем значение в зависимости от типа
            if char.characteristic_type == 'boolean':
                value_data['value'] = char_value.boolean_value
            elif char.characteristic_type == 'text':
                value_data['value'] = char_value.text_value
            elif char.characteristic_type == 'select':
                value_data['value'] = char_value.select_value
            else:
                value_data['value'] = None
                
            characteristics[char.name] = value_data
            
        data['characteristics'] = characteristics
        
        return Response(data)
    except Sample.DoesNotExist:
        return Response(
            {'error': f'Образец с ID {sample_id} не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in get_sample: {e}")
        return Response(
            {'error': f'Ошибка получения образца: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@csrf_exempt
def create_sample(request):
    """Создание нового образца"""
    try:
        validated_data = CreateSampleSchema.model_validate(request.data)
        
        # Проверяем существование связанных объектов
        if validated_data.index_letter_id and not IndexLetter.objects.filter(id=validated_data.index_letter_id).exists():
            return Response({'error': f'Индексная буква с ID {validated_data.index_letter_id} не найдена'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if validated_data.strain_id and not Strain.objects.filter(id=validated_data.strain_id).exists():
            return Response({'error': f'Штамм с ID {validated_data.strain_id} не найден'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if validated_data.storage_id and not Storage.objects.filter(id=validated_data.storage_id).exists():
            return Response({'error': f'Хранилище с ID {validated_data.storage_id} не найдено'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if validated_data.source_id and not Source.objects.filter(id=validated_data.source_id).exists():
            return Response({'error': f'Источник с ID {validated_data.source_id} не найден'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if validated_data.location_id and not Location.objects.filter(id=validated_data.location_id).exists():
            return Response({'error': f'Местоположение с ID {validated_data.location_id} не найдено'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if validated_data.iuk_color_id and not IUKColor.objects.filter(id=validated_data.iuk_color_id).exists():
            return Response({'error': f'Цвет ИУК с ID {validated_data.iuk_color_id} не найден'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if validated_data.amylase_variant_id and not AmylaseVariant.objects.filter(id=validated_data.amylase_variant_id).exists():
            return Response({'error': f'Вариант амилазы с ID {validated_data.amylase_variant_id} не найден'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Создаем образец
        with transaction.atomic():
            sample = Sample.objects.create(
                index_letter_id=validated_data.index_letter_id,
                strain_id=validated_data.strain_id,
                storage_id=validated_data.storage_id,
                original_sample_number=validated_data.original_sample_number,
                source_id=validated_data.source_id,
                location_id=validated_data.location_id,
                appendix_note=validated_data.appendix_note,
                comment=validated_data.comment,
                has_photo=validated_data.has_photo,
                iuk_color_id=validated_data.iuk_color_id,
                amylase_variant_id=validated_data.amylase_variant_id
            )
            
            # Добавляем среды роста
            if validated_data.growth_media_ids:
                for medium_id in validated_data.growth_media_ids:
                    if GrowthMedium.objects.filter(id=medium_id).exists():
                        SampleGrowthMedia.objects.create(sample=sample, growth_medium_id=medium_id)
            
            logger.info(f"Created sample: ID {sample.id}")
        
        # Возвращаем данные созданного образца
        sample_data = {
            'id': sample.id,
            'original_sample_number': sample.original_sample_number,
            'strain': {
                'id': sample.strain.id,
                'short_code': sample.strain.short_code,
                'identifier': sample.strain.identifier
            } if sample.strain else None,
            'strain_code': sample.strain.short_code if sample.strain else None,
            'storage': {'id': sample.storage.id, 'name': str(sample.storage)} if sample.storage else None,
            'storage_name': str(sample.storage) if sample.storage else None,
            'appendix_note': sample.appendix_note,
            'comment': sample.comment,
            'has_photo': sample.has_photo,
            'created_at': sample.created_at.isoformat() if sample.created_at else None,
            'updated_at': sample.updated_at.isoformat() if sample.updated_at else None,
            'growth_media': [
                {
                    'id': gm.growth_medium.id,
                    'name': gm.growth_medium.name
                } for gm in sample.growth_media.all()
            ]
        }
        
        return Response(sample_data, status=status.HTTP_201_CREATED)
    
    except ValidationError as e:
        return Response({
            'error': 'Ошибки валидации данных',
            'details': e.errors()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except IntegrityError as e:
        logger.warning(f"IntegrityError in create_sample: {e}")
        # Сбрасываем последовательность и пытаемся снова
        reset_sequence(Sample)
        try:
            with transaction.atomic():
                sample = Sample.objects.create(
                    index_letter_id=validated_data.index_letter_id,
                    strain_id=validated_data.strain_id,
                    storage_id=validated_data.storage_id,
                    original_sample_number=validated_data.original_sample_number,
                    source_id=validated_data.source_id,
                    location_id=validated_data.location_id,
                    appendix_note=validated_data.appendix_note,
                    comment=validated_data.comment,
                    has_photo=validated_data.has_photo,
                    iuk_color_id=validated_data.iuk_color_id,
                    amylase_variant_id=validated_data.amylase_variant_id
                )
                
                # Добавляем среды роста
                if validated_data.growth_media_ids:
                    for medium_id in validated_data.growth_media_ids:
                        if GrowthMedium.objects.filter(id=medium_id).exists():
                            SampleGrowthMedia.objects.create(sample=sample, growth_medium_id=medium_id)
                
                logger.info(f"Created sample after sequence reset: ID {sample.id}")
                
                # Возвращаем данные созданного образца
                sample_data = {
                    'id': sample.id,
                    'original_sample_number': sample.original_sample_number,
                    'strain': {
                        'id': sample.strain.id,
                        'short_code': sample.strain.short_code,
                        'identifier': sample.strain.identifier
                    } if sample.strain else None,
                    'strain_code': sample.strain.short_code if sample.strain else None,
                    'storage': {'id': sample.storage.id, 'name': str(sample.storage)} if sample.storage else None,
                    'storage_name': str(sample.storage) if sample.storage else None,
                    'appendix_note': sample.appendix_note,
                    'comment': sample.comment,
                    'has_photo': sample.has_photo,
                    'created_at': sample.created_at.isoformat() if sample.created_at else None,
                    'updated_at': sample.updated_at.isoformat() if sample.updated_at else None,
                    'growth_media': [
                        {
                            'id': gm.growth_medium.id,
                            'name': gm.growth_medium.name
                        } for gm in sample.growth_media.all()
                    ]
                }
                
                return Response(sample_data, status=status.HTTP_201_CREATED)
                
        except Exception as retry_e:
            logger.error(f"Failed to create sample even after sequence reset: {retry_e}")
            return Response({
                'error': 'Не удалось создать образец'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Unexpected error in create_sample: {e}")
        return Response({
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@csrf_exempt
def update_sample(request, sample_id):
    """Обновление образца"""

    logger.info(f"🔧 update_sample called for sample {sample_id}")
    logger.info(f"🔧 Request data: {request.data}")
    
    try:
        # Получаем образец
        try:
            sample = Sample.objects.get(id=sample_id)
        except Sample.DoesNotExist:
            return Response({
                'error': f'Образец с ID {sample_id} не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Валидируем данные
        validated_data = UpdateSampleSchema.model_validate(request.data)
        
        # Проверяем существование связанных объектов (аналогично create_sample)
        # ... (код проверки аналогичен create_sample)
        
        # Обновление образца
        with transaction.atomic():
            # Обновляем поля образца, исключая has_photo (управляется автоматически через сигналы) и characteristics
            for field, value in validated_data.model_dump(exclude={'growth_media_ids', 'has_photo', 'characteristics'}).items():
                setattr(sample, field, value)
            sample.save()
            
            # Обновляем среды роста
            SampleGrowthMedia.objects.filter(sample=sample).delete()
            if validated_data.growth_media_ids:
                for medium_id in validated_data.growth_media_ids:
                    if GrowthMedium.objects.filter(id=medium_id).exists():
                        SampleGrowthMedia.objects.create(sample=sample, growth_medium_id=medium_id)
            
            # Обрабатываем характеристики
            if validated_data.characteristics:
                logger.info(f"🔧 Processing characteristics: {validated_data.characteristics}")
                for char_name, char_data in validated_data.characteristics.items():
                    try:
                        characteristic = SampleCharacteristic.objects.get(name=char_name)
                        
                        # Получаем или создаем значение характеристики
                        char_value, created = SampleCharacteristicValue.objects.get_or_create(
                            sample=sample,
                            characteristic=characteristic,
                            defaults={}
                        )
                        
                        # Устанавливаем значение в зависимости от типа
                        if characteristic.characteristic_type == 'boolean':
                            char_value.boolean_value = bool(char_data.get('value', False))
                            char_value.text_value = None
                            char_value.select_value = None
                        elif characteristic.characteristic_type == 'text':
                            char_value.text_value = str(char_data.get('value', ''))
                            char_value.boolean_value = None
                            char_value.select_value = None
                        elif characteristic.characteristic_type == 'select':
                            char_value.select_value = str(char_data.get('value', ''))
                            char_value.boolean_value = None
                            char_value.text_value = None
                        
                        char_value.save()
                        logger.info(f"🔧 Saved characteristic '{char_name}' with value: {char_data}")
                        
                    except SampleCharacteristic.DoesNotExist:
                        logger.warning(f"🔧 Characteristic '{char_name}' not found, skipping")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing characteristic '{char_name}': {e}")
                        continue
            
            logger.info(f"Updated sample: ID {sample.id}")
        
        # Возвращаем данные обновленного образца
        sample_data = {
            'id': sample.id,
            'original_sample_number': sample.original_sample_number,
            'strain': {
                'id': sample.strain.id,
                'short_code': sample.strain.short_code,
                'identifier': sample.strain.identifier
            } if sample.strain else None,
            'strain_code': sample.strain.short_code if sample.strain else None,
            'storage': str(sample.storage) if sample.storage else None,
            'storage_name': str(sample.storage) if sample.storage else None,
            'appendix_note': sample.appendix_note,
            'comment': sample.comment,
            'has_photo': sample.has_photo,
            'created_at': sample.created_at.isoformat() if sample.created_at else None,
            'updated_at': sample.updated_at.isoformat() if sample.updated_at else None,
            'growth_media': [
                {
                    'id': gm.growth_medium.id,
                    'name': gm.growth_medium.name
                } for gm in sample.growth_media.all()
            ]
        }
        
        # Добавляем характеристики в ответ
        characteristics = {}
        sample_characteristics = SampleCharacteristicValue.objects.filter(
            sample=sample
        ).select_related('characteristic')
        
        for char_value in sample_characteristics:
            char = char_value.characteristic
            value_data = {
                'characteristic_id': char.id,
                'characteristic_name': char.name,
                'characteristic_type': char.characteristic_type,
            }
            
            # Добавляем значение в зависимости от типа
            if char.characteristic_type == 'boolean':
                value_data['value'] = char_value.boolean_value
            elif char.characteristic_type == 'text':
                value_data['value'] = char_value.text_value
            elif char.characteristic_type == 'select':
                value_data['value'] = char_value.select_value
            else:
                value_data['value'] = None
                
            characteristics[char.name] = value_data
            
        sample_data['characteristics'] = characteristics
        
        return Response(sample_data, status=status.HTTP_200_OK)
    
    except ValidationError as e:
        return Response({
            'error': 'Ошибки валидации данных',
            'details': e.errors()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Unexpected error in update_sample: {e}")
        return Response({
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@csrf_exempt
def delete_sample(request, sample_id):
    """Удаление образца"""
    try:
        # Получаем образец
        try:
            sample = Sample.objects.get(id=sample_id)
        except Sample.DoesNotExist:
            return Response({
                'error': f'Образец с ID {sample_id} не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Сохраняем информацию об образце для ответа
        sample_info = {
            'id': sample.id,
            'original_sample_number': sample.original_sample_number
        }
        
        # Удаляем образец (связанные объекты удалятся каскадно)
        with transaction.atomic():
            sample.delete()
            logger.info(f"Deleted sample: ID {sample_info['id']}")
        
        return Response({
            'message': f"Образец ID {sample_info['id']} успешно удален",
            'deleted_sample': sample_info
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Unexpected error in delete_sample: {e}")
        return Response({
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@csrf_exempt
def validate_sample(request):
    """Валидация данных образца без сохранения"""
    try:
        validated_data = CreateSampleSchema.model_validate(request.data)
        
        # Проверяем существование связанных объектов
        validation_errors = []
        
        if validated_data.index_letter_id and not IndexLetter.objects.filter(id=validated_data.index_letter_id).exists():
            validation_errors.append({
                'type': 'value_error',
                'loc': ['index_letter_id'],
                'msg': f'Индексная буква с ID {validated_data.index_letter_id} не найдена'
            })
        
        if validated_data.strain_id and not Strain.objects.filter(id=validated_data.strain_id).exists():
            validation_errors.append({
                'type': 'value_error',
                'loc': ['strain_id'],
                'msg': f'Штамм с ID {validated_data.strain_id} не найден'
            })
        
        if validated_data.storage_id and not Storage.objects.filter(id=validated_data.storage_id).exists():
            validation_errors.append({
                'type': 'value_error',
                'loc': ['storage_id'],
                'msg': f'Хранилище с ID {validated_data.storage_id} не найдено'
            })
        
        if validated_data.source_id and not Source.objects.filter(id=validated_data.source_id).exists():
            validation_errors.append({
                'type': 'value_error',
                'loc': ['source_id'],
                'msg': f'Источник с ID {validated_data.source_id} не найден'
            })
        
        if validated_data.location_id and not Location.objects.filter(id=validated_data.location_id).exists():
            validation_errors.append({
                'type': 'value_error',
                'loc': ['location_id'],
                'msg': f'Местоположение с ID {validated_data.location_id} не найдено'
            })
        
        if validated_data.iuk_color_id and not IUKColor.objects.filter(id=validated_data.iuk_color_id).exists():
            validation_errors.append({
                'type': 'value_error',
                'loc': ['iuk_color_id'],
                'msg': f'Цвет ИУК с ID {validated_data.iuk_color_id} не найден'
            })
        
        # Примечание: amylase_variant_id, appendix_note_id, comment_id и growth_media_ids 
        # не являются частью CreateSampleSchema, поэтому их проверка не нужна
        
        if validation_errors:
            return Response({
                'valid': False,
                'errors': validation_errors,
                'message': 'Ошибки валидации данных'
            })
        
        return Response({
            'valid': True,
            'data': validated_data.model_dump(),
            'errors': {},
            'message': 'Данные образца валидны'
        })
    except ValidationError as e:
        return Response({
            'valid': False,
            'errors': e.errors(),
            'message': 'Ошибки валидации данных'
        })
    except Exception as e:
        logger.error(f"Unexpected error in validate_sample: {e}")
        return Response({
            'valid': False,
            'errors': {'general': [str(e)]},
            'message': 'Неожиданная ошибка'
        })


# Константы для загрузки изображений
MAX_IMAGE_SIZE_MB = 1
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png"]


def _validate_uploaded_image(uploaded_file):
    """Валидация загружаемого изображения"""
    if uploaded_file.content_type not in ALLOWED_IMAGE_TYPES:
        raise DjangoValidationError("Разрешены только JPEG и PNG файлы")

    if uploaded_file.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise DjangoValidationError("Максимальный размер файла 1 МБ")


@extend_schema(
    summary="Загрузка фотографий образца",
    description="Загружает одну или несколько фотографий для образца",
    responses={
        200: OpenApiResponse(description="Фотографии успешно загружены"),
        400: OpenApiResponse(description="Ошибка валидации"),
        404: OpenApiResponse(description="Образец не найден"),
    }
)
@api_view(["POST"])
@csrf_exempt
def upload_sample_photos(request, sample_id):
    """Загружает одну или несколько фотографий для образца."""
    try:
        sample = Sample.objects.get(id=sample_id)
    except Sample.DoesNotExist:
        return Response({"error": "Образец не найден"}, status=status.HTTP_404_NOT_FOUND)

    if not request.FILES:
        return Response({"error": "Файлы не переданы"}, status=status.HTTP_400_BAD_REQUEST)

    created = []
    errors = []

    for file_obj in request.FILES.getlist("photos"):
        try:
            _validate_uploaded_image(file_obj)
            photo = sample.photos.create(image=file_obj)
            created.append({"id": photo.id, "url": photo.image.url})
        except DjangoValidationError as e:
            errors.append(str(e))
        except Exception as e:
            logger.exception("Ошибка при загрузке фото: %s", e)
            errors.append(str(e))

    # Обновляем флаг has_photo если были загружены фотографии
    if created:
        sample.has_photo = True
        sample.save(update_fields=['has_photo'])

    return Response({"created": created, "errors": errors})


@extend_schema(
    summary="Удаление фотографии образца",
    description="Удаляет фотографию образца по ID",
    responses={
        200: OpenApiResponse(description="Фотография успешно удалена"),
        404: OpenApiResponse(description="Фотография не найдена"),
    }
)
@api_view(["DELETE"])
@csrf_exempt
def delete_sample_photo(request, sample_id, photo_id):
    """Удаляет фотографию образца."""
    try:
        photo = SamplePhoto.objects.get(id=photo_id, sample_id=sample_id)
        photo.delete()
        
        # Проверяем, остались ли еще фотографии у образца
        sample = Sample.objects.get(id=sample_id)
        if not sample.photos.exists():
            sample.has_photo = False
            sample.save(update_fields=['has_photo'])
        
        return Response({"message": "Фото удалено"})
    except SamplePhoto.DoesNotExist:
        return Response({"error": "Фото не найдено"}, status=status.HTTP_404_NOT_FOUND)
    except Sample.DoesNotExist:
        return Response({"error": "Образец не найден"}, status=status.HTTP_404_NOT_FOUND)


# Schemas for characteristics management
class CharacteristicOptionSchema(BaseModel):
    """Схема для опций характеристик"""
    value: str = Field(min_length=1, max_length=200, description="Значение опции")
    display_name: str = Field(min_length=1, max_length=200, description="Отображаемое название")
    color: Optional[str] = Field(None, max_length=20, description="Цвет опции")


class CreateCharacteristicSchema(BaseModel):
    """Схема для создания характеристики"""
    name: str = Field(min_length=1, max_length=100, description="Название характеристики")
    display_name: str = Field(min_length=1, max_length=150, description="Отображаемое название")
    characteristic_type: str = Field(description="Тип характеристики")
    options: Optional[List[str]] = Field(None, description="Опции для select типа")
    is_active: bool = Field(default=True, description="Активна ли характеристика")
    order: int = Field(default=0, description="Порядок отображения")

    @field_validator('characteristic_type')
    @classmethod
    def validate_type(cls, v):
        if v not in ['boolean', 'text', 'select']:
            raise ValueError('Тип должен быть boolean, text или select')
        return v


# Characteristics management endpoints
@extend_schema(
    summary="Получение списка характеристик",
    description="Возвращает список всех активных характеристик образцов",
    responses={
        200: OpenApiResponse(description="Список характеристик успешно получен"),
        500: OpenApiResponse(description="Внутренняя ошибка сервера"),
    }
)
@api_view(['GET'])
@csrf_exempt
def list_characteristics(request):
    """Получение списка всех активных характеристик"""
    try:
        characteristics = SampleCharacteristic.objects.filter(is_active=True).order_by('display_name')
        
        result = []
        for char in characteristics:
            char_data = {
                'id': char.id,
                'name': char.name,
                'display_name': char.display_name,
                'characteristic_type': char.characteristic_type,
                'options': char.options or [],
                'is_active': char.is_active,
                'order': char.order
            }
            
            result.append(char_data)
        
        return Response(result)
    
    except Exception as e:
        logger.error(f"Error in list_characteristics: {e}")
        return Response({
            'error': f'Ошибка при получении характеристик: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Создание новой характеристики",
    description="Создает новую характеристику для образцов",
    request=CreateCharacteristicSchema,
    responses={
        200: OpenApiResponse(description="Характеристика успешно создана"),
        400: OpenApiResponse(description="Ошибка валидации данных"),
        500: OpenApiResponse(description="Внутренняя ошибка сервера"),
    }
)
@api_view(['POST'])
@csrf_exempt
def create_characteristic(request):
    """Создание новой характеристики"""
    try:
        data = CreateCharacteristicSchema(**request.data)
        
        with transaction.atomic():
            characteristic = SampleCharacteristic.objects.create(
                name=data.name,
                display_name=data.display_name,
                characteristic_type=data.characteristic_type,
                options=data.options,
                is_active=data.is_active,
                order=data.order
            )
            
            return Response({
                'id': characteristic.id,
                'message': f'Характеристика "{characteristic.display_name}" успешно создана'
            })
    
    except ValidationError as e:
        return Response({
            'error': 'Ошибка валидации данных',
            'details': e.errors()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Error in create_characteristic: {e}")
        return Response({
            'error': f'Ошибка при создании характеристики: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Обновление характеристики",
    description="Обновляет существующую характеристику",
    request=CreateCharacteristicSchema,
    responses={
        200: OpenApiResponse(description="Характеристика успешно обновлена"),
        400: OpenApiResponse(description="Ошибка валидации данных"),
        404: OpenApiResponse(description="Характеристика не найдена"),
        500: OpenApiResponse(description="Внутренняя ошибка сервера"),
    }
)
@api_view(['PUT'])
@csrf_exempt
def update_characteristic(request, characteristic_id):
    """Обновление характеристики"""
    try:
        characteristic = SampleCharacteristic.objects.get(id=characteristic_id)
    except SampleCharacteristic.DoesNotExist:
        return Response({
            'error': f'Характеристика с ID {characteristic_id} не найдена'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        data = CreateCharacteristicSchema(**request.data)
        
        with transaction.atomic():
            characteristic.name = data.name
            characteristic.display_name = data.display_name
            characteristic.characteristic_type = data.characteristic_type
            characteristic.options = data.options
            characteristic.is_active = data.is_active
            characteristic.order = data.order
            characteristic.save()
            
            return Response({
                'id': characteristic.id,
                'message': f'Характеристика "{characteristic.display_name}" успешно обновлена'
            })
    
    except ValidationError as e:
        return Response({
            'error': 'Ошибка валидации данных',
            'details': e.errors()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Error in update_characteristic: {e}")
        return Response({
            'error': f'Ошибка при обновлении характеристики: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Удаление характеристики",
    description="Удаляет характеристику (мягкое удаление)",
    responses={
        200: OpenApiResponse(description="Характеристика успешно удалена"),
        404: OpenApiResponse(description="Характеристика не найдена"),
        500: OpenApiResponse(description="Внутренняя ошибка сервера"),
    }
)
@api_view(['DELETE'])
@csrf_exempt
def delete_characteristic(request, characteristic_id):
    """Удаление характеристики (мягкое удаление)"""
    try:
        characteristic = SampleCharacteristic.objects.get(id=characteristic_id)
    except SampleCharacteristic.DoesNotExist:
        return Response({
            'error': f'Характеристика с ID {characteristic_id} не найдена'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        with transaction.atomic():
            # Мягкое удаление - помечаем как неактивную
            characteristic.is_active = False
            characteristic.save()
            
            # Также деактивируем все опции
            SampleCharacteristicOption.objects.filter(characteristic=characteristic).update(is_active=False)
            
            return Response({
                'message': f'Характеристика "{characteristic.display_name}" успешно удалена'
            })
    
    except Exception as e:
        logger.error(f"Error in delete_characteristic: {e}")
        return Response({
            'error': f'Ошибка при удалении характеристики: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
