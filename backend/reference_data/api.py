"""
API endpoints для справочных данных
"""

from typing import List, Optional

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from pydantic import BaseModel, ValidationError, field_validator

from .models import (
    IndexLetter,
    Location,
    Source,
    IUKColor,
    AmylaseVariant,
    GrowthMedium,
)


class IndexLetterSchema(BaseModel):
    id: Optional[int] = None
    letter_value: str

    class Config:
        from_attributes = True


class LocationSchema(BaseModel):
    id: Optional[int] = None
    name: str

    class Config:
        from_attributes = True


class SourceTypeSchema(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class SourceCategorySchema(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class SourceSchema(BaseModel):
    id: Optional[int] = None
    name: str

    class Config:
        from_attributes = True


class IUKColorSchema(BaseModel):
    id: Optional[int] = None
    name: str
    hex_code: Optional[str] = None

    class Config:
        from_attributes = True


class AmylaseVariantSchema(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class GrowthMediumSchema(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


@api_view(['GET'])
def get_reference_data(request):
    """Получить все справочные данные"""
    try:
        sources_qs = Source.objects.all()

        data = {
            'index_letters': [
                IndexLetterSchema.model_validate(letter).model_dump()
                for letter in IndexLetter.objects.all()
            ],
            'locations': [
                LocationSchema.model_validate(location).model_dump()
                for location in Location.objects.all()
            ],
            'sources': [
                SourceSchema.model_validate(source).model_dump()
                for source in sources_qs
            ],
            'iuk_colors': [
                IUKColorSchema.model_validate(color).model_dump()
                for color in IUKColor.objects.all()
            ],
            'amylase_variants': [
                AmylaseVariantSchema.model_validate(variant).model_dump()
                for variant in AmylaseVariant.objects.all()
            ],
            'growth_media': [
                GrowthMediumSchema.model_validate(medium).model_dump()
                for medium in GrowthMedium.objects.all()
            ]
        }
        return Response(data)
    except Exception as e:
        return Response(
            {'error': f'Ошибка получения справочных данных: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )






@api_view(['GET'])
def get_organism_names(request):
    """Получить названия источников"""
    try:
        sources = Source.objects.all()
        data = [source.name for source in sources]
        return Response(data)
    except Exception as e:
        return Response(
            {'error': f'Ошибка получения названий источников: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
def growth_media_list(request):
    """Получить список сред роста или создать новую"""
    if request.method == 'GET':
        try:
            media = GrowthMedium.objects.order_by('name')
            data = [
                GrowthMediumSchema.model_validate(medium).model_dump()
                for medium in media
            ]
            return Response(data)
        except Exception as e:
            return Response(
                {'error': f'Ошибка получения сред роста: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'POST':
        try:
            schema = GrowthMediumSchema(**request.data)
            medium = GrowthMedium.objects.create(
                name=schema.name,
                description=schema.description
            )
            return Response(
                GrowthMediumSchema.model_validate(medium).model_dump(),
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {'error': f'Ошибка валидации: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Ошибка создания среды роста: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET', 'PUT', 'DELETE'])
def growth_medium_detail(request, pk):
    """Получить, обновить или удалить среду роста"""
    try:
        medium = GrowthMedium.objects.get(pk=pk)
    except GrowthMedium.DoesNotExist:
        return Response(
            {'error': 'Среда роста не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        return Response(GrowthMediumSchema.model_validate(medium).model_dump())
    
    elif request.method == 'PUT':
        try:
            schema = GrowthMediumSchema(**request.data)
            medium.name = schema.name
            medium.description = schema.description
            medium.save()
            return Response(GrowthMediumSchema.model_validate(medium).model_dump())
        except ValidationError as e:
            return Response(
                {'error': f'Ошибка валидации: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Ошибка обновления среды роста: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'DELETE':
        try:
            medium.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'error': f'Ошибка удаления среды роста: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
