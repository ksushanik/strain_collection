"""
API endpoints с валидацией Pydantic для управления коллекцией штаммов
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional
import logging
from django.db.models import Q
from django.db.models.functions import Lower
from django.db import connection

from .models import (
    IndexLetter, Location, Source, Comment, AppendixNote,
    Storage, Strain, Sample
)
from .schemas import (
    IndexLetterSchema, LocationSchema, SourceSchema,
    CommentSchema, AppendixNoteSchema, StorageSchema,
    StrainSchema, SampleSchema
)
from .utils import log_change, generate_batch_id, model_to_dict

logger = logging.getLogger(__name__)


@api_view(['GET'])
def api_status(request):
    """Статус API с информацией о валидации"""
    return Response({
        'status': 'OK',
        'validation': 'Pydantic 2.x',
        'endpoints': [
            '/api/strains/',
            '/api/strains/create/',
            '/api/strains/<id>/',
            '/api/strains/<id>/update/',
            '/api/strains/<id>/delete/',
            '/api/strains/validate/',
            '/api/strains/bulk-delete/',
            '/api/strains/bulk-update/',
            '/api/strains/export/',
            '/api/samples/',
            '/api/samples/create/',
            '/api/samples/<id>/',
            '/api/samples/<id>/update/',
            '/api/samples/<id>/delete/',
            '/api/samples/validate/',
            '/api/samples/bulk-delete/',
            '/api/samples/bulk-update/',
            '/api/samples/export/',
            '/api/storage/',
            '/api/stats/',
            '/api/reference-data/',
        ]
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
    
    # Дополнительные фильтры
    if 'rcam_id' in request.GET:
        where_conditions.append("st.rcam_collection_id ILIKE %s")
        sql_params.append(f"%{request.GET['rcam_id']}%")
        
    if 'taxonomy' in request.GET:
        where_conditions.append("st.rrna_taxonomy ILIKE %s")
        sql_params.append(f"%{request.GET['taxonomy']}%")
        
    if 'short_code' in request.GET:
        where_conditions.append("st.short_code ILIKE %s")
        sql_params.append(f"%{request.GET['short_code']}%")
        
    if 'identifier' in request.GET:
        where_conditions.append("st.identifier ILIKE %s")
        sql_params.append(f"%{request.GET['identifier']}%")
    
    # Фильтры по датам
    if 'created_after' in request.GET:
        try:
            from datetime import datetime
            date_after = datetime.fromisoformat(request.GET['created_after'].replace('Z', '+00:00'))
            where_conditions.append("st.created_at >= %s")
            sql_params.append(date_after)
        except ValueError:
            pass
            
    if 'created_before' in request.GET:
        try:
            from datetime import datetime
            date_before = datetime.fromisoformat(request.GET['created_before'].replace('Z', '+00:00'))
            where_conditions.append("st.created_at <= %s")
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
        FROM collection_manager_strain st
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
        FROM collection_manager_strain st
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
            'rcam_id': 'rcam_id' in request.GET,
            'taxonomy': 'taxonomy' in request.GET,
            'short_code': 'short_code' in request.GET,
            'identifier': 'identifier' in request.GET,
            'date_range': 'created_after' in request.GET or 'created_before' in request.GET,
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
        samples_identified = strain.samples.filter(is_identified=True).count()
        samples_with_genome = strain.samples.filter(has_genome=True).count()
        samples_with_biochemistry = strain.samples.filter(has_biochemistry=True).count()
        
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
                'identified_count': samples_identified,
                'with_genome_count': samples_with_genome,
                'with_biochemistry_count': samples_with_biochemistry,
                'photo_percentage': round((samples_with_photo / samples_count * 100) if samples_count > 0 else 0, 1),
                'identified_percentage': round((samples_identified / samples_count * 100) if samples_count > 0 else 0, 1),
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
        
        # Создание штамма
        with transaction.atomic():
            strain = Strain.objects.create(
                short_code=validated_data.short_code,
                rrna_taxonomy=validated_data.rrna_taxonomy,
                identifier=validated_data.identifier,
                name_alt=validated_data.name_alt,
                rcam_collection_id=validated_data.rcam_collection_id
            )
            
            logger.info(f"Created new strain: {strain.short_code} (ID: {strain.id})")
        
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
            src.organism_name ILIKE %s OR
            src.source_type ILIKE %s OR
            src.category ILIKE %s OR
            loc.name ILIKE %s OR
            storage.box_id ILIKE %s OR
            storage.cell_id ILIKE %s OR
            idx.letter_value ILIKE %s
        )"""
        where_conditions.append(search_condition)
        search_param = f"%{search_query}%"
        sql_params.extend([search_param] * 13)
    
    # Дополнительные фильтры
    if 'strain_id' in request.GET:
        where_conditions.append("sam.strain_id = %s")
        sql_params.append(int(request.GET['strain_id']))
        
    if 'has_photo' in request.GET:
        where_conditions.append("sam.has_photo = %s")
        sql_params.append(request.GET['has_photo'].lower() == 'true')
        
    if 'is_identified' in request.GET:
        where_conditions.append("sam.is_identified = %s")
        sql_params.append(request.GET['is_identified'].lower() == 'true')
        
    if 'has_antibiotic_activity' in request.GET:
        where_conditions.append("sam.has_antibiotic_activity = %s")
        sql_params.append(request.GET['has_antibiotic_activity'].lower() == 'true')
        
    if 'has_genome' in request.GET:
        where_conditions.append("sam.has_genome = %s")
        sql_params.append(request.GET['has_genome'].lower() == 'true')
        
    if 'has_biochemistry' in request.GET:
        where_conditions.append("sam.has_biochemistry = %s")
        sql_params.append(request.GET['has_biochemistry'].lower() == 'true')
        
    if 'seq_status' in request.GET:
        where_conditions.append("sam.seq_status = %s")
        sql_params.append(request.GET['seq_status'].lower() == 'true')
        
    if 'box_id' in request.GET:
        where_conditions.append("storage.box_id = %s")
        sql_params.append(request.GET['box_id'])
        
    if 'source_id' in request.GET:
        where_conditions.append("sam.source_id = %s")
        sql_params.append(int(request.GET['source_id']))
        
    if 'location_id' in request.GET:
        where_conditions.append("sam.location_id = %s")
        sql_params.append(int(request.GET['location_id']))
        
    if 'source_type' in request.GET:
        where_conditions.append("src.source_type ILIKE %s")
        sql_params.append(f"%{request.GET['source_type']}%")
        
    if 'organism_name' in request.GET:
        where_conditions.append("src.organism_name ILIKE %s")
        sql_params.append(f"%{request.GET['organism_name']}%")
    
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
        FROM collection_manager_sample sam
        LEFT JOIN collection_manager_strain st ON sam.strain_id = st.id
        LEFT JOIN collection_manager_storage storage ON sam.storage_id = storage.id
        LEFT JOIN collection_manager_source src ON sam.source_id = src.id
        LEFT JOIN collection_manager_location loc ON sam.location_id = loc.id
        LEFT JOIN collection_manager_indexletter idx ON sam.index_letter_id = idx.id
        {where_clause}
    """
    
    # SQL для получения данных с пагинацией и всеми связанными данными
    data_sql = f"""
        SELECT 
            sam.id,
            sam.original_sample_number,
            sam.has_photo,
            sam.is_identified,
            sam.has_antibiotic_activity,
            sam.has_genome,
            sam.has_biochemistry,
            sam.seq_status,
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
            src.organism_name as source_organism_name,
            src.source_type as source_source_type,
            src.category as source_category,
            -- Location data
            loc.id as location_id,
            loc.name as location_name,
            -- Index letter data
            idx.id as index_letter_id,
            idx.letter_value as index_letter_value
        FROM collection_manager_sample sam
        LEFT JOIN collection_manager_strain st ON sam.strain_id = st.id
        LEFT JOIN collection_manager_storage storage ON sam.storage_id = storage.id
        LEFT JOIN collection_manager_source src ON sam.source_id = src.id
        LEFT JOIN collection_manager_location loc ON sam.location_id = loc.id
        LEFT JOIN collection_manager_indexletter idx ON sam.index_letter_id = idx.id
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
                'organism_name': sample['source_organism_name'],
                'source_type': sample['source_source_type'],
                'category': sample['source_category'],
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
            'is_identified': sample['is_identified'],
            'has_antibiotic_activity': sample['has_antibiotic_activity'],
            'has_genome': sample['has_genome'],
            'has_biochemistry': sample['has_biochemistry'],
            'seq_status': sample['seq_status'],
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
            'is_identified': 'is_identified' in request.GET,
            'has_antibiotic_activity': 'has_antibiotic_activity' in request.GET,
            'has_genome': 'has_genome' in request.GET,
            'has_biochemistry': 'has_biochemistry' in request.GET,
            'seq_status': 'seq_status' in request.GET,
            'box_id': 'box_id' in request.GET,
            'source_id': 'source_id' in request.GET,
            'location_id': 'location_id' in request.GET,
            'date_range': 'created_after' in request.GET or 'created_before' in request.GET,
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
def list_storage(request):
    """Информация о хранилищах с заполненностью"""
    storage_data = {}
    
    for storage in Storage.objects.all():
        box_id = storage.box_id
        if box_id not in storage_data:
            storage_data[box_id] = {
                'box_id': box_id,
                'cells': [],
                'occupied': 0,
                'total': 0
            }
        
        # Получаем сначала «нормальный» образец (не помеченный как свободная ячейка)
        sample = (
            storage.sample_set.select_related('strain', 'comment')
            .exclude(comment_id=2)
            .first()
        )
        # Если таких нет — берём первый образец с пометкой «свободная ячейка»
        free_sample = None
        if sample is None:
            free_sample = (
                storage.sample_set.select_related('comment')
                .filter(comment_id=2)
                .first()
            )
        
        # Логика занятости:
        # 1) есть «нормальный» образец с привязанным штаммом → занято
        # 2) иначе — свободно (либо нет образцов, либо помечено как свободная ячейка)
        is_occupied = sample is not None and sample.strain is not None
        actual_sample = sample or free_sample  # то, что вернём в ответе
        
        cell_info = {
            'cell_id': storage.cell_id,
            'storage_id': storage.id,
            'occupied': is_occupied,
            'sample_id': actual_sample.id if actual_sample else None,
            'strain_code': actual_sample.strain.short_code if actual_sample and actual_sample.strain else None,
            'is_free_cell': free_sample is not None
        }
        
        storage_data[box_id]['cells'].append(cell_info)
        storage_data[box_id]['total'] += 1
        if is_occupied:
            storage_data[box_id]['occupied'] += 1
    
    # Преобразуем в список боксов
    boxes = list(storage_data.values())
    
    # Сортируем ячейки для каждого бокса
    for box in boxes:
        box['cells'].sort(key=lambda x: x['cell_id'])
    
    # Сортируем боксы
    boxes.sort(key=lambda x: x['box_id'])
    
    # Вычисляем общую статистику
    total_boxes = len(boxes)
    total_cells = sum(box['total'] for box in boxes)
    occupied_cells = sum(box['occupied'] for box in boxes)
    
    return Response({
        'boxes': boxes,
        'total_boxes': total_boxes,
        'total_cells': total_cells,
        'occupied_cells': occupied_cells
    })


