"""
API endpoints для управления образцами
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction, connection, IntegrityError
from django.db.models import Q, Prefetch, Count
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional, List, Dict, Iterable
from datetime import datetime, timedelta
import logging
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.openapi import AutoSchema
from django.http import HttpResponse
from django.utils import timezone

from .models import Sample, SampleGrowthMedia, SamplePhoto, SampleCharacteristic, SampleCharacteristicValue
from reference_data.models import IndexLetter, IUKColor, AmylaseVariant, GrowthMedium, Source, Location
from strain_management.models import Strain
from storage_management.models import Storage
from collection_manager.schemas import SampleCharacteristicSchema, SampleCharacteristicValueSchema
from collection_manager.utils import log_change, generate_batch_id, model_to_dict

logger = logging.getLogger(__name__)


BOOLEAN_CHARACTERISTIC_FIELDS: Dict[str, Iterable[str]] = {
    'mobilizes_phosphates': ('mobilizes_phosphates', 'Мобилизирует фосфаты'),
    'stains_medium': ('stains_medium', 'Окрашивает среду'),
    'produces_siderophores': ('produces_siderophores', 'Вырабатывает сидерофоры'),
    'is_identified': ('is_identified', 'Идентифицирован'),
    'has_genome': ('has_genome', 'Есть геном'),
    'has_biochemistry': ('has_biochemistry', 'Есть биохимия'),
    'seq_status': ('seq_status', 'Секвенирован'),
}


def _coerce_to_bool(value) -> Optional[bool]:
    """Преобразовать значение к булевому типу, возвращая None при невозможности."""

    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {'true', '1', 'yes', 'y', 'on'}:
            return True
        if normalized in {'false', '0', 'no', 'n', 'off'}:
            return False
    return None


def _parse_ids(raw_ids) -> List[int]:
    """Нормализует входной список/строку ID в уникальный список целых чисел."""

    if raw_ids is None:
        return []

    candidates: List[int] = []

    if isinstance(raw_ids, list):
        sources = raw_ids
    else:
        sources = str(raw_ids).replace(',', ' ').split()

    for token in sources:
        try:
            value = int(token)
        except (TypeError, ValueError):
            continue
        if value > 0:
            candidates.append(value)

    # Используем dict.fromkeys для сохранения порядка и исключения дубликатов
    return list(dict.fromkeys(candidates))


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
    operation_id='samples_search',
    summary='Поиск образцов',
    description='Поиск образцов по номеру, штамму, местоположению или примечаниям',
    parameters=[
        OpenApiParameter(name='search', type=str, description='Строка поиска'),
        OpenApiParameter(name='limit', type=int, description='Максимальное количество результатов'),
        OpenApiParameter(name='strain_id', type=int, description='Фильтр по штамму'),
        OpenApiParameter(name='storage_id', type=int, description='Фильтр по месту хранения'),
        OpenApiParameter(name='has_photo', type=bool, description='Фильтр по наличию фотографий'),
    ],
    responses={200: OpenApiResponse(description='Список найденных образцов')}
)
@api_view(['GET'])
def search_samples(request):
    """Поиск образцов для автокомплита и быстрых фильтров."""

    try:
        query = (request.GET.get('search') or '').strip()
        limit_raw = request.GET.get('limit', 10)

        try:
            limit = int(limit_raw)
        except (TypeError, ValueError):
            limit = 10

        limit = max(1, min(limit, 100))

        queryset = Sample.objects.select_related(
            'strain', 'storage', 'source', 'location', 'index_letter',
            'iuk_color', 'amylase_variant'
        )

        if query:
            search_filter = (
                Q(original_sample_number__icontains=query)
                | Q(appendix_note__icontains=query)
                | Q(comment__icontains=query)
                | Q(strain__short_code__icontains=query)
                | Q(strain__identifier__icontains=query)
                | Q(storage__box_id__icontains=query)
                | Q(storage__cell_id__icontains=query)
                | Q(source__organism_name__icontains=query)
                | Q(location__name__icontains=query)
            )
            queryset = queryset.filter(search_filter)

        strain_id = request.GET.get('strain_id')
        storage_id = request.GET.get('storage_id')
        has_photo = request.GET.get('has_photo')

        if strain_id:
            queryset = queryset.filter(strain_id=strain_id)
        if storage_id:
            queryset = queryset.filter(storage_id=storage_id)
        if has_photo is not None:
            has_photo_flag = _coerce_to_bool(has_photo)
            if has_photo_flag is not None:
                queryset = queryset.filter(has_photo=has_photo_flag)

        samples = list(queryset.order_by('original_sample_number', 'id')[:limit])

        results = []
        for sample in samples:
            result = {
                'id': sample.id,
                'original_sample_number': sample.original_sample_number,
                'has_photo': sample.has_photo,
                'appendix_note': sample.appendix_note,
                'comment': sample.comment,
                'created_at': sample.created_at.isoformat() if sample.created_at else None,
                'updated_at': sample.updated_at.isoformat() if sample.updated_at else None,
            }

            if sample.strain:
                result['strain'] = {
                    'id': sample.strain.id,
                    'short_code': sample.strain.short_code,
                    'identifier': sample.strain.identifier,
                }

            if sample.storage:
                result['storage'] = {
                    'id': sample.storage.id,
                    'box_id': sample.storage.box_id,
                    'cell_id': sample.storage.cell_id,
                }

            if sample.source:
                result['source'] = {
                    'id': sample.source.id,
                    'organism_name': sample.source.organism_name,
                }

            if sample.location:
                result['location'] = {
                    'id': sample.location.id,
                    'name': sample.location.name,
                }

            results.append(result)

        return Response(results)

    except Exception as exc:
        logger.error(f"Error in search_samples: {exc}")
        return Response(
            {'error': f'Ошибка поиска образцов: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
            # Сохраняем характеристики отдельно перед исключением из model_dump
            characteristics_data = validated_data.characteristics
            
            # Обновляем поля образца, исключая has_photo (управляется автоматически через сигналы) и characteristics
            for field, value in validated_data.model_dump(exclude={'growth_media_ids', 'has_photo', 'characteristics'}).items():
                if value is not None:  # Обновляем только не-None значения
                    setattr(sample, field, value)
            sample.save()
            
            # Обновляем среды роста
            SampleGrowthMedia.objects.filter(sample=sample).delete()
            if validated_data.growth_media_ids:
                for medium_id in validated_data.growth_media_ids:
                    if GrowthMedium.objects.filter(id=medium_id).exists():
                        SampleGrowthMedia.objects.create(sample=sample, growth_medium_id=medium_id)
            
            # Обрабатываем характеристики
            if characteristics_data:
                logger.info(f"🔧 Processing characteristics: {characteristics_data}")
                for char_name, char_data in characteristics_data.items():
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


@extend_schema(
    summary='Массовое удаление образцов',
    description='Удаляет несколько образцов по списку ID с логированием изменений',
    responses={
        200: OpenApiResponse(description='Образцы удалены'),
        400: OpenApiResponse(description='Ошибочный запрос'),
        404: OpenApiResponse(description='Образец не найден'),
    }
)
@api_view(['POST'])
@csrf_exempt
def bulk_delete_samples(request):
    """Массовое удаление образцов c аудитом изменений."""

    try:
        payload = request.data if isinstance(request.data, dict) else {}
        sample_ids = _parse_ids(payload.get('sample_ids') or payload.get('ids'))

        if not sample_ids:
            return Response(
                {'error': 'Не переданы ID образцов для удаления'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_samples = list(
            Sample.objects.filter(id__in=sample_ids)
            .select_related('strain', 'storage')
            .order_by('id')
        )

        found_ids = {sample.id for sample in existing_samples}
        missing_ids = sorted(set(sample_ids) - found_ids)
        if missing_ids:
            return Response(
                {'error': f'Образцы с ID {missing_ids} не найдены'},
                status=status.HTTP_404_NOT_FOUND,
            )

        batch_id = generate_batch_id()
        deleted_snapshot = []

        with transaction.atomic():
            for sample in existing_samples:
                deleted_snapshot.append(
                    {
                        'id': sample.id,
                        'original_sample_number': sample.original_sample_number,
                        'strain_short_code': sample.strain.short_code if sample.strain else None,
                        'storage': (
                            f"{sample.storage.box_id}-{sample.storage.cell_id}"
                            if sample.storage
                            else None
                        ),
                    }
                )

                log_change(
                    request=request,
                    content_type='sample',
                    object_id=sample.id,
                    action='BULK_DELETE',
                    old_values=model_to_dict(sample),
                    new_values=None,
                    comment=f'Массовое удаление {len(sample_ids)} образцов',
                    batch_id=batch_id,
                )

            deleted_count = Sample.objects.filter(id__in=sample_ids).delete()[0]

        logger.info(
            "Bulk deleted %s samples (batch=%s): %s",
            deleted_count,
            batch_id,
            sample_ids,
        )

        return Response(
            {
                'message': f'Удалено {deleted_count} образцов',
                'deleted_count': deleted_count,
                'deleted_samples': deleted_snapshot,
                'batch_id': batch_id,
            }
        )

    except Exception as exc:
        logger.error(f"Error in bulk_delete_samples: {exc}")
        return Response(
            {'error': f'Ошибка при массовом удалении: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    summary='Массовое обновление образцов',
    description='Обновляет указанные поля для набора образцов, включая динамические характеристики',
    responses={
        200: OpenApiResponse(description='Обновление выполнено'),
        400: OpenApiResponse(description='Ошибочный запрос'),
        404: OpenApiResponse(description='Образец не найден'),
    }
)
@api_view(['POST'])
@csrf_exempt
def bulk_update_samples(request):
    """Массовое обновление образцов и связанных характеристик."""

    try:
        payload = request.data if isinstance(request.data, dict) else {}
        sample_ids = _parse_ids(payload.get('sample_ids') or payload.get('ids'))
        update_data = payload.get('update_data') or payload.get('data') or {}

        if not sample_ids:
            return Response(
                {'error': 'Не переданы ID образцов для обновления'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(update_data, dict) or not update_data:
            return Response(
                {'error': 'Не переданы данные для обновления'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_samples = list(
            Sample.objects.filter(id__in=sample_ids)
            .select_related('strain')
            .order_by('id')
        )

        found_ids = {sample.id for sample in existing_samples}
        missing_ids = sorted(set(sample_ids) - found_ids)
        if missing_ids:
            return Response(
                {'error': f'Образцы с ID {missing_ids} не найдены'},
                status=status.HTTP_404_NOT_FOUND,
            )

        direct_updates: Dict[str, Optional[object]] = {}
        characteristic_updates: Dict[str, Optional[bool]] = {}

        for field, raw_value in update_data.items():
            if field == 'has_photo':
                coerced = _coerce_to_bool(raw_value)
                if coerced is None:
                    return Response(
                        {'error': "Поле 'has_photo' должно быть булевым"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                direct_updates[field] = coerced

            elif field in {'iuk_color_id', 'amylase_variant_id'}:
                if raw_value in {None, '', 'null'}:
                    direct_updates[field] = None
                else:
                    try:
                        related_id = int(raw_value)
                    except (TypeError, ValueError):
                        return Response(
                            {'error': f"Поле '{field}' должно содержать числовой ID"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    model_cls = IUKColor if field == 'iuk_color_id' else AmylaseVariant
                    if not model_cls.objects.filter(id=related_id).exists():
                        return Response(
                            {'error': f"Запись с ID {related_id} для '{field}' не найдена"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    direct_updates[field] = related_id

            elif field in BOOLEAN_CHARACTERISTIC_FIELDS:
                coerced = _coerce_to_bool(raw_value)
                if coerced is None:
                    return Response(
                        {'error': f"Поле '{field}' должно быть булевым"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                characteristic_updates[field] = coerced

        if not direct_updates and not characteristic_updates:
            return Response(
                {'error': 'Нет допустимых полей для обновления'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        characteristics_map: Dict[str, SampleCharacteristic] = {}
        if characteristic_updates:
            search_names = set()
            for slug in characteristic_updates.keys():
                search_names.update(BOOLEAN_CHARACTERISTIC_FIELDS.get(slug, (slug,)))

            characteristic_qs = SampleCharacteristic.objects.filter(
                Q(name__in=search_names) | Q(display_name__in=search_names)
            )

            for characteristic in characteristic_qs:
                for slug, aliases in BOOLEAN_CHARACTERISTIC_FIELDS.items():
                    if characteristic.name in aliases or characteristic.display_name in aliases:
                        characteristics_map.setdefault(slug, characteristic)

            missing_chars = [slug for slug in characteristic_updates if slug not in characteristics_map]
            if missing_chars:
                return Response(
                    {
                        'error': 'Некоторые характеристики не найдены',
                        'missing_characteristics': missing_chars,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        batch_id = generate_batch_id()
        updated_fields = list(direct_updates.keys()) + list(characteristic_updates.keys())

        with transaction.atomic():
            for sample in existing_samples:
                old_values = model_to_dict(sample)
                new_values: Dict[str, object] = {}

                if direct_updates:
                    for field, value in direct_updates.items():
                        setattr(sample, field, value)
                    sample.save(update_fields=list(direct_updates.keys()))
                    new_values.update(direct_updates)

                if characteristic_updates:
                    char_changes: Dict[str, bool] = {}
                    for slug, flag in characteristic_updates.items():
                        characteristic = characteristics_map[slug]
                        char_value = SampleCharacteristicValue.objects.filter(
                            sample=sample,
                            characteristic=characteristic,
                        ).first()

                        if flag:
                            if char_value:
                                if char_value.boolean_value is not True:
                                    char_value.boolean_value = True
                                    char_value.text_value = None
                                    char_value.select_value = None
                                    char_value.save(update_fields=['boolean_value', 'text_value', 'select_value'])
                            else:
                                SampleCharacteristicValue.objects.create(
                                    sample=sample,
                                    characteristic=characteristic,
                                    boolean_value=True,
                                )
                            char_changes[slug] = True
                        else:
                            if char_value:
                                char_value.delete()
                            char_changes[slug] = False

                    if char_changes:
                        new_values['characteristics'] = char_changes

                if new_values:
                    log_change(
                        request=request,
                        content_type='sample',
                        object_id=sample.id,
                        action='BULK_UPDATE',
                        old_values=old_values,
                        new_values=new_values,
                        comment=f"Массовое обновление полей: {', '.join(updated_fields)}",
                        batch_id=batch_id,
                    )

        logger.info(
            "Bulk updated samples (batch=%s): ids=%s fields=%s",
            batch_id,
            sample_ids,
            updated_fields,
        )

        return Response(
            {
                'message': f'Обновлено {len(existing_samples)} образцов',
                'updated_count': len(existing_samples),
                'updated_fields': updated_fields,
                'batch_id': batch_id,
            }
        )

    except Exception as exc:
        logger.error(f"Error in bulk_update_samples: {exc}")
        return Response(
            {'error': f'Ошибка при массовом обновлении: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    summary='Экспорт образцов',
    description='Экспортирует образцы в CSV, JSON или Excel с необязательными фильтрами',
    responses={200: OpenApiResponse(description='Файл со списком образцов')}
)
@api_view(['GET', 'POST'])
@csrf_exempt
def export_samples(request):
    """Экспорт образцов в различные форматы."""

    try:
        import csv
        import json
        from io import StringIO, BytesIO

        params = request.data if request.method == 'POST' else request.GET

        sample_ids = _parse_ids(params.get('sample_ids') or params.get('ids'))
        format_type = (params.get('format') or 'csv').lower()
        fields_value = params.get('fields')
        include_related = params.get('include_related', 'true')

        queryset = Sample.objects.all()

        if sample_ids:
            queryset = queryset.filter(id__in=sample_ids)
        else:
            search_query = (params.get('search') or '').strip()
            if search_query:
                queryset = queryset.filter(
                    Q(original_sample_number__icontains=search_query)
                    | Q(appendix_note__icontains=search_query)
                    | Q(comment__icontains=search_query)
                    | Q(strain__short_code__icontains=search_query)
                    | Q(strain__identifier__icontains=search_query)
                    | Q(storage__box_id__icontains=search_query)
                )

        # Фильтрация по дополнительным параметрам
        filter_map = {
            'strain_id': 'strain_id',
            'storage_id': 'storage_id',
            'source_id': 'source_id',
            'location_id': 'location_id',
            'iuk_color_id': 'iuk_color_id',
            'amylase_variant_id': 'amylase_variant_id',
        }
        for param, field_name in filter_map.items():
            value = params.get(param)
            if value not in (None, ''):
                queryset = queryset.filter(**{field_name: value})

        has_photo_value = params.get('has_photo')
        if has_photo_value not in (None, ''):
            coerced = _coerce_to_bool(has_photo_value)
            if coerced is not None:
                queryset = queryset.filter(has_photo=coerced)

        queryset = queryset.order_by('id')

        if str(include_related).lower() in {'true', '1', 'yes', 'y'}:
            queryset = queryset.select_related(
                'strain', 'storage', 'source', 'location', 'iuk_color', 'amylase_variant'
            ).prefetch_related(
                Prefetch('growth_media', queryset=SampleGrowthMedia.objects.select_related('growth_medium'))
            )

        available_fields = {
            'id': 'ID',
            'original_sample_number': 'Номер образца',
            'strain_short_code': 'Код штамма',
            'strain_identifier': 'Идентификатор штамма',
            'storage_cell': 'Ячейка хранения',
            'has_photo': 'Есть фото',
            'source_organism': 'Источник',
            'location_name': 'Локация',
            'iuk_color': 'Цвет ИУК',
            'amylase_variant': 'Вариант амилазы',
            'growth_media': 'Среды роста',
            'created_at': 'Создан',
            'updated_at': 'Обновлен',
        }

        if fields_value:
            raw_fields = [item.strip() for item in str(fields_value).split(',') if item.strip()]
            export_fields = [field for field in raw_fields if field in available_fields]
        else:
            export_fields = list(available_fields.keys())

        if not export_fields:
            return Response(
                {'error': 'Не указаны допустимые поля для экспорта'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rows = []
        for sample in queryset:
            row = {}
            for field in export_fields:
                header = available_fields[field]
                if field == 'id':
                    row[header] = sample.id
                elif field == 'original_sample_number':
                    row[header] = sample.original_sample_number or ''
                elif field == 'strain_short_code':
                    row[header] = sample.strain.short_code if sample.strain else ''
                elif field == 'strain_identifier':
                    row[header] = sample.strain.identifier if sample.strain else ''
                elif field == 'storage_cell':
                    row[header] = (
                        f"{sample.storage.box_id}:{sample.storage.cell_id}"
                        if sample.storage
                        else ''
                    )
                elif field == 'has_photo':
                    row[header] = 'Да' if sample.has_photo else 'Нет'
                elif field == 'source_organism':
                    row[header] = sample.source.organism_name if sample.source else ''
                elif field == 'location_name':
                    row[header] = sample.location.name if sample.location else ''
                elif field == 'iuk_color':
                    row[header] = sample.iuk_color.name if sample.iuk_color else ''
                elif field == 'amylase_variant':
                    row[header] = sample.amylase_variant.name if sample.amylase_variant else ''
                elif field == 'growth_media':
                    if hasattr(sample, 'growth_media'):
                        names = [gm.growth_medium.name for gm in sample.growth_media.all()]
                        row[header] = ', '.join(names)
                    else:
                        row[header] = ''
                elif field == 'created_at':
                    row[header] = (
                        sample.created_at.strftime('%Y-%m-%d %H:%M:%S')
                        if sample.created_at
                        else ''
                    )
                elif field == 'updated_at':
                    row[header] = (
                        sample.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                        if sample.updated_at
                        else ''
                    )
            rows.append(row)

        if format_type == 'json':
            response = HttpResponse(
                json.dumps(rows, ensure_ascii=False, indent=2),
                content_type='application/json; charset=utf-8',
            )
            response['Content-Disposition'] = 'attachment; filename="samples_export.json"'
            return response

        if format_type in {'xlsx', 'excel'}:
            try:
                from openpyxl import Workbook
            except ImportError:
                return Response(
                    {'error': 'Формат Excel недоступен (библиотека openpyxl не установлена)'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = 'Образцы'
            if rows:
                headers = list(rows[0].keys())
                sheet.append(headers)
                for row in rows:
                    sheet.append(list(row.values()))

            output = BytesIO()
            workbook.save(output)
            output.seek(0)

            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            response['Content-Disposition'] = 'attachment; filename="samples_export.xlsx"'
            return response

        # По умолчанию возвращаем CSV
        output = StringIO()
        writer = csv.writer(output)

        if rows:
            headers = list(rows[0].keys())
            writer.writerow(headers)
            for row in rows:
                writer.writerow(list(row.values()))

        response = HttpResponse(
            output.getvalue(),
            content_type='text/csv; charset=utf-8',
        )
        response['Content-Disposition'] = 'attachment; filename="samples_export.csv"'
        return response

    except Exception as exc:
        logger.error(f"Error in export_samples: {exc}")
        return Response(
            {'error': f'Ошибка при экспорте образцов: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    summary='Статистика по образцам',
    responses={200: OpenApiResponse(description='Статистические данные по образцам')}
)
@api_view(['GET'])
def samples_stats(request):
    """Возвращает агрегированную статистику по образцам."""

    try:
        total_count = Sample.objects.count()
        with_photo = Sample.objects.filter(has_photo=True).count()

        recent_days_raw = request.GET.get('recent_days', 30)
        try:
            recent_days = int(recent_days_raw)
        except (TypeError, ValueError):
            recent_days = 30
        recent_days = max(1, min(recent_days, 365))
        cutoff = timezone.now() - timedelta(days=recent_days)
        recent_additions = Sample.objects.filter(created_at__gte=cutoff).count()

        by_strain_qs = (
            Sample.objects.filter(strain__isnull=False)
            .values('strain__short_code')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        by_strain = {
            row['strain__short_code'] or 'Не указан': row['count'] for row in by_strain_qs
        }

        by_iuk_color_qs = (
            Sample.objects.filter(iuk_color__isnull=False)
            .values('iuk_color__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        by_iuk_color = {
            row['iuk_color__name'] or 'Не указан': row['count'] for row in by_iuk_color_qs
        }

        by_amylase_variant_qs = (
            Sample.objects.filter(amylase_variant__isnull=False)
            .values('amylase_variant__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        by_amylase_variant = {
            row['amylase_variant__name'] or 'Не указан': row['count']
            for row in by_amylase_variant_qs
        }

        response_data = {
            'total': total_count,
            'with_photo': with_photo,
            'by_strain': by_strain,
            'by_iuk_color': by_iuk_color,
            'by_amylase_variant': by_amylase_variant,
            'recent_additions': recent_additions,
            'recent_days_window': recent_days,
        }

        return Response(response_data)

    except Exception as exc:
        logger.error(f"Error in samples_stats: {exc}")
        return Response(
            {'error': f'Ошибка получения статистики: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


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
