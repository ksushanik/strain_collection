"""
API endpoints для управления штаммами
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional
import logging

from .models import Strain

logger = logging.getLogger(__name__)


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


@api_view(['GET'])
def list_strains(request):
    """Список всех штаммов с поиском и фильтрацией"""
    try:
        page = max(1, int(request.GET.get('page', 1)))
        limit = max(1, min(int(request.GET.get('limit', 50)), 1000))
        offset = (page - 1) * limit
        
        # Полнотекстовый поиск
        search_query = request.GET.get('search', '').strip()
        
        queryset = Strain.objects.all()
        
        if search_query:
            queryset = queryset.filter(
                Q(short_code__icontains=search_query) |
                Q(identifier__icontains=search_query) |
                Q(rrna_taxonomy__icontains=search_query) |
                Q(name_alt__icontains=search_query) |
                Q(rcam_collection_id__icontains=search_query)
            )
        
        total_count = queryset.count()
        strains = queryset[offset:offset + limit]
        
        data = [StrainSchema.model_validate(strain).model_dump() for strain in strains]
        
        return Response({
            'strains': data,
            'total': total_count,
            'page': page,
            'limit': limit,
            'has_next': offset + limit < total_count,
            'has_prev': page > 1
        })
        
    except Exception as e:
        logger.error(f"Error in list_strains: {e}")
        return Response(
            {'error': f'Ошибка получения списка штаммов: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_strain(request, strain_id):
    """Получение штамма по ID"""
    try:
        strain = Strain.objects.get(id=strain_id)
        data = StrainSchema.model_validate(strain).model_dump()
        return Response(data)
    except Strain.DoesNotExist:
        return Response(
            {'error': f'Штамм с ID {strain_id} не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in get_strain: {e}")
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
        with transaction.atomic():
            strain = Strain.objects.create(
                short_code=validated_data.short_code,
                rrna_taxonomy=validated_data.rrna_taxonomy,
                identifier=validated_data.identifier,
                name_alt=validated_data.name_alt,
                rcam_collection_id=validated_data.rcam_collection_id
            )
            logger.info(f"Created strain: {strain.short_code} (ID: {strain.id})")
        
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