@api_view(['GET'])
def api_stats(request):
    """Общая статистика с информацией о валидации"""
    return Response({
        'counts': {
            'strains': Strain.objects.count(),
            'samples': Sample.objects.count(),
            'storage_units': Storage.objects.count(),
            'sources': Source.objects.count(),
            'locations': Location.objects.count(),
            'index_letters': IndexLetter.objects.count(),
            'comments': Comment.objects.count(),
            'appendix_notes': AppendixNote.objects.count(),
        },
        'samples_analysis': {
            'with_photo': Sample.objects.filter(has_photo=True).count(),
            'identified': Sample.objects.filter(is_identified=True).count(),
            'with_antibiotic_activity': Sample.objects.filter(has_antibiotic_activity=True).count(),
            'with_genome': Sample.objects.filter(has_genome=True).count(),
            'with_biochemistry': Sample.objects.filter(has_biochemistry=True).count(),
            'sequenced': Sample.objects.filter(seq_status=True).count(),
        },
        'validation': {
            'engine': 'Pydantic 2.x',
            'schemas_available': [
                'StrainSchema', 'SampleSchema', 'StorageSchema',
                'SourceSchema', 'LocationSchema', 'IndexLetterSchema',
                'CommentSchema', 'AppendixNoteSchema'
            ]
        }
    })


