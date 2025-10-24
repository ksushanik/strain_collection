"""
API endpoints с валидацией Pydantic для управления коллекцией штаммов
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction, IntegrityError
from django.db import models
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional
import logging
from django.db.models import Q
from django.db.models.functions import Lower, TruncMonth
from django.db import connection
import re
from django.core.exceptions import ValidationError as DjangoValidationError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.utils import timezone

from reference_data.models import (
    IndexLetter, Location, Source, Comment, AppendixNote,
    IUKColor, AmylaseVariant, GrowthMedium
)
from storage_management.models import Storage
from strain_management.models import Strain
from sample_management.models import Sample, SamplePhoto, SampleGrowthMedia, SampleCharacteristic, SampleCharacteristicValue
from .schemas import (
    IndexLetterSchema, LocationSchema, SourceSchema,
    CommentSchema, AppendixNoteSchema, StorageSchema,
    StrainSchema, SampleSchema, SampleCharacteristicSchema,
    SampleCharacteristicValueSchema, UpdateSampleSchema
)
from .utils import log_change, generate_batch_id, model_to_dict, reset_sequence

logger = logging.getLogger(__name__)




def _assign_growth_media(sample, growth_media_ids):
    """Связать образец с выбранными средами роста без дублирования логики."""
    if not growth_media_ids:
        return

    for media_id in growth_media_ids:
        try:
            media = GrowthMedium.objects.get(id=media_id)
            SampleGrowthMedia.objects.create(sample=sample, growth_medium=media)
        except GrowthMedium.DoesNotExist:
            logger.warning(f"Growth medium with ID {media_id} not found, skipping")


@api_view(['GET'])
def api_status(request):
    """API health summary with currently supported routes."""
    return Response({
        'status': 'OK',
        'validation': 'Pydantic 2.x',
        'endpoints': [
            # Strains Management
            '/api/strains/',
            '/api/strains/create/',
            '/api/strains/<id>/',
            '/api/strains/<id>/update/',
            '/api/strains/<id>/delete/',
            '/api/strains/validate/',
            '/api/strains/bulk-delete/',
            '/api/strains/bulk-update/',
            '/api/strains/export/',

            # Samples Management
            '/api/samples/',
            '/api/samples/create/',
            '/api/samples/<id>/',
            '/api/samples/<id>/update/',
            '/api/samples/<id>/delete/',
            '/api/samples/validate/',
            '/api/samples/bulk-delete/',
            '/api/samples/bulk-update/',
            '/api/samples/export/',

            # Storage Management
            '/api/storage/',
            '/api/storage/summary/',
            '/api/storage/boxes/',
            '/api/storage/boxes/create/',
            '/api/storage/boxes/<box_id>/',
            '/api/storage/boxes/<box_id>/detail/',
            '/api/storage/boxes/<box_id>/update/',
            '/api/storage/boxes/<box_id>/delete/',
            '/api/storage/boxes/<box_id>/cells/',
            '/api/storage/boxes/<box_id>/cells/<cell_id>/assign/',
            '/api/storage/boxes/<box_id>/cells/<cell_id>/clear/',
            '/api/storage/boxes/<box_id>/cells/bulk-assign/',

            # Audit & Logging
            '/api/audit/batch-log/',
            '/api/audit/batch/<batch_id>/',
            '/api/audit/user-activity/',

            # Analytics & Status
            '/api/analytics/',
            '/api/stats/',
            '/api/health/',
            '/api/schema/',
            '/docs/',
        ]
    })


@api_view(['GET'])
def api_health(request):
    """Простой health-check со сводной статистикой."""
    try:
        samples_total = Sample.objects.count()
        strains_total = Strain.objects.count()
        storage_total = Storage.objects.count()

        return Response({
            'status': 'ok',
            'timestamp': timezone.now().isoformat(),
            'services': {
                'database': 'ok',
            },
            'counts': {
                'samples': samples_total,
                'strains': strains_total,
                'storage_cells': storage_total,
            },
        })
    except Exception as exc:
        logger.exception("Health check failed: %s", exc)
        return Response(
            {
                'status': 'error',
                'message': str(exc),
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@api_view(['GET'])
@cache_page(300)
def analytics_data(request):
    """Агрегированная аналитика для фронтенда."""
    total_samples = Sample.objects.count()
    total_strains = Strain.objects.count()
    total_storage = Storage.objects.count()

    source_distribution_qs = (
        Sample.objects.exclude(source__isnull=True)
        .values('source__name')
        .annotate(count=models.Count('id'))
        .order_by('-count')
    )
    source_distribution = {
        row['source__name']: row['count']
        for row in source_distribution_qs
    }

    strain_distribution_qs = (
        Sample.objects.exclude(strain__short_code__isnull=True)
        .values('strain__short_code')
        .annotate(count=models.Count('id'))
        .order_by('-count')[:10]
    )
    strain_distribution = {
        row['strain__short_code']: row['count']
        for row in strain_distribution_qs
    }

    twelve_months_ago = timezone.now() - timezone.timedelta(days=365)
    monthly_trends_qs = (
        Sample.objects.filter(created_at__gte=twelve_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=models.Count('id'))
        .order_by('month')
    )
    monthly_trends = [
        {
            'month': item['month'].strftime('%Y-%m') if item['month'] else 'unknown',
            'count': item['count'],
        }
        for item in monthly_trends_qs
    ]

    characteristics_stats = {
        'has_photo': Sample.objects.filter(has_photo=True).count(),
    }
    for characteristic in SampleCharacteristic.objects.filter(is_active=True):
        values_qs = SampleCharacteristicValue.objects.filter(characteristic=characteristic)
        if characteristic.characteristic_type == 'boolean':
            count = values_qs.filter(boolean_value=True).count()
        else:
            count = values_qs.exclude(
                models.Q(text_value__isnull=True) | models.Q(text_value='') |
                models.Q(select_value__isnull=True) | models.Q(select_value='')
            ).count()
        characteristics_stats[characteristic.display_name] = count

    occupied_cells = Sample.objects.filter(storage__isnull=False).count()
    free_cells = max(total_storage - occupied_cells, 0)

    return Response({
        'totalSamples': total_samples,
        'totalStrains': total_strains,
        'totalStorage': total_storage,
        'sourceDistribution': source_distribution,
        'strainDistribution': strain_distribution,
        'monthlyTrends': monthly_trends,
        'characteristicsStats': characteristics_stats,
        'storageUtilization': {
            'occupied': occupied_cells,
            'free': free_cells,
            'total': total_storage,
        },
    })


@api_view(['GET'])
def list_strains(request):
    """Список всех штаммов с расширенным поиском и фильтрацией - ОПТИМИЗИРОВАННАЯ ВЕРСИЯ"""
    page = max(1, int(request.GET.get('page', 1)))
    limit = max(1, min(int(request.GET.get('limit', 50)), 1000))
    offset = (page - 1) * limit
    
    # Полнотекстовый поиск
    search_query = request.GET.get('search', '').strip()
    
    # Базовые параметры для SQL
    sql_params = []
    where_conditions = []
    
    # Условия поиска
    if search_query:
        search_condition = """(
            st.short_code ILIKE %s OR 
            st.identifier ILIKE %s OR 
            st.rrna_taxonomy ILIKE %s OR 
            st.name_alt ILIKE %s OR 
            st.rcam_collection_id ILIKE %s
        )"""
        where_conditions.append(search_condition)
        search_param = f"%{search_query}%"
        sql_params.extend([search_param] * 5)
    
    # Обработка расширенных фильтров
    def process_filter_param(param_name, param_value):
        """Обработка расширенных операторов фильтрации"""
        if not param_value:
            return
        
        # Карта полей к колонкам в БД
        field_mapping = {
            'short_code': 'st.short_code',
            'identifier': 'st.identifier',
            'rrna_taxonomy': 'st.rrna_taxonomy',
            'rcam_collection_id': 'st.rcam_collection_id',
            'created_at': 'st.created_at'
        }
        
        # Разбираем параметр на поле и оператор
        if '__' in param_name:
            field, operator = param_name.split('__', 1)
        else:
            field = param_name
            # Для числовых/датовых полей безопаснее по умолчанию использовать '='
            numeric_or_date_fields = {'strain_id', 'box_id', 'created_at'}
            operator = 'equals' if field in numeric_or_date_fields else 'ilike'
        
        # Получаем имя колонки
        db_field = field_mapping.get(field)
        if not db_field:
            return
        
        # Применяем оператор
        if operator == 'startswith':
            where_conditions.append(f"{db_field} ILIKE %s")
            sql_params.append(f"{param_value}%")
        elif operator == 'endswith':
            where_conditions.append(f"{db_field} ILIKE %s")
            sql_params.append(f"%{param_value}")
        elif operator == 'contains' or operator == 'ilike':
            where_conditions.append(f"{db_field} ILIKE %s")
            sql_params.append(f"%{param_value}%")
        elif operator == 'equals' or operator == 'exact':
            if field == 'created_at':
                # Для дат используем точное сравнение
                try:
                    from datetime import datetime
                    date_value = datetime.fromisoformat(param_value.replace('Z', '+00:00'))
                    where_conditions.append(f"{db_field} = %s")
                    sql_params.append(date_value)
                except ValueError:
                    pass
            else:
                # Приводим к числу, если поле числовое
                if field == 'strain_id':
                    try:
                        param_value = int(param_value)
                    except ValueError:
                        return
                where_conditions.append(f"{db_field} = %s")
                sql_params.append(param_value)
        elif operator == 'gt':
            if field == 'created_at':
                try:
                    from datetime import datetime
                    date_value = datetime.fromisoformat(param_value.replace('Z', '+00:00'))
                    where_conditions.append(f"{db_field} > %s")
                    sql_params.append(date_value)
                except ValueError:
                    pass
            else:
                where_conditions.append(f"{db_field} > %s")
                sql_params.append(param_value)
        elif operator == 'lt':
            if field == 'created_at':
                try:
                    from datetime import datetime
                    date_value = datetime.fromisoformat(param_value.replace('Z', '+00:00'))
                    where_conditions.append(f"{db_field} < %s")
                    sql_params.append(date_value)
                except ValueError:
                    pass
            else:
                where_conditions.append(f"{db_field} < %s")
                sql_params.append(param_value)
        elif operator == 'gte':
            if field == 'created_at':
                try:
                    from datetime import datetime
                    date_value = datetime.fromisoformat(param_value.replace('Z', '+00:00'))
                    where_conditions.append(f"{db_field} >= %s")
                    sql_params.append(date_value)
                except ValueError:
                    pass
            else:
                where_conditions.append(f"{db_field} >= %s")
                sql_params.append(param_value)
        elif operator == 'lte':
            if field == 'created_at':
                try:
                    from datetime import datetime
                    date_value = datetime.fromisoformat(param_value.replace('Z', '+00:00'))
                    where_conditions.append(f"{db_field} <= %s")
                    sql_params.append(date_value)
                except ValueError:
                    pass
            else:
                where_conditions.append(f"{db_field} <= %s")
                sql_params.append(param_value)

    # Обрабатываем все GET параметры
    for param_name, param_value in request.GET.items():
        if param_name in ['page', 'limit', 'search']:
            continue  # Пропускаем системные параметры
        
        # Обратная совместимость для старых параметров
        if param_name == 'rcam_id':
            process_filter_param('rcam_collection_id', param_value)
        elif param_name == 'taxonomy':
            process_filter_param('rrna_taxonomy', param_value)
        elif param_name == 'created_after':
            process_filter_param('created_at__gte', param_value)
        elif param_name == 'created_before':
            process_filter_param('created_at__lte', param_value)
        else:
            # Новые расширенные фильтры
            process_filter_param(param_name, param_value)
    
    # Формируем WHERE условие
    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)
    
    # SQL для подсчета общего количества
    count_sql = f"""
        SELECT COUNT(*) as total
        FROM strain_management_strain st
        {where_clause}
    """
    
    # SQL для получения данных с пагинацией
    data_sql = f"""
        SELECT 
            st.id,
            st.short_code,
            st.identifier,
            st.rrna_taxonomy,
            st.name_alt,
            st.rcam_collection_id,
            st.created_at,
            st.updated_at
        FROM strain_management_strain st
        {where_clause}
        ORDER BY st.id
        LIMIT %s OFFSET %s
    """
    
    with connection.cursor() as cursor:
        # Получаем общее количество
        cursor.execute(count_sql, sql_params)
        total_count = cursor.fetchone()[0]
        
        # Получаем данные
        cursor.execute(data_sql, sql_params + [limit, offset])
        columns = [col[0] for col in cursor.description]
        strains_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Метаданные пагинации
    total_pages = (total_count + limit - 1) // limit
    has_next = page < total_pages
    has_previous = page > 1
    
    # Форматируем данные
    data = []
    for strain in strains_data:
        data.append({
            'id': strain['id'],
            'short_code': strain['short_code'],
            'identifier': strain['identifier'],
            'rrna_taxonomy': strain['rrna_taxonomy'],
            'name_alt': strain['name_alt'],
            'rcam_collection_id': strain['rcam_collection_id'],
            'created_at': strain['created_at'].isoformat() if strain['created_at'] else None,
            'updated_at': strain['updated_at'].isoformat() if strain['updated_at'] else None,
        })
    
    return Response({
        'strains': data,
        'pagination': {
            'total': total_count,
            'shown': len(data),
            'page': page,
            'limit': limit,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_previous': has_previous,
            'offset': offset
        },
        'search_query': search_query,
        'filters_applied': {
            'search': bool(search_query),
            'advanced_filters': [param for param in request.GET.keys() 
                               if param not in ['page', 'limit', 'search'] and request.GET[param]],
            'total_filters': len([param for param in request.GET.keys() 
                                if param not in ['page', 'limit', 'search'] and request.GET[param]]),
        }
    })


@api_view(['GET'])
def get_strain(request, strain_id):
    """Получение детальной информации о штамме"""
    try:
        strain = Strain.objects.select_related().prefetch_related('samples').get(id=strain_id)
        
        # Подсчитываем статистику по образцам
        samples_count = strain.samples.count()
        samples_with_photo = strain.samples.filter(has_photo=True).count()
        # Динамические характеристики теперь обрабатываются через SampleCharacteristicValue
        samples_with_characteristics = strain.samples.filter(characteristic_values__isnull=False).distinct().count()
        
        return Response({
            'id': strain.id,
            'short_code': strain.short_code,
            'identifier': strain.identifier,
            'rrna_taxonomy': strain.rrna_taxonomy,
            'name_alt': strain.name_alt,
            'rcam_collection_id': strain.rcam_collection_id,
            'created_at': strain.created_at.isoformat() if strain.created_at else None,
            'updated_at': strain.updated_at.isoformat() if strain.updated_at else None,
            # Статистика по образцам
            'samples_stats': {
                'total_count': samples_count,
                'with_photo_count': samples_with_photo,
                'with_characteristics_count': samples_with_characteristics,
                'photo_percentage': round((samples_with_photo / samples_count * 100) if samples_count > 0 else 0, 1),
                'characteristics_percentage': round((samples_with_characteristics / samples_count * 100) if samples_count > 0 else 0, 1),
            }
        })
    
    except Strain.DoesNotExist:
        return Response({
            'error': 'Штамм не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Unexpected error in get_strain: {e}")
        return Response({
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@csrf_exempt
def update_strain(request, strain_id):
    """Обновление существующего штамма"""
    try:
        # Создаем схему для обновления без ID
        class UpdateStrainSchema(BaseModel):
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
        
        # Проверяем существование штамма
        try:
            strain = Strain.objects.get(id=strain_id)
        except Strain.DoesNotExist:
            return Response({
                'error': f'Штамм с ID {strain_id} не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Валидация входных данных
        validated_data = UpdateStrainSchema.model_validate(request.data)
        
        # Проверка уникальности короткого кода (исключая текущий штамм)
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
def create_strain(request):
    """Создание нового штамма"""
    try:
        # Создаем схему для создания без ID
        class CreateStrainSchema(BaseModel):
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
        
        # Валидация входных данных
        validated_data = CreateStrainSchema.model_validate(request.data)
        
        # Проверка уникальности короткого кода
        if Strain.objects.filter(short_code=validated_data.short_code).exists():
            return Response({
                'error': f'Штамм с кодом "{validated_data.short_code}" уже существует'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создание штамма с авто-восстановлением последовательности PK при необходимости
        try:
            with transaction.atomic():
                strain = Strain.objects.create(
                    short_code=validated_data.short_code,
                    rrna_taxonomy=validated_data.rrna_taxonomy,
                    identifier=validated_data.identifier,
                    name_alt=validated_data.name_alt,
                    rcam_collection_id=validated_data.rcam_collection_id,
                )
                logger.info(
                    f"Created new strain: {strain.short_code} (ID: {strain.id})"
                )
        except IntegrityError as ie:
            # Попытка исправить несинхронизированную последовательность PK
            if "duplicate key value violates unique constraint" in str(ie) and "_pkey" in str(ie):
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


@api_view(['POST'])
def validate_strain(request):
    """Валидация данных штамма с помощью Pydantic"""
    try:
        # Используем схему без ID для валидации данных создания
        class CreateStrainSchema(BaseModel):
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
        
        validated_data = CreateStrainSchema.model_validate(request.data)
        
        return Response({
            'valid': True,
            'data': validated_data.model_dump(),
            'message': 'Данные штамма корректны'
        })
    
    except ValidationError as e:
        return Response({
            'valid': False,
            'errors': e.errors(),
            'message': 'Ошибки валидации данных'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Unexpected error in validate_strain: {e}")
        return Response({
            'valid': False,
            'error': str(e),
            'message': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def list_samples(request):
    """Список образцов с связанными данными и расширенным поиском - ОПТИМИЗИРОВАННАЯ ВЕРСИЯ"""
    page = int(request.GET.get('page', 1))
    limit = min(int(request.GET.get('limit', 100)), 1000)  # Максимум 1000 записей за раз
    offset = (page - 1) * limit
    
    # Полнотекстовый поиск
    search_query = request.GET.get('search', '').strip()
    
    # Базовые параметры для SQL
    sql_params = []
    where_conditions = []
    
    # Условия поиска
    if search_query:
        search_condition = """(
            sam.original_sample_number ILIKE %s OR
            st.short_code ILIKE %s OR
            st.identifier ILIKE %s OR
            st.rrna_taxonomy ILIKE %s OR
            st.name_alt ILIKE %s OR
            st.rcam_collection_id ILIKE %s OR
            src.name ILIKE %s OR
            loc.name ILIKE %s OR
            storage.box_id ILIKE %s OR
            storage.cell_id ILIKE %s OR
            idx.letter_value ILIKE %s
        )"""
        where_conditions.append(search_condition)
        search_param = f"%{search_query}%"
        sql_params.extend([search_param] * 11)
    
    # ------------------ Расширенные фильтры (динамические) ------------------ #
    def process_sample_filter_param(param_name, param_value):
        """Обработка расширенных операторов фильтрации для образцов"""
        if not param_value:
            return

        field_mapping = {
            'original_sample_number': 'sam.original_sample_number',
            'strain_id': 'sam.strain_id',
            'box_id': 'storage.box_id',
            'organism_name': 'src.name',
            'created_at': 'sam.created_at',
        }

        if '__' in param_name:
            field, operator = param_name.split('__', 1)
        else:
            field = param_name
            # Для числовых/датовых полей и полей выбора безопаснее по умолчанию использовать '='
            exact_match_fields = {'strain_id', 'box_id', 'created_at', 'organism_name'}
            operator = 'equals' if field in exact_match_fields else 'ilike'

        db_field = field_mapping.get(field)
        if not db_field:
            return

        # Текстовые и числовые операторы
        if operator == 'startswith':
            where_conditions.append(f"{db_field} ILIKE %s")
            sql_params.append(f"{param_value}%")
        elif operator == 'endswith':
            where_conditions.append(f"{db_field} ILIKE %s")
            sql_params.append(f"%{param_value}")
        elif operator in ['contains', 'ilike']:
            where_conditions.append(f"{db_field} ILIKE %s")
            sql_params.append(f"%{param_value}%")
        elif operator in ['equals', 'exact']:
            if field == 'created_at':
                try:
                    from datetime import datetime
                    date_val = datetime.fromisoformat(param_value.replace('Z', '+00:00'))
                    where_conditions.append(f"{db_field} = %s")
                    sql_params.append(date_val)
                except ValueError:
                    pass
            else:
                # Приводим к числу, если поле числовое
                if field == 'strain_id':
                    try:
                        param_value = int(param_value)
                    except ValueError:
                        return
                where_conditions.append(f"{db_field} = %s")
                sql_params.append(param_value)
        elif operator == 'gt':
            where_conditions.append(f"{db_field} > %s")
            sql_params.append(param_value)
        elif operator == 'lt':
            where_conditions.append(f"{db_field} < %s")
            sql_params.append(param_value)
        elif operator == 'gte':
            where_conditions.append(f"{db_field} >= %s")
            sql_params.append(param_value)
        elif operator == 'lte':
            where_conditions.append(f"{db_field} <= %s")
            sql_params.append(param_value)

    # Перебираем все GET параметры и применяем процессинг
    for p_name, p_val in request.GET.items():
        if p_name in ['page', 'limit', 'search']:
            continue
        process_sample_filter_param(p_name, p_val)
    
    # Дополнительные фильтры
    if 'has_photo' in request.GET:
        where_conditions.append("sam.has_photo = %s")
        sql_params.append(request.GET['has_photo'].lower() == 'true')
        
    # Старые характеристики удалены, теперь используются динамические характеристики
        
    if 'source_id' in request.GET:
        where_conditions.append("sam.source_id = %s")
        sql_params.append(int(request.GET['source_id']))
        
    if 'location_id' in request.GET:
        where_conditions.append("sam.location_id = %s")
        sql_params.append(int(request.GET['location_id']))

    # Фильтры по характеристикам теперь обрабатываются через новую систему динамических характеристик
    # TODO: Добавить поддержку фильтрации по динамическим характеристикам при необходимости

    if 'iuk_color_id' in request.GET:
        where_conditions.append("sam.iuk_color_id = %s")
        sql_params.append(int(request.GET['iuk_color_id']))

    if 'amylase_variant_id' in request.GET:
        where_conditions.append("sam.amylase_variant_id = %s")
        sql_params.append(int(request.GET['amylase_variant_id']))

    if 'growth_medium_id' in request.GET:
        # Фильтр по средам роста (многие-ко-многим)
        where_conditions.append("""
            sam.id IN (
                SELECT sgm.sample_id
                FROM sample_management_sample_growth_media sgm
                WHERE sgm.growth_medium_id = %s
            )
        """)
        sql_params.append(int(request.GET['growth_medium_id']))


    # Фильтры по датам
    if 'created_after' in request.GET:
        try:
            from datetime import datetime
            date_after = datetime.fromisoformat(request.GET['created_after'].replace('Z', '+00:00'))
            where_conditions.append("sam.created_at >= %s")
            sql_params.append(date_after)
        except ValueError:
            pass
            
    if 'created_before' in request.GET:
        try:
            from datetime import datetime
            date_before = datetime.fromisoformat(request.GET['created_before'].replace('Z', '+00:00'))
            where_conditions.append("sam.created_at <= %s")
            sql_params.append(date_before)
        except ValueError:
            pass
    
    # Формируем WHERE условие
    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)
    
    # SQL для подсчета общего количества
    count_sql = f"""
        SELECT COUNT(*) as total
        FROM sample_management_sample sam
        LEFT JOIN strain_management_strain st ON sam.strain_id = st.id
        LEFT JOIN storage_management_storage storage ON sam.storage_id = storage.id
        LEFT JOIN reference_data_source src ON sam.source_id = src.id

        LEFT JOIN reference_data_location loc ON sam.location_id = loc.id
        LEFT JOIN reference_data_indexletter idx ON sam.index_letter_id = idx.id
        {where_clause}
    """
    
    # SQL для получения данных с пагинацией и всеми связанными данными
    data_sql = f"""
        SELECT 
            sam.id,
            sam.original_sample_number,
            sam.has_photo,
            sam.created_at,
            sam.updated_at,
            -- Strain data
            st.id as strain_id,
            st.short_code as strain_short_code,
            st.identifier as strain_identifier,
            st.rrna_taxonomy as strain_rrna_taxonomy,
            -- Storage data
            storage.id as storage_id,
            storage.box_id as storage_box_id,
            storage.cell_id as storage_cell_id,
            -- Source data
            src.id as source_id,
            src.name as source_name,
            -- Location data
            loc.id as location_id,
            loc.name as location_name,
            -- Index letter data
            idx.id as index_letter_id,
            idx.letter_value as index_letter_value
        FROM sample_management_sample sam
        LEFT JOIN strain_management_strain st ON sam.strain_id = st.id
        LEFT JOIN storage_management_storage storage ON sam.storage_id = storage.id
        LEFT JOIN reference_data_source src ON sam.source_id = src.id

        LEFT JOIN reference_data_location loc ON sam.location_id = loc.id
        LEFT JOIN reference_data_indexletter idx ON sam.index_letter_id = idx.id
        {where_clause}
        ORDER BY sam.id
        LIMIT %s OFFSET %s
    """
    
    with connection.cursor() as cursor:
        # Получаем общее количество
        cursor.execute(count_sql, sql_params)
        total_count = cursor.fetchone()[0]
        
        # Получаем данные
        cursor.execute(data_sql, sql_params + [limit, offset])
        columns = [col[0] for col in cursor.description]
        samples_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Вычисляем метаданные пагинации
    total_pages = (total_count + limit - 1) // limit  # Округление вверх
    has_next = page < total_pages
    has_previous = page > 1
    
    # Форматируем данные
    data = []
    for sample in samples_data:
        # Получаем дополнительные данные для новых полей
        sample_obj = Sample.objects.select_related(
            'iuk_color', 'amylase_variant', 'source'
        ).get(id=sample['id'])

        # Получаем динамические характеристики для этого образца
        characteristics = {}
        characteristic_values = SampleCharacteristicValue.objects.filter(
            sample_id=sample['id']
        ).select_related('characteristic')
        
        for cv in characteristic_values:
            char = cv.characteristic
            value = None
            
            if char.characteristic_type == 'boolean':
                value = cv.boolean_value
            elif char.characteristic_type == 'text':
                value = cv.text_value
            elif char.characteristic_type == 'select':
                value = cv.select_value
            
            characteristics[char.name] = {
                'id': char.id,
                'display_name': char.display_name,
                'type': char.characteristic_type,
                'value': value,
                'options': char.options,
                'color': char.color
            }

        data.append({
            'id': sample['id'],
            'strain': {
                'id': sample['strain_id'],
                'short_code': sample['strain_short_code'],
                'identifier': sample['strain_identifier'],
                'rrna_taxonomy': sample['strain_rrna_taxonomy'],
            } if sample['strain_id'] else None,
            'storage': {
                'id': sample['storage_id'],
                'box_id': sample['storage_box_id'],
                'cell_id': sample['storage_cell_id'],
            } if sample['storage_id'] else None,
            'source': {
                'id': sample['source_id'],
                'name': sample['source_name'],
            } if sample['source_id'] else None,
            'location': {
                'id': sample['location_id'],
                'name': sample['location_name'],
            } if sample['location_id'] else None,
            'index_letter': {
                'id': sample['index_letter_id'],
                'letter_value': sample['index_letter_value'],
            } if sample['index_letter_id'] else None,
            'original_sample_number': sample['original_sample_number'],
            'has_photo': sample['has_photo'],
            'iuk_color': {
                'id': sample_obj.iuk_color.id if sample_obj.iuk_color else None,
                'name': sample_obj.iuk_color.name if sample_obj.iuk_color else None,
                'hex_code': sample_obj.iuk_color.hex_code if sample_obj.iuk_color else None,
            } if sample_obj.iuk_color else None,
            'amylase_variant': {
                'id': sample_obj.amylase_variant.id if sample_obj.amylase_variant else None,
                'name': sample_obj.amylase_variant.name if sample_obj.amylase_variant else None,
                'description': sample_obj.amylase_variant.description if sample_obj.amylase_variant else None,
            } if sample_obj.amylase_variant else None,
            'growth_media': [
                {
                    'id': gm.growth_medium.id,
                    'name': gm.growth_medium.name,
                    'description': gm.growth_medium.description
                } for gm in sample_obj.growth_media.all()
            ],
            'characteristics': characteristics,
            'created_at': sample['created_at'].isoformat() if sample['created_at'] else None,
            'updated_at': sample['updated_at'].isoformat() if sample['updated_at'] else None,
        })
    
    return Response({
        'samples': data,
        'pagination': {
            'total': total_count,
            'shown': len(data),
            'page': page,
            'limit': limit,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_previous': has_previous,
            'offset': offset
        },
        'search_query': search_query,
        'filters_applied': {
            'search': bool(search_query),
            'strain_id': 'strain_id' in request.GET,
            'has_photo': 'has_photo' in request.GET,
            'box_id': 'box_id' in request.GET,
            'source_id': 'source_id' in request.GET,
            'location_id': 'location_id' in request.GET,
            'date_range': 'created_after' in request.GET or 'created_before' in request.GET,
            'iuk_color_id': 'iuk_color_id' in request.GET,
            'amylase_variant_id': 'amylase_variant_id' in request.GET,
            'growth_medium_id': 'growth_medium_id' in request.GET,
            'advanced_filters': [param for param in request.GET.keys() if param not in ['page', 'limit', 'search'] and request.GET[param]],
            'total_filters': len([param for param in request.GET.keys() if param not in ['page', 'limit', 'search'] and request.GET[param]]),
        }
    })


@api_view(['POST'])
def validate_sample(request):
    """Валидация данных образца с помощью Pydantic"""
    try:
        validated_data = SampleSchema.model_validate(request.data)
        
        return Response({
            'valid': True,
            'data': validated_data.model_dump(),
            'message': 'Данные образца корректны'
        })
    
    except ValidationError as e:
        return Response({
            'valid': False,
            'errors': e.errors(),
            'message': 'Ошибки валидации данных'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Unexpected error in validate_sample: {e}")
        return Response({
            'valid': False,
            'error': str(e),
            'message': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
def api_stats(request):
    """Общая статистика с информацией о валидации и детализацией по боксам"""
    from django.db import connection
    
    # Получаем общую статистику хранения
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total_cells,
                COUNT(CASE WHEN sam.id IS NOT NULL THEN 1 ELSE NULL END) as occupied_cells
            FROM storage_management_storage s
            LEFT JOIN sample_management_sample sam ON s.id = sam.storage_id
        """)
        row = cursor.fetchone()
        total_storage_cells, occupied_storage_cells = row
    
    # Получаем детализацию по боксам (объединяем логику storage_summary)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                s.box_id,
                COUNT(*) as total_cells,
                COUNT(CASE WHEN sam.id IS NOT NULL THEN 1 ELSE NULL END) as occupied_cells
            FROM storage_management_storage s
            LEFT JOIN sample_management_sample sam ON s.id = sam.storage_id
            GROUP BY s.box_id
            ORDER BY s.box_id
        """)
        box_rows = cursor.fetchall()

    # Формируем данные по боксам
    boxes = []
    total_boxes = 0
    for box_id, total, occupied in box_rows:
        boxes.append({'box_id': box_id, 'occupied': occupied, 'total': total})
        total_boxes += 1
    
    # Рассчитываем заполненность хранилища
    storage_occupancy = 0
    if total_storage_cells > 0:
        storage_occupancy = round((occupied_storage_cells / total_storage_cells) * 100, 1)

    return Response({
        'counts': {
            'strains': Strain.objects.count(),
            'samples': Sample.objects.count(),
            'storage_units': total_storage_cells,  # ИСПРАВЛЕНО: используем правильный подсчет
            'sources': Source.objects.count(),
            'locations': Location.objects.count(),
            'index_letters': IndexLetter.objects.count(),
            'comments': Comment.objects.count(),
            'appendix_notes': AppendixNote.objects.count(),
            # Новые модели характеристик
            'iuk_colors': IUKColor.objects.count(),
            'amylase_variants': AmylaseVariant.objects.count(),
            'growth_media': GrowthMedium.objects.count(),
        },
        'storage': {
            'total_cells': total_storage_cells,
            'occupied_cells': occupied_storage_cells,
            'occupancy_percentage': storage_occupancy,
            # Добавляем детализацию по боксам
            'boxes': boxes,
            'total_boxes': total_boxes,
        },
        'samples_analysis': {
            'with_photo': Sample.objects.filter(has_photo=True).count(),
            # Динамические характеристики - получаем статистику по каждой активной характеристике
            'characteristics': {
                char.name: SampleCharacteristicValue.objects.filter(
                    characteristic=char,
                    boolean_value=True
                ).count() if char.characteristic_type == 'boolean' else SampleCharacteristicValue.objects.filter(
                    characteristic=char
                ).exclude(
                    models.Q(text_value__isnull=True) | models.Q(text_value='') |
                    models.Q(select_value__isnull=True) | models.Q(select_value='')
                ).count()
                for char in SampleCharacteristic.objects.filter(is_active=True).order_by('order', 'name')
            },
            'total_characteristics': SampleCharacteristicValue.objects.count(),
            'unique_characteristics': SampleCharacteristic.objects.filter(is_active=True).count(),
        },
        'validation': {
            'engine': 'Pydantic 2.x',
            'schemas_available': [
                'StrainSchema', 'SampleSchema', 'StorageSchema',
                'SourceSchema', 'LocationSchema', 'IndexLetterSchema',
                'CommentSchema', 'AppendixNoteSchema',
                # Новые модели характеристик
                'IUKColorSchema', 'AmylaseVariantSchema', 'GrowthMediumSchema'
            ]
        }
    })


@api_view(['POST'])
@csrf_exempt
def create_sample(request):
    """Создание нового образца"""
    try:
        # Динамически создаем схему валидации
        class CreateSampleSchema(BaseModel):
            strain_id: Optional[int] = Field(None, ge=1, description="ID штамма")
            index_letter_id: Optional[int] = Field(None, ge=1, description="ID индексной буквы")
            storage_id: Optional[int] = Field(None, ge=1, description="ID хранилища")
            original_sample_number: Optional[str] = Field(None, max_length=100, description="Оригинальный номер образца")
            source_id: Optional[int] = Field(None, ge=1, description="ID источника")
            location_id: Optional[int] = Field(None, ge=1, description="ID местоположения")
            appendix_note: Optional[str] = Field(None, max_length=1000, description="Примечание")
            comment: Optional[str] = Field(None, max_length=1000, description="Комментарий")
            has_photo: bool = Field(default=False, description="Есть ли фото")

            # Новые поля характеристик
            mobilizes_phosphates: bool = Field(default=False, description="Мобилизирует фосфаты")
            stains_medium: bool = Field(default=False, description="Окрашивает среду")
            produces_siderophores: bool = Field(default=False, description="Вырабатывает сидерофоры")
            iuk_color_id: Optional[int] = Field(None, ge=1, description="ID цвета ИУК")
            amylase_variant_id: Optional[int] = Field(None, ge=1, description="ID варианта амилазы")
            growth_media_ids: Optional[list[int]] = Field(None, description="Список ID сред роста")

            @field_validator('original_sample_number', 'appendix_note', 'comment')
            @classmethod
            def validate_string_fields(cls, v: Optional[str]) -> Optional[str]:
                if v is not None:
                    v = v.strip()
                    return v if v else None
                return v

            @field_validator('growth_media_ids')
            @classmethod
            def validate_growth_media_ids(cls, v: Optional[list[int]]) -> Optional[list[int]]:
                if v is not None:
                    # Убираем дубликаты и None значения
                    v = list(set(filter(None, v)))
                    return v if v else None
                return v

        validated_data = CreateSampleSchema.model_validate(request.data)
        
        # Проверяем существование связанных объектов
        if validated_data.strain_id:
            if not Strain.objects.filter(id=validated_data.strain_id).exists():
                return Response({
                    'error': f'Штамм с ID {validated_data.strain_id} не найден'
                }, status=status.HTTP_404_NOT_FOUND)
        
        if validated_data.storage_id:
            if not Storage.objects.filter(id=validated_data.storage_id).exists():
                return Response({
                    'error': f'Хранилище с ID {validated_data.storage_id} не найдено'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Проверяем, не занята ли ячейка
            existing_sample = Sample.objects.filter(
                storage_id=validated_data.storage_id
            ).first()  # Исключаем помеченные как свободные
            
            if existing_sample:
                storage = Storage.objects.get(id=validated_data.storage_id)
                return Response({
                    'error': f'Ячейка {storage.box_id}-{storage.cell_id} уже занята образцом {existing_sample.id}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if validated_data.source_id:
            if not Source.objects.filter(id=validated_data.source_id).exists():
                return Response({
                    'error': f'Источник с ID {validated_data.source_id} не найден'
                }, status=status.HTTP_404_NOT_FOUND)
        
        if validated_data.location_id:
            if not Location.objects.filter(id=validated_data.location_id).exists():
                return Response({
                    'error': f'Местоположение с ID {validated_data.location_id} не найдено'
                }, status=status.HTTP_404_NOT_FOUND)
        
        if validated_data.index_letter_id:
            if not IndexLetter.objects.filter(id=validated_data.index_letter_id).exists():
                return Response({
                    'error': f'Индексная буква с ID {validated_data.index_letter_id} не найдена'
                }, status=status.HTTP_404_NOT_FOUND)

        # Проверки для новых полей характеристик
        if validated_data.iuk_color_id:
            if not IUKColor.objects.filter(id=validated_data.iuk_color_id).exists():
                return Response({
                    'error': f'Цвет ИУК с ID {validated_data.iuk_color_id} не найден'
                }, status=status.HTTP_404_NOT_FOUND)

        if validated_data.amylase_variant_id:
            if not AmylaseVariant.objects.filter(id=validated_data.amylase_variant_id).exists():
                return Response({
                    'error': f'Вариант амилазы с ID {validated_data.amylase_variant_id} не найден'
                }, status=status.HTTP_404_NOT_FOUND)

        # Проверки для appendix_note и comment не нужны, так как они текстовые поля
        
        create_kwargs = {
            'strain_id': validated_data.strain_id,
            'index_letter_id': validated_data.index_letter_id,
            'storage_id': validated_data.storage_id,
            'original_sample_number': validated_data.original_sample_number,
            'source_id': validated_data.source_id,
            'location_id': validated_data.location_id,
            'appendix_note': validated_data.appendix_note,
            'comment': validated_data.comment,
            'has_photo': validated_data.has_photo,
            'iuk_color_id': validated_data.iuk_color_id,
            'amylase_variant_id': validated_data.amylase_variant_id,
        }

        optional_boolean_flags = {
            'mobilizes_phosphates': validated_data.mobilizes_phosphates,
            'stains_medium': validated_data.stains_medium,
            'produces_siderophores': validated_data.produces_siderophores,
        }
        for field_name, value in optional_boolean_flags.items():
            if hasattr(Sample, field_name):
                create_kwargs[field_name] = value

        # Создание образца с авто-сбросом последовательности при необходимости
        try:
            with transaction.atomic():
                sample = Sample.objects.create(**create_kwargs)

                _assign_growth_media(sample, validated_data.growth_media_ids)

                logger.info(f"Created new sample (ID: {sample.id})")
        except IntegrityError as ie:
            if "duplicate key value violates unique constraint" in str(ie) and "_pkey" in str(ie):
                logger.warning("IntegrityError on Sample create — resetting sequence and retry")
                reset_sequence(Sample)
                with transaction.atomic():
                    sample = Sample.objects.create(**create_kwargs)
                    logger.info(f"Created new sample after sequence reset (ID: {sample.id})")
            else:
                raise
        
        return Response({
            'id': sample.id,
            'message': f'Образец {sample.id} успешно создан',
            'sample': {
                'id': sample.id,
                'strain_id': sample.strain_id,
                'storage_id': sample.storage_id,
                'original_sample_number': sample.original_sample_number,
                'has_photo': sample.has_photo,
            }
        }, status=status.HTTP_201_CREATED)
    
    except ValidationError as e:
        return Response({
            'error': 'Ошибка валидации данных',
            'details': e.errors()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Unexpected error in create_sample: {e}")
        return Response({
            'error': f'Ошибка при создании образца: {e}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_sample(request, sample_id):
    """Получение детальной информации об образце"""
    try:
        sample = Sample.objects.select_related(
            'strain', 'storage', 'source', 'location', 'index_letter'
        ).get(id=sample_id)
        
        # Получаем информацию о средах роста
        growth_media = []
        if hasattr(sample, 'growth_media'):
            growth_media = [
                {
                    'id': gm.growth_medium.id,
                    'name': gm.growth_medium.name,
                    'description': gm.growth_medium.description
                } for gm in sample.growth_media.all()
            ]

        # Получаем динамические характеристики
        characteristics = {}
        characteristic_values = SampleCharacteristicValue.objects.filter(
            sample=sample
        ).select_related('characteristic')
        
        for cv in characteristic_values:
            char = cv.characteristic
            value = None
            
            if char.characteristic_type == 'boolean':
                value = cv.boolean_value
            elif char.characteristic_type == 'text':
                value = cv.text_value
            elif char.characteristic_type == 'select':
                value = cv.select_value
            
            characteristics[char.name] = {
                'id': char.id,
                'display_name': char.display_name,
                'type': char.characteristic_type,
                'value': value,
                'options': char.options,
                'color': char.color
            }

        return Response({
            'id': sample.id,
            'strain': {
                'id': sample.strain.id if sample.strain else None,
                'short_code': sample.strain.short_code if sample.strain else None,
                'identifier': sample.strain.identifier if sample.strain else None,
                'rrna_taxonomy': sample.strain.rrna_taxonomy if sample.strain else None,
            } if sample.strain else None,
            'storage': {
                'id': sample.storage.id if sample.storage else None,
                'box_id': sample.storage.box_id if sample.storage else None,
                'cell_id': sample.storage.cell_id if sample.storage else None,
            } if sample.storage else None,
            'source': {
                'id': sample.source.id if sample.source else None,
                'name': sample.source.name if sample.source else None,
            } if sample.source else None,
            'location': {
                'id': sample.location.id if sample.location else None,
                'name': sample.location.name if sample.location else None,
            } if sample.location else None,
            'index_letter': {
                'id': sample.index_letter.id if sample.index_letter else None,
                'letter_value': sample.index_letter.letter_value if sample.index_letter else None,
            } if sample.index_letter else None,
            'appendix_note': sample.appendix_note,
            'comment': sample.comment,
            'original_sample_number': sample.original_sample_number,
            'has_photo': sample.photos.exists(),
            'photos': [
                {
                    'id': photo.id,
                    'url': request.build_absolute_uri(photo.image.url),
                    'uploaded_at': photo.uploaded_at.isoformat()
                } for photo in sample.photos.all()
            ],
            'iuk_color': {
                'id': sample.iuk_color.id if sample.iuk_color else None,
                'name': sample.iuk_color.name if sample.iuk_color else None,
                'hex_code': sample.iuk_color.hex_code if sample.iuk_color else None,
            } if sample.iuk_color else None,
            'amylase_variant': {
                'id': sample.amylase_variant.id if sample.amylase_variant else None,
                'name': sample.amylase_variant.name if sample.amylase_variant else None,
                'description': sample.amylase_variant.description if sample.amylase_variant else None,
            } if sample.amylase_variant else None,
            'growth_media': growth_media,
            'characteristics': characteristics,
            'created_at': sample.created_at.isoformat() if sample.created_at else None,
            'updated_at': sample.updated_at.isoformat() if sample.updated_at else None,
        })
    
    except Sample.DoesNotExist:
        return Response({
            'error': f'Образец с ID {sample_id} не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Unexpected error in get_sample: {e}")
        return Response({
            'error': f'Ошибка при получении образца: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@csrf_exempt
def update_sample(request, sample_id):
    """Обновление данных образца"""
    logger.info(f"🔧 update_sample called for sample {sample_id}")
    logger.info(f"🔧 Request data: {request.data}")
    
    try:
        sample = Sample.objects.get(id=sample_id)
    except Sample.DoesNotExist:
        return Response({
            'error': f'Образец с ID {sample_id} не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        validated_data = UpdateSampleSchema.model_validate(request.data)
        logger.info(f"🔧 Validated data: {validated_data.model_dump()}")
        
        # Проверяем существование связанных объектов если они указаны
        if validated_data.strain_id is not None:
            if not Strain.objects.filter(id=validated_data.strain_id).exists():
                return Response({
                    'error': f'Штамм с ID {validated_data.strain_id} не найден'
                }, status=status.HTTP_404_NOT_FOUND)
        
        if validated_data.storage_id is not None:
            if not Storage.objects.filter(id=validated_data.storage_id).exists():
                return Response({
                    'error': f'Хранилище с ID {validated_data.storage_id} не найдено'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Проверяем, не занята ли ячейка другим образцом
            existing_sample = Sample.objects.filter(
                storage_id=validated_data.storage_id
            ).exclude(id=sample_id).first()
            
            if existing_sample:
                storage = Storage.objects.get(id=validated_data.storage_id)
                return Response({
                    'error': f'Ячейка {storage.box_id}-{storage.cell_id} уже занята образцом {existing_sample.id}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Аналогичные проверки для других связанных объектов
        if validated_data.source_id is not None and not Source.objects.filter(id=validated_data.source_id).exists():
            return Response({
                'error': f'Источник с ID {validated_data.source_id} не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if validated_data.location_id is not None and not Location.objects.filter(id=validated_data.location_id).exists():
            return Response({
                'error': f'Местоположение с ID {validated_data.location_id} не найдено'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if validated_data.index_letter_id is not None and not IndexLetter.objects.filter(id=validated_data.index_letter_id).exists():
            return Response({
                'error': f'Индексная буква с ID {validated_data.index_letter_id} не найдена'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Проверки для новых полей характеристик
        if validated_data.iuk_color_id is not None:
            if not IUKColor.objects.filter(id=validated_data.iuk_color_id).exists():
                return Response({
                    'error': f'Цвет ИУК с ID {validated_data.iuk_color_id} не найден'
                }, status=status.HTTP_404_NOT_FOUND)

        if validated_data.amylase_variant_id is not None:
            if not AmylaseVariant.objects.filter(id=validated_data.amylase_variant_id).exists():
                return Response({
                    'error': f'Вариант амилазы с ID {validated_data.amylase_variant_id} не найден'
                }, status=status.HTTP_404_NOT_FOUND)

        # Проверки для appendix_note и comment не нужны, так как они текстовые поля
        
        # Обновление данных в транзакции
        with transaction.atomic():
            # Обновляем только переданные поля
            update_fields = []
            for field, value in validated_data.model_dump(exclude_unset=True).items():
                # Преобразуем старые поля в новые
                if field == 'appendix_note_id':
                    field = 'appendix_note'
                elif field == 'comment_id':
                    field = 'comment'
                elif field == 'growth_media_ids':
                    # Обновляем связи со средами роста
                    if value is not None:
                        # Удаляем старые связи
                        SampleGrowthMedia.objects.filter(sample=sample).delete()
                        # Добавляем новые связи
                        for media_id in value:
                            try:
                                media = GrowthMedium.objects.get(id=media_id)
                                SampleGrowthMedia.objects.create(sample=sample, growth_medium=media)
                            except GrowthMedium.DoesNotExist:
                                logger.warning(f"Growth medium with ID {media_id} not found, skipping")
                    continue  # Не добавляем в update_fields
                elif field == 'characteristics':
                    # Обновляем динамические характеристики
                    logger.info(f"🔧 Processing characteristics for sample {sample.id}: {value}")
                    if value is not None:
                        for char_name, char_data in value.items():
                            logger.info(f"🔧 Processing characteristic: {char_name} = {char_data}")
                            try:
                                characteristic = SampleCharacteristic.objects.get(name=char_name, is_active=True)
                                char_value, created = SampleCharacteristicValue.objects.get_or_create(
                                    sample=sample,
                                    characteristic=characteristic
                                )
                                
                                # Устанавливаем значение в зависимости от типа
                                if characteristic.characteristic_type == 'boolean':
                                    char_value.boolean_value = char_data.get('value')
                                    char_value.text_value = None
                                    char_value.select_value = None
                                elif characteristic.characteristic_type == 'text':
                                    char_value.text_value = char_data.get('value')
                                    char_value.boolean_value = None
                                    char_value.select_value = None
                                elif characteristic.characteristic_type == 'select':
                                    char_value.select_value = char_data.get('value')
                                    char_value.boolean_value = None
                                    char_value.text_value = None
                                
                                char_value.save()
                                logger.info(f"✅ Saved characteristic {char_name} for sample {sample.id}: {char_data.get('value')}")
                                
                            except SampleCharacteristic.DoesNotExist:
                                logger.warning(f"Characteristic '{char_name}' not found or inactive, skipping")
                    continue  # Не добавляем в update_fields
                else:
                    setattr(sample, field, value)
                    update_fields.append(field)

            if update_fields:
                sample.save(update_fields=update_fields)
                logger.info(f"Updated sample {sample.id}, fields: {update_fields}")

            # Обновляем связи со средами роста если они указаны
            if validated_data.growth_media_ids is not None:
                # Удаляем существующие связи
                sample.growth_media.clear()
                # Добавляем новые связи
                for media_id in validated_data.growth_media_ids:
                    try:
                        media = GrowthMedium.objects.get(id=media_id)
                        SampleGrowthMedia.objects.create(sample=sample, growth_medium=media)
                    except GrowthMedium.DoesNotExist:
                        logger.warning(f"Growth medium with ID {media_id} not found, skipping")

            return Response({
                'id': sample.id,
                'message': f'Образец {sample.id} успешно обновлен',
                'updated_fields': update_fields
            })
    
    except ValidationError as e:
        return Response({
            'error': 'Ошибка валидации данных',
            'details': e.errors()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Unexpected error in update_sample: {e}")
        return Response({
            'error': f'Ошибка при обновлении образца: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@csrf_exempt
def delete_sample(request, sample_id):
    """Удаление образца"""
    try:
        sample = Sample.objects.get(id=sample_id)
    except Sample.DoesNotExist:
        return Response({
            'error': f'Образец с ID {sample_id} не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        with transaction.atomic():
            sample_info = f"образец {sample.id}"
            if sample.strain:
                sample_info += f" штамма {sample.strain.short_code}"
            if sample.storage:
                sample_info += f" из ячейки {sample.storage.box_id}-{sample.storage.cell_id}"
            
            sample.delete()
            logger.info(f"Deleted sample {sample_id}")
            
            return Response({
                'message': f'Образец {sample_id} успешно удален',
                'deleted_sample': sample_info
            })
    
    except Exception as e:
        logger.error(f"Unexpected error in delete_sample: {e}")
        return Response({
            'error': f'Ошибка при удалении образца: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


MAX_IMAGE_SIZE_MB = 1
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png"]


def _validate_uploaded_image(uploaded_file):
    if uploaded_file.content_type not in ALLOWED_IMAGE_TYPES:
        raise DjangoValidationError("Разрешены только JPEG и PNG файлы")

    if uploaded_file.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise DjangoValidationError("Максимальный размер файла 1 МБ")


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

    for file_obj in request.FILES.getlist("images"):
        try:
            _validate_uploaded_image(file_obj)
            photo = sample.photos.create(image=file_obj)
            created.append({"id": photo.id, "url": photo.image.url})
        except DjangoValidationError as e:
            errors.append(str(e))
        except Exception as e:
            logger.exception("Ошибка при загрузке фото: %s", e)
            errors.append(str(e))

    return Response({"created": created, "errors": errors})


@api_view(["DELETE"])
@csrf_exempt
def delete_sample_photo(request, sample_id, photo_id):
    """Удаляет фотографию образца."""
    try:
        photo = SamplePhoto.objects.get(id=photo_id, sample_id=sample_id)
        photo.delete()
        return Response({"message": "Фото удалено"})
    except SamplePhoto.DoesNotExist:
        return Response({"error": "Фото не найдено"}, status=status.HTTP_404_NOT_FOUND)


