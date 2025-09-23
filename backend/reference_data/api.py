"""
API endpoints для справочных данных
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from pydantic import BaseModel, ValidationError
from typing import List, Optional

from .models import IndexLetter, Location, Source, IUKColor, AmylaseVariant, GrowthMedium


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


class SourceSchema(BaseModel):
    id: Optional[int] = None
    organism_name: str
    source_type: str
    category: str
    
    class Config:
        from_attributes = True


class IUKColorSchema(BaseModel):
    id: Optional[int] = None
    name: str
    hex_code: str
    
    class Config:
        from_attributes = True


class AmylaseVariantSchema(BaseModel):
    id: Optional[int] = None
    name: str
    
    class Config:
        from_attributes = True


class GrowthMediumSchema(BaseModel):
    id: Optional[int] = None
    name: str
    
    class Config:
        from_attributes = True


@api_view(['GET'])
def get_reference_data(request):
    """Получить все справочные данные"""
    try:
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
                for source in Source.objects.all()
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
def get_source_types(request):
    """Получить типы источников"""
    try:
        sources = Source.objects.all()
        data = [SourceSchema.model_validate(source).model_dump() for source in sources]
        return Response(data)
    except Exception as e:
        return Response(
            {'error': f'Ошибка получения типов источников: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_organism_names(request):
    """Получить названия организмов (из источников)"""
    try:
        sources = Source.objects.all()
        data = [source.organism_name for source in sources]
        return Response(data)
    except Exception as e:
        return Response(
            {'error': f'Ошибка получения названий организмов: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )