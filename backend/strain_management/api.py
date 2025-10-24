"""
API endpoints для управления штаммами
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction, connection, IntegrityError
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional, Dict, Tuple
import logging
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from datetime import datetime, time
from django.utils.dateparse import parse_datetime, parse_date
from django.http import HttpResponse

from .models import Strain
from sample_management.models import Sample, SampleCharacteristic, SampleCharacteristicValue
from collection_manager.utils import log_change, model_to_dict, generate_batch_id

logger = logging.getLogger(__name__)


def reset_sequence(model):
    """Сбросить последовательность primary key, чтобы она соответствовала MAX(id)+1.

    Полезно, если база данных была импортирована вручную и последовательности
    не синхронизированы, что приводит к ошибке duplicate key value на вставке.
    """
    table_name = model._meta.db_table
    pk_column = model._meta.pk.column

    sql = (
        "SELECT setval(pg_get_serial_sequence(%s, %s), "
        "COALESCE((SELECT MAX(" + pk_column + ") FROM " + table_name + "), 1) + 1, false)"
    )

    with connection.cursor() as cursor:
        cursor.execute(sql, [table_name, pk_column])


class StrainSchema(BaseModel):
    """Схема валидации для штаммов"""

    id: Optional[int] = Field(None, ge=1, description="ID штамма")
    short_code: str = Field(
        min_length=1, max_length=50, description="Короткий код штамма"
    )
    rrna_taxonomy: Optional[str] = Field(
        None, max_length=500, description="rRNA таксономия"
    )
    identifier: str = Field(
        min_length=1, max_length=100, description="Идентификатор штамма"
    )
    name_alt: Optional[str] = Field(
        None, max_length=200, description="Альтернативное название"
    )
    rcam_collection_id: Optional[str] = Field(
        None, max_length=50, description="ID коллекции RCAM"
    )
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")

    @field_validator("short_code", "identifier")
    @classmethod
    def validate_required_fields(cls, v: str) -> str:
        return v.strip()

    @field_validator("rrna_taxonomy", "name_alt", "rcam_collection_id")
    @classmethod
    def validate_optional_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    class Config:
        from_attributes = True


class CreateStrainSchema(BaseModel):
    """Схема для создания штамма без ID"""
    
    short_code: str = Field(min_length=1, max_length=50, description="Короткий код штамма")
    rrna_taxonomy: Optional[str] = Field(None, max_length=500, description="rRNA таксономия")
    identifier: str = Field(min_length=1, max_length=100, description="Идентификатор штамма")
    name_alt: Optional[str] = Field(None, max_length=200, description="Альтернативное название")
    rcam_collection_id: Optional[str] = Field(None, max_length=50, description="ID коллекции RCAM")
    
    @field_validator('short_code', 'identifier')
    @classmethod
    def validate_required_fields(cls, v: str) -> str:
        return v.strip()
    
    @field_validator('rrna_taxonomy', 'name_alt', 'rcam_collection_id')
    @classmethod
    def validate_optional_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


FILTER_FIELD_TYPES: Dict[str, str] = {
    'id': 'int',
    'short_code': 'string',
    'identifier': 'string',
    'rrna_taxonomy': 'string',
    'name_alt': 'string',
    'rcam_collection_id': 'string',
    'created_at': 'datetime',
}

FILTER_ALIASES: Dict[str, str] = {
    'rcam_id': 'rcam_collection_id',
    'taxonomy': 'rrna_taxonomy',
}

SPECIAL_FILTERS: Dict[str, Tuple[str, str]] = {
    'created_after': ('created_at', 'gte'),
    'created_before': ('created_at', 'lte'),
}

RESERVED_QUERY_PARAMS = {'page', 'limit', 'search'}

BOOLEAN_CHARACTERISTIC_NAMES = (
    'is_identified',
    'has_genome',
    'has_biochemistry',
)


def _resolve_lookup(field: str, operator: Optional[str]) -> Optional[str]:
    """Сопоставить оператор фильтрации с Django lookup."""

    field_type = FILTER_FIELD_TYPES.get(field)
    if field_type is None:
        return None

    if operator is None:
        return 'icontains' if field_type == 'string' else 'exact'

    normalized = operator.lower()
    mapping = {
        'contains': 'icontains',
        'ilike': 'icontains',
        'startswith': 'istartswith',
        'endswith': 'iendswith',
        'equals': 'exact',
        'exact': 'exact',
        'gt': 'gt',
        'lt': 'lt',
        'gte': 'gte',
        'lte': 'lte',
    }

    lookup = mapping.get(normalized)
    if lookup is None:
        return None

    if lookup == 'exact' and field_type == 'string':
        return 'iexact'

    return lookup


def _coerce_filter_value(field: str, value: str, lookup: str):
    """Преобразовать значение параметра к типу поля для фильтрации."""

    field_type = FILTER_FIELD_TYPES.get(field)
    if field_type == 'int':
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    if field_type == 'datetime':
        dt = parse_datetime(value)
        if dt is not None:
            return dt

        date_value = parse_date(value)
        if date_value is None:
            return None

        if lookup in {'lt', 'lte'}:
            return datetime.combine(date_value, time.max)
        return datetime.combine(date_value, time.min)

    # Строковые значения приводим и удаляем лишние пробелы
    normalized = value.strip()
    return normalized if normalized else None


def _collect_strain_filters(params, reserved_keys=None):
    """Разобрать параметры запроса и подготовить фильтры ORM."""

    reserved = set(reserved_keys or [])
    filters = {}
    applied = []

    for param, raw_value in params.items():
        if param in reserved:
            continue

        if raw_value is None or raw_value == '':
            continue

        value = str(raw_value).strip()
        if not value:
            continue

        field = param
        operator = None

        if field in SPECIAL_FILTERS:
            field, operator = SPECIAL_FILTERS[field]
        elif '__' in field:
            field, operator = field.split('__', 1)

        field = FILTER_ALIASES.get(field, field)

        lookup = _resolve_lookup(field, operator)
        if lookup is None:
            continue

        coerced = _coerce_filter_value(field, value, lookup)
        if coerced is None:
            continue

        filters[f"{field}__{lookup}"] = coerced
        applied.append(param)

    return filters, applied


def _collect_samples_stats(strain_id: int) -> Dict[str, float]:
    """Подсчитать расширенную статистику по образцам штамма."""

    samples_qs = Sample.objects.filter(strain_id=strain_id)
    total_count = samples_qs.count()

    if total_count == 0:
        return {
            'total_count': 0,
            'with_photo_count': 0,
            'identified_count': 0,
            'with_genome_count': 0,
            'with_biochemistry_count': 0,
            'photo_percentage': 0.0,
            'identified_percentage': 0.0,
        }

    with_photo_count = samples_qs.filter(has_photo=True).count()

    characteristic_types = dict(
        SampleCharacteristic.objects.filter(name__in=BOOLEAN_CHARACTERISTIC_NAMES)
        .values_list('name', 'characteristic_type')
    )

    characteristic_counts = {
        'is_identified': 0,
        'has_genome': 0,
        'has_biochemistry': 0,
    }

    for char_name, char_type in characteristic_types.items():
        values_qs = SampleCharacteristicValue.objects.filter(
            sample__strain_id=strain_id,
            characteristic__name=char_name,
        )

        if char_type == 'boolean':
            values_qs = values_qs.filter(boolean_value=True)
        elif char_type == 'select':
            values_qs = values_qs.exclude(select_value__isnull=True).exclude(select_value='')
        else:
            values_qs = values_qs.exclude(text_value__isnull=True).exclude(text_value='')

        characteristic_counts[char_name] = values_qs.count()

    identified_count = characteristic_counts['is_identified']

    return {
        'total_count': total_count,
        'with_photo_count': with_photo_count,
        'identified_count': identified_count,
        'with_genome_count': characteristic_counts['has_genome'],
        'with_biochemistry_count': characteristic_counts['has_biochemistry'],
        'photo_percentage': round((with_photo_count / total_count) * 100, 1) if total_count else 0.0,
        'identified_percentage': round((identified_count / total_count) * 100, 1) if total_count else 0.0,
    }


def _normalize_id_list(raw_ids) -> list[int]:
    """Преобразовать входной параметр ID в уникальный список целых чисел."""

    if raw_ids is None:
        return []

    if isinstance(raw_ids, (list, tuple)):
        candidates = raw_ids
    else:
        candidates = str(raw_ids).replace(',', ' ').split()

    normalized: list[int] = []
    seen = set()

    for item in candidates:
        try:
            value = int(item)
        except (TypeError, ValueError):
            continue
        if value > 0 and value not in seen:
            normalized.append(value)
            seen.add(value)

    return normalized


def _to_bool(value) -> bool:
    """Привести значение к bool с учетом строковых входов."""

    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {'true', '1', 'yes', 'y', 'on'}
    return False

@extend_schema(
    operation_id="strains_list",
    summary="Список штаммов",
    description="Получение списка всех штаммов с поиском и фильтрацией",
    parameters=[
        OpenApiParameter(name='search', type=str, description='Поисковый запрос'),
        OpenApiParameter(name='page', type=int, description='Номер страницы'),
        OpenApiParameter(name='limit', type=int, description='Количество элементов на странице'),
    ],
    responses={
        200: OpenApiResponse(description="Список штаммов"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(["GET"])
def list_strains(request: Request) -> Response:
    """Список всех штаммов с поиском, пагинацией и расширенными фильтрами."""

    try:
        try:
            page = int(request.GET.get('page', 1))
        except (TypeError, ValueError):
            page = 1

        try:
            limit = int(request.GET.get('limit', 50))
        except (TypeError, ValueError):
            limit = 50

        page = max(1, page)
        limit = max(1, min(limit, 1000))

        search_query = request.GET.get('search', '')
        search_query = search_query.strip() if search_query else ''

        queryset = Strain.objects.all()

        if search_query:
            queryset = queryset.filter(
                Q(short_code__icontains=search_query)
                | Q(identifier__icontains=search_query)
                | Q(rrna_taxonomy__icontains=search_query)
                | Q(name_alt__icontains=search_query)
                | Q(rcam_collection_id__icontains=search_query)
            )

        filters, applied_filters = _collect_strain_filters(request.GET, RESERVED_QUERY_PARAMS)
        if filters:
            queryset = queryset.filter(**filters)

        total_count = queryset.count()
        total_pages = max(1, (total_count + limit - 1) // limit) if limit else 1
        page = min(page, total_pages)
        offset = (page - 1) * limit

        strains = queryset.order_by('id')[offset:offset + limit]
        data = [StrainSchema.model_validate(strain).model_dump(mode='json') for strain in strains]

        has_next = page < total_pages
        has_previous = page > 1

        return Response({
            'total': total_count,
            'strains': data,
            'pagination': {
                'total': total_count,
                'shown': len(data),
                'page': page,
                'limit': limit,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_previous': has_previous,
                'offset': offset,
            },
            'search_query': search_query,
            'filters_applied': {
                'search': bool(search_query),
                'advanced_filters': applied_filters,
                'total_filters': len(applied_filters),
            },
        })

    except Exception as exc:
        logger.error("Error in list_strains: %s", exc)
        return Response(
            {'error': f'Ошибка получения списка штаммов: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    operation_id="strain_detail",
    summary="Получение штамма",
    description="Получение штамма по ID",
    responses={
        200: OpenApiResponse(description="Данные штамма"),
        404: OpenApiResponse(description="Штамм не найден"),
        500: OpenApiResponse(description="Ошибка сервера"),
    }
)
@api_view(['GET'])
def get_strain(request, strain_id):
    """Получение штамма по ID"""
    try:
        strain = Strain.objects.get(id=strain_id)
        data = StrainSchema.model_validate(strain).model_dump(mode='json')
        data['samples_stats'] = _collect_samples_stats(strain.id)
        return Response(data)
    except Strain.DoesNotExist:
        return Response(
            {'error': f'Штамм с ID {strain_id} не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error("Error in get_strain: %s", e)
        return Response(
            {'error': f'Ошибка получения штамма: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@csrf_exempt
def create_strain(request):
    """Создание нового штамма"""
    try:
        validated_data = CreateStrainSchema.model_validate(request.data)
        
        # Проверяем уникальность short_code
        if Strain.objects.filter(short_code=validated_data.short_code).exists():
            return Response({
                'error': f'Штамм с кодом "{validated_data.short_code}" уже существует'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создаем штамм
        try:
            with transaction.atomic():
                strain = Strain.objects.create(
                    short_code=validated_data.short_code,
                    rrna_taxonomy=validated_data.rrna_taxonomy,
                    identifier=validated_data.identifier,
                    name_alt=validated_data.name_alt,
                    rcam_collection_id=validated_data.rcam_collection_id
                )
                logger.info(f"Created strain: {strain.short_code} (ID: {strain.id})")
        except IntegrityError as e:
            if "duplicate key value violates unique constraint" in str(e):
                logger.warning(
                    "IntegrityError on Strain create — attempting to reset sequence and retry"
                )
                reset_sequence(Strain)
                with transaction.atomic():
                    strain = Strain.objects.create(
                        short_code=validated_data.short_code,
                        rrna_taxonomy=validated_data.rrna_taxonomy,
                        identifier=validated_data.identifier,
                        name_alt=validated_data.name_alt,
                        rcam_collection_id=validated_data.rcam_collection_id,
                    )
                    logger.info(
                        f"Created new strain after sequence reset: {strain.short_code} (ID: {strain.id})"
                    )
            else:
                raise
        
        return Response({
            'id': strain.id,
            'short_code': strain.short_code,
            'identifier': strain.identifier,
            'rrna_taxonomy': strain.rrna_taxonomy,
            'name_alt': strain.name_alt,
            'rcam_collection_id': strain.rcam_collection_id,
            'message': 'Штамм успешно создан'
        }, status=status.HTTP_201_CREATED)
    
    except ValidationError as e:
        return Response({
            'error': 'Ошибки валидации данных',
            'details': e.errors()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Unexpected error in create_strain: {e}")
        return Response({
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@csrf_exempt
def update_strain(request, strain_id):
    """Обновление штамма"""
    try:
        # Получаем штамм
        try:
            strain = Strain.objects.get(id=strain_id)
        except Strain.DoesNotExist:
            return Response({
                'error': f'Штамм с ID {strain_id} не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Валидируем данные
        validated_data = CreateStrainSchema.model_validate(request.data)
        
        # Проверяем уникальность short_code (исключая текущий штамм)
        if Strain.objects.filter(short_code=validated_data.short_code).exclude(id=strain_id).exists():
            return Response({
                'error': f'Штамм с кодом "{validated_data.short_code}" уже существует'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Обновление штамма
        with transaction.atomic():
            strain.short_code = validated_data.short_code
            strain.rrna_taxonomy = validated_data.rrna_taxonomy
            strain.identifier = validated_data.identifier
            strain.name_alt = validated_data.name_alt
            strain.rcam_collection_id = validated_data.rcam_collection_id
            strain.save()
            
            logger.info(f"Updated strain: {strain.short_code} (ID: {strain.id})")
        
        return Response({
            'id': strain.id,
            'short_code': strain.short_code,
            'identifier': strain.identifier,
            'rrna_taxonomy': strain.rrna_taxonomy,
            'name_alt': strain.name_alt,
            'rcam_collection_id': strain.rcam_collection_id,
            'message': 'Штамм успешно обновлен'
        })
    
    except ValidationError as e:
        return Response({
            'error': 'Ошибки валидации данных',
            'details': e.errors()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Unexpected error in update_strain: {e}")
        return Response({
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@csrf_exempt
def delete_strain(request, strain_id):
    """Удаление штамма"""
    try:
        # Получаем штамм
        try:
            strain = Strain.objects.get(id=strain_id)
        except Strain.DoesNotExist:
            return Response({
                'error': f'Штамм с ID {strain_id} не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем, есть ли связанные образцы
        from sample_management.models import Sample
        related_samples = Sample.objects.filter(strain_id=strain_id).count()
        if related_samples > 0:
            return Response({
                'error': f'Нельзя удалить штамм, так как с ним связано {related_samples} образцов',
                'related_samples_count': related_samples
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Сохраняем информацию о штамме для ответа
        strain_info = {
            'id': strain.id,
            'short_code': strain.short_code,
            'identifier': strain.identifier
        }
        
        # Удаляем штамм
        with transaction.atomic():
            strain.delete()
            logger.info(f"Deleted strain: {strain_info['short_code']} (ID: {strain_info['id']})")
        
        return Response({
            'message': f"Штамм '{strain_info['short_code']}' успешно удален",
            'deleted_strain': strain_info
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Unexpected error in delete_strain: {e}")
        return Response({
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@csrf_exempt
def validate_strain(request):
    """Валидация данных штамма без сохранения"""
    try:
        validated_data = CreateStrainSchema.model_validate(request.data)
        return Response({
            'valid': True,
            'data': validated_data.model_dump(),
            'message': 'Данные штамма валидны'
        })
    except ValidationError as e:
        return Response({
            'valid': False,
            'errors': e.errors(),
            'message': 'Ошибки валидации данных'
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id="strains_bulk_delete",
    summary="Массовое удаление штаммов",
    description="Удаляет несколько штаммов. При наличии связанных образцов требуется force_delete=true.",
    responses={
        200: OpenApiResponse(description="Результат массового удаления"),
        400: OpenApiResponse(description="Ошибки валидации"),
        404: OpenApiResponse(description="Некоторые штаммы не найдены"),
    },
)
@api_view(['POST'])
@csrf_exempt
def bulk_delete_strains(request):
    """Массовое удаление штаммов с поддержкой принудительного удаления связанных образцов."""

    try:
        strain_ids = _normalize_id_list(request.data.get('strain_ids'))
        force_delete = _to_bool(request.data.get('force_delete', False))

        if not strain_ids:
            return Response(
                {'error': 'Не указаны ID штаммов для удаления'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        strains = list(Strain.objects.filter(id__in=strain_ids).order_by('id'))
        existing_ids = [strain.id for strain in strains]

        missing_ids = sorted(set(strain_ids) - set(existing_ids))
        if missing_ids:
            return Response(
                {'error': f'Штаммы с ID {missing_ids} не найдены'},
                status=status.HTTP_404_NOT_FOUND,
            )

        samples_counts = {
            row['strain_id']: row['count']
            for row in Sample.objects.filter(strain_id__in=existing_ids)
            .values('strain_id')
            .annotate(count=Count('id'))
        }

        if not force_delete:
            strains_with_samples = [
                {
                    'id': strain.id,
                    'short_code': strain.short_code,
                    'sample_count': samples_counts.get(strain.id, 0),
                }
                for strain in strains
                if samples_counts.get(strain.id)
            ]
            if strains_with_samples:
                return Response(
                    {
                        'error': 'Некоторые штаммы имеют связанные образцы',
                        'strains_with_samples': strains_with_samples,
                        'message': 'Укажите force_delete=true для удаления вместе с образцами',
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        strains_info = [
            {
                'id': strain.id,
                'short_code': strain.short_code,
                'identifier': strain.identifier,
            }
            for strain in strains
        ]

        with transaction.atomic():
            if force_delete and samples_counts:
                Sample.objects.filter(strain_id__in=existing_ids).delete()

            for strain in strains:
                log_change(
                    request=request,
                    content_type='strain',
                    object_id=strain.id,
                    action='BULK_DELETE',
                    old_values=model_to_dict(strain),
                    new_values=None,
                    comment='Массовое удаление штамма',
                )

            deleted_count = Strain.objects.filter(id__in=existing_ids).delete()[0]
            logger.info(
                "Bulk deleted %s strains (force_delete=%s)", deleted_count, force_delete
            )

        return Response(
            {
                'message': f'Успешно удалено {deleted_count} штаммов',
                'deleted_count': deleted_count,
                'deleted_strains': strains_info,
                'force_delete': force_delete,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as exc:
        logger.error("Error in bulk_delete_strains: %s", exc)
        return Response(
            {'error': f'Ошибка при массовом удалении штаммов: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    operation_id="strains_bulk_update",
    summary="Массовое обновление штаммов",
    description="Обновляет перечисленные штаммы указанными полями.",
    responses={
        200: OpenApiResponse(description="Результат массового обновления"),
        400: OpenApiResponse(description="Ошибки валидации"),
        404: OpenApiResponse(description="Некоторые штаммы не найдены"),
    },
)
@api_view(['POST'])
@csrf_exempt
def bulk_update_strains(request):
    """Массовое обновление базовых полей штаммов."""

    try:
        strain_ids = _normalize_id_list(request.data.get('strain_ids'))
        update_data = request.data.get('update_data', {}) or {}

        if not strain_ids:
            return Response(
                {'error': 'Не указаны ID штаммов для обновления'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(update_data, dict) or not update_data:
            return Response(
                {'error': 'Не указаны данные для обновления'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        strains = list(Strain.objects.filter(id__in=strain_ids).order_by('id'))
        existing_ids = [strain.id for strain in strains]
        missing_ids = sorted(set(strain_ids) - set(existing_ids))

        if missing_ids:
            return Response(
                {'error': f'Штаммы с ID {missing_ids} не найдены'},
                status=status.HTTP_404_NOT_FOUND,
            )

        allowed_fields = {
            'short_code',
            'rrna_taxonomy',
            'identifier',
            'name_alt',
            'rcam_collection_id',
        }

        filtered_update_data = {}
        validation_errors = {}

        for key, value in update_data.items():
            if key not in allowed_fields:
                continue

            if value is None:
                filtered_update_data[key] = None
                continue

            if isinstance(value, str):
                normalized = value.strip()
            else:
                normalized = str(value).strip()

            if key in {'short_code', 'identifier'} and not normalized:
                validation_errors[key] = 'Поле не может быть пустым'
                continue

            filtered_update_data[key] = normalized if normalized else None

        if validation_errors:
            return Response(
                {'error': 'Ошибки валидации данных', 'details': validation_errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not filtered_update_data:
            return Response(
                {'error': 'Нет допустимых полей для обновления'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if 'short_code' in filtered_update_data:
            short_code = filtered_update_data['short_code']
            if short_code and Strain.objects.filter(short_code=short_code).exclude(id__in=existing_ids).exists():
                return Response(
                    {
                        'error': f'Штамм с кодом "{short_code}" уже существует',
                        'field': 'short_code',
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        batch_id = generate_batch_id()
        comment = f"Массовое обновление {len(existing_ids)} штаммов: {list(filtered_update_data.keys())}"

        update_queryset = Strain.objects.filter(id__in=existing_ids)

        with transaction.atomic():
            for strain in strains:
                old_values = model_to_dict(strain)
                for field, value in filtered_update_data.items():
                    setattr(strain, field, value)
                new_values = model_to_dict(strain)

                log_change(
                    request=request,
                    content_type='strain',
                    object_id=strain.id,
                    action='BULK_UPDATE',
                    old_values=old_values,
                    new_values=new_values,
                    comment=comment,
                    batch_id=batch_id,
                )

            updated_count = update_queryset.update(**filtered_update_data)
            logger.info(
                "Bulk updated %s strains with data %s (batch=%s)",
                updated_count,
                filtered_update_data,
                batch_id,
            )

        return Response(
            {
                'message': f'Успешно обновлено {updated_count} штаммов',
                'updated_count': updated_count,
                'updated_fields': list(filtered_update_data.keys()),
                'updated_data': filtered_update_data,
                'batch_id': batch_id,
            }
        )

    except Exception as exc:
        logger.error("Error in bulk_update_strains: %s", exc)
        return Response(
            {'error': f'Ошибка при массовом обновлении штаммов: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    operation_id="strains_bulk_export",
    summary="Экспорт штаммов",
    description="Экспорт штаммов в формате CSV, JSON или Excel с учетом фильтров.",
    responses={
        200: OpenApiResponse(description="Файл с данными"),
        400: OpenApiResponse(description="Ошибки параметров"),
    },
)
@api_view(['GET', 'POST'])
@csrf_exempt
def bulk_export_strains(request):
    """Экспорт штаммов с поддержкой фильтров и выбора полей."""

    try:
        import csv
        import json
        from io import StringIO, BytesIO

        params = request.data if request.method == 'POST' else request.GET

        strain_ids = _normalize_id_list(params.get('strain_ids'))

        raw_fields = params.get('fields')
        if isinstance(raw_fields, (list, tuple)):
            fields = [str(value) for value in raw_fields if value]
        else:
            fields = str(raw_fields).split(',') if raw_fields else []

        format_type = str(params.get('format', 'csv')).lower()
        include_related = _to_bool(params.get('include_related', True))
        _ = include_related  # совместимость с существующим API

        queryset = Strain.objects.all()

        if strain_ids:
            queryset = queryset.filter(id__in=strain_ids)
        else:
            search_query = params.get('search', '')
            search_query = search_query.strip() if isinstance(search_query, str) else ''

            if search_query:
                queryset = queryset.filter(
                    Q(short_code__icontains=search_query)
                    | Q(identifier__icontains=search_query)
                    | Q(rrna_taxonomy__icontains=search_query)
                    | Q(name_alt__icontains=search_query)
                    | Q(rcam_collection_id__icontains=search_query)
                )

            reserved = RESERVED_QUERY_PARAMS.union({'format', 'fields', 'include_related', 'strain_ids'})
            filters, _ = _collect_strain_filters(params, reserved_keys=reserved)
            if filters:
                queryset = queryset.filter(**filters)

        queryset = queryset.order_by('id')

        available_fields = {
            'id': 'ID',
            'short_code': 'Короткий код',
            'identifier': 'Идентификатор',
            'rrna_taxonomy': 'rRNA таксономия',
            'name_alt': 'Альтернативное название',
            'rcam_collection_id': 'RCAM ID',
            'created_at': 'Дата создания',
            'updated_at': 'Дата обновления',
        }

        if not fields or not any(field.strip() for field in fields):
            export_fields = list(available_fields.keys())
        else:
            export_fields = [field.strip() for field in fields if field and field.strip() in available_fields]

        if not export_fields:
            return Response(
                {'error': 'Не указаны корректные поля для экспорта'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data_rows = []
        for strain in queryset:
            row = {}
            for field in export_fields:
                label = available_fields[field]
                value = getattr(strain, field, None)
                if value is None:
                    row[label] = ''
                    continue

                if isinstance(value, datetime):
                    row[label] = value.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    row[label] = value
            data_rows.append(row)

        if format_type == 'json':
            response = HttpResponse(
                json.dumps(data_rows, ensure_ascii=False, indent=2),
                content_type='application/json; charset=utf-8',
            )
            response['Content-Disposition'] = 'attachment; filename="strains_export.json"'
            return response

        if format_type == 'excel':
            try:
                from openpyxl import Workbook

                workbook = Workbook()
                worksheet = workbook.active
                worksheet.title = 'Штаммы'

                if data_rows:
                    headers = list(data_rows[0].keys())
                    worksheet.append(headers)
                    for row in data_rows:
                        worksheet.append(list(row.values()))

                output = BytesIO()
                workbook.save(output)
                output.seek(0)

                response = HttpResponse(
                    output.getvalue(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                )
                response['Content-Disposition'] = 'attachment; filename="strains_export.xlsx"'
                return response

            except ImportError:
                return Response(
                    {'error': 'Excel экспорт недоступен. Установите openpyxl.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # CSV по умолчанию
        output = StringIO()
        writer = csv.writer(output)

        if data_rows:
            headers = list(data_rows[0].keys())
            writer.writerow(headers)
            for row in data_rows:
                writer.writerow([row.get(header, '') for header in headers])

        response = HttpResponse(
            output.getvalue(),
            content_type='text/csv; charset=utf-8',
        )
        response['Content-Disposition'] = 'attachment; filename="strains_export.csv"'
        return response

    except Exception as exc:
        logger.error("Error in bulk_export_strains: %s", exc)
        return Response(
            {'error': f'Ошибка при экспорте штаммов: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
