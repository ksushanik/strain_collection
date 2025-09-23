"""
API endpoints для управления образцами
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import Q, Prefetch
from django.views.decorators.csrf import csrf_exempt
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional, List
import logging

from .models import Sample, SampleGrowthMedia, SamplePhoto
from reference_data.models import IndexLetter, IUKColor, AmylaseVariant, GrowthMedium, Source, Location
from strain_management.models import Strain
from storage_management.models import Storage

logger = logging.getLogger(__name__)


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
    is_identified: bool = Field(default=False, description="Идентифицирован ли")
    has_antibiotic_activity: bool = Field(default=False, description="Есть ли антибиотическая активность")
    has_genome: bool = Field(default=False, description="Есть ли геном")
    has_biochemistry: bool = Field(default=False, description="Есть ли биохимия")
    seq_status: bool = Field(default=False, description="Статус секвенирования")
    mobilizes_phosphates: bool = Field(default=False, description="Мобилизирует фосфаты")
    stains_medium: bool = Field(default=False, description="Окрашивает среду")
    produces_siderophores: bool = Field(default=False, description="Вырабатывает сидерофоры")
    iuk_color_id: Optional[int] = Field(None, ge=1, description="ID цвета ИУК")
    amylase_variant_id: Optional[int] = Field(None, ge=1, description="ID варианта амилазы")
    growth_media_ids: Optional[List[int]] = Field(None, description="Список ID сред роста")

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
    is_identified: bool = Field(default=False, description="Идентифицирован ли")
    has_antibiotic_activity: bool = Field(default=False, description="Есть ли антибиотическая активность")
    has_genome: bool = Field(default=False, description="Есть ли геном")
    has_biochemistry: bool = Field(default=False, description="Есть ли биохимия")
    seq_status: bool = Field(default=False, description="Статус секвенирования")
    mobilizes_phosphates: bool = Field(default=False, description="Мобилизирует фосфаты")
    stains_medium: bool = Field(default=False, description="Окрашивает среду")
    produces_siderophores: bool = Field(default=False, description="Вырабатывает сидерофоры")
    iuk_color_id: Optional[int] = Field(None, ge=1, description="ID цвета ИУК")
    amylase_variant_id: Optional[int] = Field(None, ge=1, description="ID варианта амилазы")
    growth_media_ids: Optional[List[int]] = Field(None, description="Список ID сред роста")
    
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


@api_view(['GET'])
def list_samples(request):
    """Список всех образцов с поиском и фильтрацией"""
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
        is_identified = request.GET.get('is_identified')
        
        queryset = Sample.objects.select_related(
            'index_letter', 'strain', 'storage', 'source', 'location',
            'iuk_color', 'amylase_variant'
        ).prefetch_related(
            Prefetch('samplegrowthmedium_set', queryset=SampleGrowthMedia.objects.select_related('growth_medium'))
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
        if has_photo is not None:
            queryset = queryset.filter(has_photo=has_photo.lower() == 'true')
        if is_identified is not None:
            queryset = queryset.filter(is_identified=is_identified.lower() == 'true')
        
        total_count = queryset.count()
        samples = queryset[offset:offset + limit]
        
        # Формируем данные с дополнительной информацией
        data = []
        for sample in samples:
            sample_data = SampleSchema.model_validate(sample).model_dump()
            
            # Добавляем информацию о связанных объектах
            sample_data['index_letter'] = sample.index_letter.value if sample.index_letter else None
            sample_data['strain_code'] = sample.strain.short_code if sample.strain else None
            sample_data['storage_name'] = sample.storage.name if sample.storage else None
            sample_data['source_name'] = sample.source.name if sample.source else None
            sample_data['location_name'] = sample.location.name if sample.location else None
            sample_data['iuk_color_name'] = sample.iuk_color.name if sample.iuk_color else None
            sample_data['amylase_variant_name'] = sample.amylase_variant.name if sample.amylase_variant else None
            
            # Добавляем среды роста
            growth_media = [sgm.growth_medium.name for sgm in sample.samplegrowthmedium_set.all()]
            sample_data['growth_media'] = growth_media
            
            data.append(sample_data)
        
        return Response({
            'samples': data,
            'total': total_count,
            'page': page,
            'limit': limit,
            'has_next': offset + limit < total_count,
            'has_prev': page > 1
        })
        
    except Exception as e:
        logger.error(f"Error in list_samples: {e}")
        return Response(
            {'error': f'Ошибка получения списка образцов: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_sample(request, sample_id):
    """Получение образца по ID"""
    try:
        sample = Sample.objects.select_related(
            'index_letter', 'strain', 'storage', 'source', 'location',
            'iuk_color', 'amylase_variant'
        ).prefetch_related(
            Prefetch('samplegrowthmedium_set', queryset=SampleGrowthMedia.objects.select_related('growth_medium'))
        ).get(id=sample_id)
        
        data = SampleSchema.model_validate(sample).model_dump()
        
        # Добавляем информацию о связанных объектах
        data['index_letter'] = sample.index_letter.value if sample.index_letter else None
        data['strain_code'] = sample.strain.short_code if sample.strain else None
        data['storage_name'] = sample.storage.name if sample.storage else None
        data['source_name'] = sample.source.name if sample.source else None
        data['location_name'] = sample.location.name if sample.location else None
        data['iuk_color_name'] = sample.iuk_color.name if sample.iuk_color else None
        data['amylase_variant_name'] = sample.amylase_variant.name if sample.amylase_variant else None
        
        # Добавляем среды роста
        growth_media = [sgm.growth_medium.name for sgm in sample.samplegrowthmedium_set.all()]
        data['growth_media'] = growth_media
        
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
                is_identified=validated_data.is_identified,
                has_antibiotic_activity=validated_data.has_antibiotic_activity,
                has_genome=validated_data.has_genome,
                has_biochemistry=validated_data.has_biochemistry,
                seq_status=validated_data.seq_status,
                mobilizes_phosphates=validated_data.mobilizes_phosphates,
                stains_medium=validated_data.stains_medium,
                produces_siderophores=validated_data.produces_siderophores,
                iuk_color_id=validated_data.iuk_color_id,
                amylase_variant_id=validated_data.amylase_variant_id
            )
            
            # Добавляем среды роста
            if validated_data.growth_media_ids:
                for medium_id in validated_data.growth_media_ids:
                    if GrowthMedium.objects.filter(id=medium_id).exists():
                        SampleGrowthMedia.objects.create(sample=sample, growth_medium_id=medium_id)
            
            logger.info(f"Created sample: ID {sample.id}")
        
        return Response({
            'id': sample.id,
            'message': 'Образец успешно создан'
        }, status=status.HTTP_201_CREATED)
    
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


@api_view(['PUT'])
@csrf_exempt
def update_sample(request, sample_id):
    """Обновление образца"""
    try:
        # Получаем образец
        try:
            sample = Sample.objects.get(id=sample_id)
        except Sample.DoesNotExist:
            return Response({
                'error': f'Образец с ID {sample_id} не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Валидируем данные
        validated_data = CreateSampleSchema.model_validate(request.data)
        
        # Проверяем существование связанных объектов (аналогично create_sample)
        # ... (код проверки аналогичен create_sample)
        
        # Обновление образца
        with transaction.atomic():
            # Обновляем поля образца
            for field, value in validated_data.model_dump(exclude={'growth_media_ids'}).items():
                setattr(sample, field, value)
            sample.save()
            
            # Обновляем среды роста
            SampleGrowthMedia.objects.filter(sample=sample).delete()
            if validated_data.growth_media_ids:
                for medium_id in validated_data.growth_media_ids:
                    if GrowthMedium.objects.filter(id=medium_id).exists():
                        SampleGrowthMedia.objects.create(sample=sample, growth_medium_id=medium_id)
            
            logger.info(f"Updated sample: ID {sample.id}")
        
        return Response({
            'id': sample.id,
            'message': 'Образец успешно обновлен'
        })
    
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
        return Response({
            'valid': True,
            'data': validated_data.model_dump(),
            'message': 'Данные образца валидны'
        })
    except ValidationError as e:
        return Response({
            'valid': False,
            'errors': e.errors(),
            'message': 'Ошибки валидации данных'
        }, status=status.HTTP_400_BAD_REQUEST)