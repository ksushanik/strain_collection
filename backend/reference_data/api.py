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
    SourceType,
    SourceCategory,
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
    organism_name: str
    source_type: str
    category: str

    @field_validator('source_type', mode='before')
    @classmethod
    def normalize_source_type(cls, value):
        if value is None:
            return value
        return getattr(value, 'name', value)

    @field_validator('category', mode='before')
    @classmethod
    def normalize_category(cls, value):
        if value is None:
            return value
        return getattr(value, 'name', value)

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
        sources_qs = Source.objects.select_related('source_type', 'category')

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
            'source_types': [
                SourceTypeSchema.model_validate(source_type).model_dump()
                for source_type in SourceType.objects.order_by('name')
            ],
            'source_categories': [
                SourceCategorySchema.model_validate(category).model_dump()
                for category in SourceCategory.objects.order_by('name')
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
    """Получить список типов источников"""
    try:
        source_types = SourceType.objects.order_by('name')
        data = [
            SourceTypeSchema.model_validate(source_type).model_dump()
            for source_type in source_types
        ]
        return Response(data)
    except Exception as e:
        return Response(
            {'error': f'Ошибка получения типов источников: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_source_categories(request):
    """Получить список категорий источников"""
    try:
        categories = SourceCategory.objects.order_by('name')
        data = [
            SourceCategorySchema.model_validate(category).model_dump()
            for category in categories
        ]
        return Response(data)
    except Exception as e:
        return Response(
            {'error': f'Ошибка получения категорий источников: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_organism_names(request):
    """Получить названия организмов (из источников)"""
    try:
        sources = Source.objects.select_related('source_type').all()
        data = [source.organism_name for source in sources]
        return Response(data)
    except Exception as e:
        return Response(
            {'error': f'Ошибка получения названий организмов: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