@api_view(['POST'])
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
            appendix_note_id: Optional[int] = Field(None, ge=1, description="ID примечания")
            comment_id: Optional[int] = Field(None, ge=1, description="ID комментария")
            has_photo: bool = Field(default=False, description="Есть ли фото")
            is_identified: bool = Field(default=False, description="Идентифицирован ли")
            has_antibiotic_activity: bool = Field(default=False, description="Есть ли антибиотическая активность")
            has_genome: bool = Field(default=False, description="Есть ли геном")
            has_biochemistry: bool = Field(default=False, description="Есть ли биохимия")
            seq_status: bool = Field(default=False, description="Статус секвенирования")
            
            @field_validator('original_sample_number')
            @classmethod
            def validate_sample_number(cls, v: Optional[str]) -> Optional[str]:
                if v is not None:
                    v = v.strip()
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
            ).exclude(comment_id=2).first()  # Исключаем помеченные как свободные
            
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
        
        if validated_data.appendix_note_id:
            if not AppendixNote.objects.filter(id=validated_data.appendix_note_id).exists():
                return Response({
                    'error': f'Примечание с ID {validated_data.appendix_note_id} не найдено'
                }, status=status.HTTP_404_NOT_FOUND)
        
        if validated_data.comment_id:
            if not Comment.objects.filter(id=validated_data.comment_id).exists():
                return Response({
                    'error': f'Комментарий с ID {validated_data.comment_id} не найден'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Создание образца в транзакции
        with transaction.atomic():
            sample = Sample.objects.create(
                strain_id=validated_data.strain_id,
                index_letter_id=validated_data.index_letter_id,
                storage_id=validated_data.storage_id,
                original_sample_number=validated_data.original_sample_number,
                source_id=validated_data.source_id,
                location_id=validated_data.location_id,
                appendix_note_id=validated_data.appendix_note_id,
                comment_id=validated_data.comment_id,
                has_photo=validated_data.has_photo,
                is_identified=validated_data.is_identified,
                has_antibiotic_activity=validated_data.has_antibiotic_activity,
                has_genome=validated_data.has_genome,
                has_biochemistry=validated_data.has_biochemistry,
                seq_status=validated_data.seq_status,
            )
            
            logger.info(f"Created sample {sample.id} for strain {validated_data.strain_id}")
            
            return Response({
                'id': sample.id,
                'message': f'Образец {sample.id} успешно создан',
                'sample': {
                    'id': sample.id,
                    'strain_id': sample.strain_id,
                    'storage_id': sample.storage_id,
                    'original_sample_number': sample.original_sample_number,
                    'has_photo': sample.has_photo,
                    'is_identified': sample.is_identified,
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
            'error': f'Ошибка при создании образца: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_sample(request, sample_id):
    """Получение детальной информации об образце"""
    try:
        sample = Sample.objects.select_related(
            'strain', 'storage', 'source', 'location', 'index_letter', 'appendix_note', 'comment'
        ).get(id=sample_id)
        
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
                'organism_name': sample.source.organism_name if sample.source else None,
                'source_type': sample.source.source_type if sample.source else None,
                'category': sample.source.category if sample.source else None,
            } if sample.source else None,
            'location': {
                'id': sample.location.id if sample.location else None,
                'name': sample.location.name if sample.location else None,
            } if sample.location else None,
            'index_letter': {
                'id': sample.index_letter.id if sample.index_letter else None,
                'letter_value': sample.index_letter.letter_value if sample.index_letter else None,
            } if sample.index_letter else None,
            'appendix_note': {
                'id': sample.appendix_note.id if sample.appendix_note else None,
                'text': sample.appendix_note.text if sample.appendix_note else None,
            } if sample.appendix_note else None,
            'comment': {
                'id': sample.comment.id if sample.comment else None,
                'text': sample.comment.text if sample.comment else None,
            } if sample.comment else None,
            'original_sample_number': sample.original_sample_number,
            'has_photo': sample.has_photo,
            'is_identified': sample.is_identified,
            'has_antibiotic_activity': sample.has_antibiotic_activity,
            'has_genome': sample.has_genome,
            'has_biochemistry': sample.has_biochemistry,
            'seq_status': sample.seq_status,
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
def update_sample(request, sample_id):
    """Обновление данных образца"""
    try:
        sample = Sample.objects.get(id=sample_id)
    except Sample.DoesNotExist:
        return Response({
            'error': f'Образец с ID {sample_id} не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        # Динамически создаем схему валидации для обновления
        class UpdateSampleSchema(BaseModel):
            strain_id: Optional[int] = Field(None, ge=1, description="ID штамма")
            index_letter_id: Optional[int] = Field(None, ge=1, description="ID индексной буквы")
            storage_id: Optional[int] = Field(None, ge=1, description="ID хранилища")
            original_sample_number: Optional[str] = Field(None, max_length=100, description="Оригинальный номер образца")
            source_id: Optional[int] = Field(None, ge=1, description="ID источника")
            location_id: Optional[int] = Field(None, ge=1, description="ID местоположения")
            appendix_note_id: Optional[int] = Field(None, ge=1, description="ID примечания")
            comment_id: Optional[int] = Field(None, ge=1, description="ID комментария")
            has_photo: Optional[bool] = Field(None, description="Есть ли фото")
            is_identified: Optional[bool] = Field(None, description="Идентифицирован ли")
            has_antibiotic_activity: Optional[bool] = Field(None, description="Есть ли антибиотическая активность")
            has_genome: Optional[bool] = Field(None, description="Есть ли геном")
            has_biochemistry: Optional[bool] = Field(None, description="Есть ли биохимия")
            seq_status: Optional[bool] = Field(None, description="Статус секвенирования")
            
            @field_validator('original_sample_number')
            @classmethod
            def validate_sample_number(cls, v: Optional[str]) -> Optional[str]:
                if v is not None:
                    v = v.strip()
                    return v if v else None
                return v

        validated_data = UpdateSampleSchema.model_validate(request.data)
        
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
            ).exclude(id=sample_id).exclude(comment_id=2).first()  # Исключаем текущий образец и помеченные как свободные
            
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
        
        if validated_data.appendix_note_id is not None and not AppendixNote.objects.filter(id=validated_data.appendix_note_id).exists():
            return Response({
                'error': f'Примечание с ID {validated_data.appendix_note_id} не найдено'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if validated_data.comment_id is not None and not Comment.objects.filter(id=validated_data.comment_id).exists():
            return Response({
                'error': f'Комментарий с ID {validated_data.comment_id} не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Обновление данных в транзакции
        with transaction.atomic():
            # Обновляем только переданные поля
            update_fields = []
            for field, value in validated_data.model_dump(exclude_unset=True).items():
                setattr(sample, field, value)
                update_fields.append(field)
            
            if update_fields:
                sample.save(update_fields=update_fields)
                logger.info(f"Updated sample {sample.id}, fields: {update_fields}")
            
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


@api_view(['GET'])
def get_reference_data(request):
    """Получение справочных данных для форм"""
    try:
        # Получаем только активные/используемые данные
        strains = Strain.objects.all().order_by('short_code')[:100]
        sources = Source.objects.all().order_by('organism_name')[:100]
        locations = Location.objects.all().order_by('name')[:100]
        index_letters = IndexLetter.objects.all().order_by('letter_value')
        comments = Comment.objects.all().order_by('id')[:50]
        appendix_notes = AppendixNote.objects.all().order_by('id')[:50]
        
        # Получаем свободные ячейки хранения
        occupied_storage_ids = Sample.objects.exclude(
            comment_id=2  # Исключаем помеченные как свободные
        ).values_list('storage_id', flat=True)
        
        free_storage = Storage.objects.exclude(
            id__in=occupied_storage_ids
        ).order_by('box_id', 'cell_id')[:200]
        
        return Response({
            'strains': [
                {
                    'id': strain.id,
                    'short_code': strain.short_code,
                    'identifier': strain.identifier,
                    'display_name': f"{strain.short_code} - {strain.identifier}"
                }
                for strain in strains
            ],
            'sources': [
                {
                    'id': source.id,
                    'organism_name': source.organism_name,
                    'source_type': source.source_type,
                    'category': source.category,
                    'display_name': f"{source.organism_name} ({source.source_type})"
                }
                for source in sources
            ],
            'locations': [
                {
                    'id': location.id,
                    'name': location.name
                }
                for location in locations
            ],
            'index_letters': [
                {
                    'id': letter.id,
                    'letter_value': letter.letter_value
                }
                for letter in index_letters
            ],
            'free_storage': [
                {
                    'id': storage.id,
                    'box_id': storage.box_id,
                    'cell_id': storage.cell_id,
                    'display_name': f"Бокс {storage.box_id}, ячейка {storage.cell_id}"
                }
                for storage in free_storage
            ],
            'comments': [
                {
                    'id': comment.id,
                    'text': comment.text[:100] + ('...' if len(comment.text) > 100 else '')
                }
                for comment in comments
            ],
            'appendix_notes': [
                {
                    'id': note.id,
                    'text': note.text[:100] + ('...' if len(note.text) > 100 else '')
                }
                for note in appendix_notes
            ]
        })
    
    except Exception as e:
        logger.error(f"Unexpected error in get_reference_data: {e}")
        return Response({
            'error': f'Ошибка при получении справочных данных: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def bulk_delete_samples(request):
    """Массовое удаление образцов"""
    try:
        sample_ids = request.data.get('sample_ids', [])
        
        if not sample_ids:
            return Response({
                'error': 'Не указаны ID образцов для удаления'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(sample_ids, list):
            return Response({
                'error': 'sample_ids должен быть списком'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем существование образцов
        existing_samples = Sample.objects.filter(id__in=sample_ids)
        existing_ids = list(existing_samples.values_list('id', flat=True))
        missing_ids = set(sample_ids) - set(existing_ids)
        
        if missing_ids:
            return Response({
                'error': f'Образцы с ID {list(missing_ids)} не найдены'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Собираем информацию об удаляемых образцах для логирования
        samples_info = []
        batch_id = generate_batch_id()
        
        for sample in existing_samples:
            info = f"ID {sample.id}"
            if sample.strain:
                info += f" (штамм {sample.strain.short_code})"
            if sample.storage:
                info += f" в ячейке {sample.storage.box_id}-{sample.storage.cell_id}"
            samples_info.append(info)
            
            # Логируем каждый удаляемый образец
            old_values = model_to_dict(sample)
            log_change(
                request=request,
                content_type='sample',
                object_id=sample.id,
                action='BULK_DELETE',
                old_values=old_values,
                comment=f"Массовое удаление {len(sample_ids)} образцов",
                batch_id=batch_id
            )
        
        # Выполняем массовое удаление
        with transaction.atomic():
            deleted_count = existing_samples.delete()[0]
            logger.info(f"Bulk deleted {deleted_count} samples: {sample_ids} (batch: {batch_id})")
        
        return Response({
            'message': f'Успешно удалено {deleted_count} образцов',
            'deleted_count': deleted_count,
            'deleted_samples': samples_info
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in bulk_delete_samples: {e}")
        return Response({
            'error': f'Ошибка при массовом удалении: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def bulk_update_samples(request):
    """Массовое обновление образцов"""
    try:
        sample_ids = request.data.get('sample_ids', [])
        update_data = request.data.get('update_data', {})
        
        if not sample_ids:
            return Response({
                'error': 'Не указаны ID образцов для обновления'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not update_data:
            return Response({
                'error': 'Не указаны данные для обновления'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем существование образцов
        existing_samples = Sample.objects.filter(id__in=sample_ids)
        existing_ids = list(existing_samples.values_list('id', flat=True))
        missing_ids = set(sample_ids) - set(existing_ids)
        
        if missing_ids:
            return Response({
                'error': f'Образцы с ID {list(missing_ids)} не найдены'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Фильтруем только разрешенные поля для обновления
        allowed_fields = {
            'has_photo', 'is_identified', 'has_antibiotic_activity',
            'has_genome', 'has_biochemistry', 'seq_status'
        }
        
        filtered_update_data = {
            key: value for key, value in update_data.items() 
            if key in allowed_fields
        }
        
        if not filtered_update_data:
            return Response({
                'error': 'Нет допустимых полей для обновления'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Выполняем массовое обновление с логированием
        batch_id = generate_batch_id()
        
        with transaction.atomic():
            # Логируем каждый обновляемый образец до изменения
            for sample in existing_samples:
                old_values = model_to_dict(sample)
                
                # Применяем изменения к объекту для получения новых значений
                for field, value in filtered_update_data.items():
                    setattr(sample, field, value)
                
                new_values = model_to_dict(sample)
                
                log_change(
                    request=request,
                    content_type='sample',
                    object_id=sample.id,
                    action='BULK_UPDATE',
                    old_values=old_values,
                    new_values=new_values,
                    comment=f"Массовое обновление {len(sample_ids)} образцов: {list(filtered_update_data.keys())}",
                    batch_id=batch_id
                )
            
            # Выполняем массовое обновление
            updated_count = existing_samples.update(**filtered_update_data)
            logger.info(f"Bulk updated {updated_count} samples with data: {filtered_update_data} (batch: {batch_id})")
        
        return Response({
            'message': f'Успешно обновлено {updated_count} образцов',
            'updated_count': updated_count,
            'updated_fields': list(filtered_update_data.keys()),
            'updated_data': filtered_update_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in bulk_update_samples: {e}")
        return Response({
            'error': f'Ошибка при массовом обновлении: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def bulk_delete_strains(request):
    """Массовое удаление штаммов"""
    try:
        strain_ids = request.data.get('strain_ids', [])
        force_delete = request.data.get('force_delete', False)
        
        if not strain_ids:
            return Response({
                'error': 'Не указаны ID штаммов для удаления'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем существование штаммов
        existing_strains = Strain.objects.filter(id__in=strain_ids)
        existing_ids = list(existing_strains.values_list('id', flat=True))
        missing_ids = set(strain_ids) - set(existing_ids)
        
        if missing_ids:
            return Response({
                'error': f'Штаммы с ID {list(missing_ids)} не найдены'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем связанные образцы
        strains_with_samples = []
        for strain in existing_strains:
            sample_count = Sample.objects.filter(strain_id=strain.id).count()
            if sample_count > 0:
                strains_with_samples.append({
                    'id': strain.id,
                    'short_code': strain.short_code,
                    'sample_count': sample_count
                })
        
        if strains_with_samples and not force_delete:
            return Response({
                'error': 'Некоторые штаммы имеют связанные образцы',
                'strains_with_samples': strains_with_samples,
                'message': 'Используйте force_delete=true для принудительного удаления'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Собираем информацию об удаляемых штаммах
        strains_info = []
        for strain in existing_strains:
            strains_info.append({
                'id': strain.id,
                'short_code': strain.short_code,
                'identifier': strain.identifier
            })
        
        # Выполняем массовое удаление
        with transaction.atomic():
            if force_delete:
                # Удаляем связанные образцы
                for strain in existing_strains:
                    Sample.objects.filter(strain_id=strain.id).delete()
            
            deleted_count = existing_strains.delete()[0]
            logger.info(f"Bulk deleted {deleted_count} strains: {strain_ids}")
        
        return Response({
            'message': f'Успешно удалено {deleted_count} штаммов',
            'deleted_count': deleted_count,
            'deleted_strains': strains_info,
            'force_delete': force_delete
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in bulk_delete_strains: {e}")
        return Response({
            'error': f'Ошибка при массовом удалении штаммов: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def bulk_update_strains(request):
    """Массовое обновление штаммов"""
    try:
        strain_ids = request.data.get('strain_ids', [])
        update_data = request.data.get('update_data', {})
        
        if not strain_ids:
            return Response({
                'error': 'Не указаны ID штаммов для обновления'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not update_data:
            return Response({
                'error': 'Не указаны данные для обновления'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем существование штаммов
        existing_strains = Strain.objects.filter(id__in=strain_ids)
        existing_ids = list(existing_strains.values_list('id', flat=True))
        missing_ids = set(strain_ids) - set(existing_ids)
        
        if missing_ids:
            return Response({
                'error': f'Штаммы с ID {list(missing_ids)} не найдены'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Фильтруем только разрешенные поля для обновления штаммов
        allowed_fields = {
            'short_code', 'rrna_taxonomy', 'identifier', 'name_alt', 'rcam_collection_id'
        }
        
        filtered_update_data = {
            key: value for key, value in update_data.items() 
            if key in allowed_fields and value is not None
        }
        
        if not filtered_update_data:
            return Response({
                'error': 'Нет допустимых полей для обновления'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Выполняем массовое обновление с логированием
        batch_id = generate_batch_id()
        
        with transaction.atomic():
            # Логируем каждый обновляемый штамм до изменения
            for strain in existing_strains:
                old_values = model_to_dict(strain)
                
                # Применяем изменения к объекту для получения новых значений
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
                    comment=f"Массовое обновление {len(strain_ids)} штаммов: {list(filtered_update_data.keys())}",
                    batch_id=batch_id
                )
            
            # Выполняем массовое обновление
            updated_count = existing_strains.update(**filtered_update_data)
            logger.info(f"Bulk updated {updated_count} strains with data: {filtered_update_data} (batch: {batch_id})")
        
        return Response({
            'message': f'Успешно обновлено {updated_count} штаммов',
            'updated_count': updated_count,
            'updated_fields': list(filtered_update_data.keys()),
            'updated_data': filtered_update_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in bulk_update_strains: {e}")
        return Response({
            'error': f'Ошибка при массовом обновлении штаммов: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
def bulk_export_samples(request):
    """Экспорт образцов в CSV/JSON/Excel"""
    try:
        import csv, json
        from io import StringIO, BytesIO

        # Читаем параметры (GET или POST)
        if request.method == 'POST':
            sample_ids = request.data.get('sample_ids', '')
            format_type = request.data.get('format', 'csv').lower()
            fields = request.data.get('fields', '').split(',') if request.data.get('fields') else []
            include_related = request.data.get('include_related', 'true').lower() == 'true'
        else:
            sample_ids = request.GET.get('sample_ids', '')
            format_type = request.GET.get('format', 'csv').lower()
            fields = request.GET.get('fields', '').split(',') if request.GET.get('fields') else []
            include_related = request.GET.get('include_related', 'true').lower() == 'true'

        # Получаем выборку
        if sample_ids:
            sample_ids = [int(x) for x in sample_ids.split(',') if x.isdigit()]
            samples = Sample.objects.filter(id__in=sample_ids)
        else:
            samples = Sample.objects.all()
            
            # Добавляем простую текстовую фильтрацию (поиск)
            search_query = request.data.get('search', '').strip() if request.method == 'POST' else request.GET.get('search', '').strip()
            if search_query:
                from django.db.models import Q
                q = Q(original_sample_number__icontains=search_query) | Q(strain__short_code__icontains=search_query) | Q(strain__identifier__icontains=search_query)
                samples = samples.filter(q)

        if include_related:
            samples = samples.select_related('strain', 'storage', 'source', 'location')

        # Доступные поля
        available_fields = {
            'id': 'ID',
            'strain_short_code': 'Код штамма',
            'strain_identifier': 'Идентификатор штамма',
            'original_sample_number': 'Номер образца',
            'has_photo': 'Есть фото',
            'is_identified': 'Идентифицирован',
            'has_antibiotic_activity': 'АБ активность',
            'has_genome': 'Есть геном',
            'has_biochemistry': 'Есть биохимия',
            'seq_status': 'Секвенирован',
            'source_organism': 'Организм источника',
            'source_type': 'Тип источника',
            'location_name': 'Локация',
            'storage_cell': 'Ячейка хранения',
            'created_at': 'Дата создания',
            'updated_at': 'Дата обновления',
        }

        if not fields or not any(f.strip() for f in fields):
            export_fields = list(available_fields.keys())
        else:
            export_fields = [f.strip() for f in fields if f.strip() in available_fields]

        # Собираем данные
        data = []
        for s in samples:
            row = {}
            for f in export_fields:
                if f == 'id':
                    row[available_fields[f]] = s.id
                elif f == 'strain_short_code':
                    row[available_fields[f]] = s.strain.short_code if s.strain else ''
                elif f == 'strain_identifier':
                    row[available_fields[f]] = s.strain.identifier if s.strain else ''
                elif f == 'original_sample_number':
                    row[available_fields[f]] = s.original_sample_number or ''
                elif f == 'has_photo':
                    row[available_fields[f]] = 'Да' if s.has_photo else 'Нет'
                elif f == 'is_identified':
                    row[available_fields[f]] = 'Да' if s.is_identified else 'Нет'
                elif f == 'has_antibiotic_activity':
                    row[available_fields[f]] = 'Да' if s.has_antibiotic_activity else 'Нет'
                elif f == 'has_genome':
                    row[available_fields[f]] = 'Да' if s.has_genome else 'Нет'
                elif f == 'has_biochemistry':
                    row[available_fields[f]] = 'Да' if s.has_biochemistry else 'Нет'
                elif f == 'seq_status':
                    row[available_fields[f]] = 'Да' if s.seq_status else 'Нет'
                elif f == 'source_organism':
                    row[available_fields[f]] = s.source.organism_name if s.source else ''
                elif f == 'source_type':
                    row[available_fields[f]] = s.source.source_type if s.source else ''
                elif f == 'location_name':
                    row[available_fields[f]] = s.location.name if s.location else ''
                elif f == 'storage_cell':
                    row[available_fields[f]] = f"{s.storage.box_id}:{s.storage.cell_id}" if s.storage else ''
                elif f == 'created_at':
                    row[available_fields[f]] = s.created_at.strftime('%Y-%m-%d %H:%M:%S') if s.created_at else ''
                elif f == 'updated_at':
                    row[available_fields[f]] = s.updated_at.strftime('%Y-%m-%d %H:%M:%S') if s.updated_at else ''
            data.append(row)

        # Возврат в нужном формате
        from django.http import HttpResponse
        if format_type == 'json':
            return HttpResponse(json.dumps(data, ensure_ascii=False, indent=2), content_type='application/json; charset=utf-8')
        elif format_type == 'excel' or format_type == 'xlsx':
            try:
                import openpyxl
                from openpyxl import Workbook

                wb = Workbook()
                ws = wb.active
                if data:
                    ws.append(list(data[0].keys()))
                    for row in data:
                        ws.append(list(row.values()))
                output = BytesIO()
                wb.save(output)
                output.seek(0)
                response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename="samples_export.xlsx"'
                return response
            except ImportError:
                return Response({'error':'Excel экспорт недоступен'}, status=500)
        else:
            # CSV
            output = StringIO()
            writer = csv.writer(output)
            if data:
                writer.writerow(list(data[0].keys()))
                for row in data:
                    writer.writerow(list(row.values()))
            response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="samples_export.csv"'
            return response

    except Exception as e:
        logger.error(f"Error in bulk_export_samples: {e}")
        return Response({
            'error': f'Ошибка при экспорте: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
def bulk_export_strains(request):
    """Экспорт штаммов в CSV/JSON/Excel"""
    try:
        import csv
        import json
        from io import StringIO, BytesIO
        
        # Получаем параметры (поддерживаем GET и POST)
        if request.method == 'POST':
            strain_ids = request.data.get('strain_ids', '')
            format_type = request.data.get('format', 'csv').lower()
            fields = request.data.get('fields', '').split(',') if request.data.get('fields') else []
            include_related = request.data.get('include_related', 'true').lower() == 'true'
        else:
            strain_ids = request.GET.get('strain_ids', '')
            format_type = request.GET.get('format', 'csv').lower()
            fields = request.GET.get('fields', '').split(',') if request.GET.get('fields') else []
            include_related = request.GET.get('include_related', 'true').lower() == 'true'
        
        # Получаем штаммы
        if strain_ids:
            strain_ids = [int(x) for x in strain_ids.split(',') if x.isdigit()]
            strains = Strain.objects.filter(id__in=strain_ids)
        else:
            # Применяем те же фильтры, что и в list_strains
            strains = Strain.objects.all()
            
            # Фильтрация (копируем логику из list_strains)
            if request.method == 'POST':
                search_query = request.data.get('search', '').strip()
            else:
                search_query = request.GET.get('search', '').strip()
            
            if search_query:
                from django.db.models import Q
                search_q = Q()
                search_q |= Q(short_code__icontains=search_query)
                search_q |= Q(identifier__icontains=search_query)
                search_q |= Q(rrna_taxonomy__icontains=search_query)
                search_q |= Q(name_alt__icontains=search_query)
                search_q |= Q(rcam_collection_id__icontains=search_query)
                strains = strains.filter(search_q)
        
        strains = strains.order_by('id')
        
        # Определяем поля для экспорта
        available_fields = {
            'id': 'ID',
            'short_code': 'Короткий код',
            'identifier': 'Идентификатор',
            'rrna_taxonomy': 'rRNA таксономия',
            'name_alt': 'Альтернативное название',
            'rcam_collection_id': 'RCAM ID',
            'created_at': 'Дата создания',
            'updated_at': 'Дата обновления'
        }
        
        # Если поля не указаны, экспортируем все
        if not fields or not any(f.strip() for f in fields):
            export_fields = list(available_fields.keys())
        else:
            export_fields = [f.strip() for f in fields if f.strip() in available_fields]
        
        if not export_fields:
            return Response({
                'error': 'Не указаны корректные поля для экспорта'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Подготавливаем данные
        data = []
        for strain in strains:
            row = {}
            for field in export_fields:
                if field == 'id':
                    row[available_fields[field]] = strain.id
                elif field == 'short_code':
                    row[available_fields[field]] = strain.short_code or ''
                elif field == 'identifier':
                    row[available_fields[field]] = strain.identifier or ''
                elif field == 'rrna_taxonomy':
                    row[available_fields[field]] = strain.rrna_taxonomy or ''
                elif field == 'name_alt':
                    row[available_fields[field]] = strain.name_alt or ''
                elif field == 'rcam_collection_id':
                    row[available_fields[field]] = strain.rcam_collection_id or ''
                elif field == 'created_at':
                    row[available_fields[field]] = strain.created_at.strftime('%Y-%m-%d %H:%M:%S') if strain.created_at else ''
                elif field == 'updated_at':
                    row[available_fields[field]] = strain.updated_at.strftime('%Y-%m-%d %H:%M:%S') if strain.updated_at else ''
            data.append(row)
        
        # Экспорт в зависимости от формата
        if format_type == 'json':
            from django.http import HttpResponse
            response = HttpResponse(
                json.dumps(data, ensure_ascii=False, indent=2),
                content_type='application/json; charset=utf-8'
            )
            response['Content-Disposition'] = 'attachment; filename="strains_export.json"'
            return response
            
        elif format_type == 'excel':
            try:
                import openpyxl
                from openpyxl import Workbook
                
                wb = Workbook()
                ws = wb.active
                ws.title = "Штаммы"
                
                # Заголовки
                if data:
                    headers = list(data[0].keys())
                    for col, header in enumerate(headers, 1):
                        ws.cell(row=1, column=col, value=header)
                    
                    # Данные
                    for row_idx, row_data in enumerate(data, 2):
                        for col_idx, value in enumerate(row_data.values(), 1):
                            ws.cell(row=row_idx, column=col_idx, value=value)
                
                # Сохраняем в BytesIO
                output = BytesIO()
                wb.save(output)
                output.seek(0)
                
                from django.http import HttpResponse
                response = HttpResponse(
                    output.getvalue(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename="strains_export.xlsx"'
                return response
                
            except ImportError:
                return Response({
                    'error': 'Excel экспорт недоступен. Установите openpyxl.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        else:  # CSV по умолчанию
            output = StringIO()
            writer = csv.writer(output)

            # Заголовки и данные
            if data:
                headers = list(data[0].keys())
                writer.writerow(headers)
                for row_data in data:
                    writer.writerow(list(row_data.values()))

            from django.http import HttpResponse
            response = HttpResponse(
                output.getvalue(),
                content_type='text/csv; charset=utf-8'
            )
            response['Content-Disposition'] = 'attachment; filename="strains_export.csv"'
            return response
        
    except Exception as e:
        logger.error(f"Error in bulk_export_strains: {e}")
        return Response({
            'error': f'Ошибка при экспорте: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 


@api_view(['GET'])
def api_health(request):
    """Простой health-check endpoint для Docker"""
    return Response({'status': 'healthy'})


@api_view(['GET'])
def list_storage_summary(request):
    """Краткая информация о хранилищах без деталей ячеек (для быстрой загрузки)"""
    from django.db import connection
    
    # ИСПРАВЛЕННЫЙ SQL ЗАПРОС - правильная логика для NULL comment_id
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                s.box_id,
                COUNT(*) as total_cells,
                COUNT(CASE 
                    WHEN sam.strain_id IS NOT NULL AND (sam.comment_id IS NULL OR sam.comment_id != 2)
                    THEN 1 
                    ELSE NULL 
                END) as occupied_cells
            FROM collection_manager_storage s
            LEFT JOIN collection_manager_sample sam ON s.id = sam.storage_id
            GROUP BY s.box_id
            ORDER BY s.box_id
        """)
        
        boxes = []
        total_boxes = 0
        total_cells = 0
        occupied_cells = 0
        
        for row in cursor.fetchall():
            box_id, total, occupied = row
            boxes.append({
                'box_id': box_id,
                'occupied': occupied,
                'total': total
            })
            total_boxes += 1
            total_cells += total
            occupied_cells += occupied
    
    return Response({
        'boxes': boxes,
        'total_boxes': total_boxes,
        'total_cells': total_cells,
        'occupied_cells': occupied_cells
    })


@api_view(['GET'])
def get_box_details(request, box_id):
    """Детальная информация о ячейках конкретного бокса"""
    from django.db import connection
    
    # ИСПРАВЛЕННЫЙ SQL ЗАПРОС - правильная логика для NULL comment_id
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                s.id as storage_id,
                s.cell_id,
                sam.id as sample_id,
                st.short_code as strain_code,
                CASE 
                    WHEN sam.strain_id IS NOT NULL AND (sam.comment_id IS NULL OR sam.comment_id != 2)
                    THEN true 
                    ELSE false 
                END as occupied,
                CASE 
                    WHEN sam.comment_id = 2 
                    THEN true 
                    ELSE false 
                END as is_free_cell
            FROM collection_manager_storage s
            LEFT JOIN collection_manager_sample sam ON s.id = sam.storage_id
            LEFT JOIN collection_manager_strain st ON sam.strain_id = st.id
            WHERE s.box_id = %s
            ORDER BY s.cell_id
        """, [box_id])
        
        cells = []
        occupied_count = 0
        
        for row in cursor.fetchall():
            storage_id, cell_id, sample_id, strain_code, occupied, is_free_cell = row
            
            cell_info = {
                'cell_id': cell_id,
                'storage_id': storage_id,
                'occupied': occupied,
                'sample_id': sample_id,
                'strain_code': strain_code,
                'is_free_cell': is_free_cell
            }
            
            cells.append(cell_info)
            if occupied:
                occupied_count += 1
    
    return Response({
        'box_id': box_id,
        'cells': cells,
        'total': len(cells),
        'occupied': occupied_count
    })

