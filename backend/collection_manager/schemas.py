"""
Схемы валидации данных с использованием Pydantic
"""

import re
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator
from typing_extensions import Annotated


class IndexLetterSchema(BaseModel):
    """Схема валидации для индексных букв"""

    id: int = Field(ge=1, description="ID индексной буквы")
    letter_value: str = Field(
        min_length=1, max_length=10, description="Значение индексной буквы"
    )

    @field_validator("letter_value")
    @classmethod
    def validate_letter_value(cls, v: str) -> str:
        if not v.isalpha():
            raise ValueError("Индексная буква должна содержать только буквы")
        return v.upper()


class LocationSchema(BaseModel):
    """Схема валидации для местоположений"""

    id: int = Field(ge=1, description="ID местоположения")
    name: str = Field(
        min_length=1, max_length=200, description="Название местоположения"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()


class SourceSchema(BaseModel):
    """Схема валидации для источников (упрощённая)"""

    id: int = Field(ge=1, description="ID источника")
    name: str = Field(
        min_length=1, max_length=300, description="Название источника"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()


class CommentSchema(BaseModel):
    """Схема валидации для комментариев"""

    id: int = Field(ge=1, description="ID комментария")
    text: str = Field(
        min_length=1, max_length=1000, description="Текст комментария"
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        return v.strip()


class AppendixNoteSchema(BaseModel):
    """Схема валидации для примечаний"""

    id: int = Field(ge=1, description="ID примечания")
    text: str = Field(
        min_length=1, max_length=1000, description="Текст примечания"
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        return v.strip()


class StorageSchema(BaseModel):
    """Схема валидации для хранилищ"""

    id: int = Field(ge=1, description="ID хранилища")
    box_id: str = Field(min_length=1, max_length=50, description="ID бокса")
    cell_id: str = Field(min_length=1, max_length=10, description="ID ячейки")

    @field_validator("cell_id")
    @classmethod
    def validate_cell_id(cls, v: str) -> str:
        """Валидация формата ячейки (например, A1, B5, I9)"""
        pattern = r"^[A-I][1-9]$"
        if not re.match(pattern, v.upper()):
            raise ValueError(
                "Ячейка должна быть в формате A1-I9 (буква A-I, цифра 1-9)"
            )
        return v.upper()

    @field_validator("box_id")
    @classmethod
    def validate_box_id(cls, v: str) -> str:
        return v.strip()


class StrainSchema(BaseModel):
    """Схема валидации для штаммов"""

    id: int = Field(ge=1, description="ID штамма")
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


class IUKColorSchema(BaseModel):
    """Схема валидации для цветов ИУК"""

    id: int = Field(ge=1, description="ID цвета ИУК")
    name: str = Field(
        min_length=1, max_length=100, description="Название цвета"
    )
    hex_code: Optional[str] = Field(
        None, max_length=7, description="HEX код цвета"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("hex_code")
    @classmethod
    def validate_hex_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and not v.startswith("#"):
                v = f"#{v}"
            return v if v else None
        return v


class AmylaseVariantSchema(BaseModel):
    """Схема валидации для вариантов амилазы"""

    id: int = Field(ge=1, description="ID варианта амилазы")
    name: str = Field(
        min_length=1, max_length=200, description="Название варианта"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Описание"
    )

    @field_validator("name", "description")
    @classmethod
    def validate_text_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


class GrowthMediumSchema(BaseModel):
    """Схема валидации для сред роста"""

    id: int = Field(ge=1, description="ID среды роста")
    name: str = Field(
        min_length=1, max_length=200, description="Название среды роста"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Описание"
    )

    @field_validator("name", "description")
    @classmethod
    def validate_text_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


class SampleSchema(BaseModel):
    """Схема валидации для образцов"""

    id: int = Field(ge=1, description="ID образца")
    index_letter_id: Optional[int] = Field(
        None, ge=1, description="ID индексной буквы"
    )
    strain_id: Optional[int] = Field(None, ge=1, description="ID штамма")
    storage_id: Optional[int] = Field(None, ge=1, description="ID хранилища")
    original_sample_number: Optional[str] = Field(
        None, max_length=100, description="Оригинальный номер образца"
    )
    source_id: Optional[int] = Field(None, ge=1, description="ID источника")
    location_id: Optional[int] = Field(
        None, ge=1, description="ID местоположения"
    )
    appendix_note: Optional[str] = Field(
        None, max_length=1000, description="Текст примечания"
    )
    comment: Optional[str] = Field(None, max_length=1000, description="Текст комментария")
    has_photo: bool = Field(default=False, description="Есть ли фото")

    # Новые поля характеристик
    mobilizes_phosphates: bool = Field(
        default=False, description="Мобилизирует фосфаты"
    )
    stains_medium: bool = Field(
        default=False, description="Окрашивает среду"
    )
    produces_siderophores: bool = Field(
        default=False, description="Вырабатывает сидерофоры"
    )
    iuk_color_id: Optional[int] = Field(
        None, ge=1, description="ID цвета ИУК"
    )
    amylase_variant_id: Optional[int] = Field(
        None, ge=1, description="ID варианта амилазы"
    )
    growth_media_ids: Optional[list[int]] = Field(
        None, description="Список ID сред роста"
    )

    @field_validator("original_sample_number", "appendix_note", "comment")
    @classmethod
    def validate_text_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    @field_validator("growth_media_ids")
    @classmethod
    def validate_growth_media_ids(cls, v: Optional[list[int]]) -> Optional[list[int]]:
        if v is not None:
            # Убираем дубликаты и None значения
            v = list(set(filter(None, v)))
            return v if v else None
        return v


# Схемы для импорта данных из CSV
class ImportIndexLetterSchema(BaseModel):
    """Схема для импорта индексных букв из CSV"""

    IndexLetterID: int = Field(ge=1)
    IndexLetterValue: str = Field(min_length=1, max_length=10)


class ImportLocationSchema(BaseModel):
    """Схема для импорта местоположений из CSV"""

    LocationID: int = Field(ge=1)
    LocationNameValue: str = Field(min_length=1, max_length=200)


class ImportSourceSchema(BaseModel):
    """Схема валидации для импорта источников из CSV (упрощённая)"""

    SourceID: int = Field(ge=1)
    SourceOrganismName: str = Field(min_length=1, max_length=300)


class ImportCommentSchema(BaseModel):
    """Схема для импорта комментариев из CSV"""

    CommentID: int = Field(ge=1)
    CommentTextValue: str = Field(min_length=1, max_length=1000)


class ImportAppendixNoteSchema(BaseModel):
    """Схема для импорта примечаний из CSV"""

    AppendixNoteID: int = Field(ge=1)
    AppendixNoteText: str = Field(min_length=1, max_length=1000)


class ImportStorageSchema(BaseModel):
    """Схема для импорта хранилищ из CSV"""

    StorageID: int = Field(ge=1)
    BoxIDValue: str = Field(min_length=1, max_length=50)
    CellIDValue: str = Field(min_length=1, max_length=10)

    @field_validator("CellIDValue")
    @classmethod
    def validate_cell_id(cls, v: str) -> str:
        v = v.strip().upper()

        # Паттерн: Буква (A-Z) и одна или более цифр (A1, B10, I8, etc.)
        pattern = r"^[A-Z]\d+$"

        if not re.match(pattern, v):
            raise ValueError(
                f"Неверный формат ячейки: {v}. Должен быть, например, A1, B10, I8"
            )

        return v

    @field_validator("BoxIDValue")
    @classmethod
    def validate_box_id(cls, v: str) -> str:
        return v.strip()


class ImportStrainSchema(BaseModel):
    """Схема для импорта штаммов из CSV"""

    StrainID: int = Field(ge=1)
    ShortStrainCode: str = Field(min_length=1, max_length=50)
    RRNATaxonomy: Optional[str] = Field(None, max_length=500)
    StrainIdentifierValue: str = Field(min_length=1, max_length=100)
    StrainNameAlt: Optional[str] = Field(None, max_length=200)
    RCAMCollectionID: Optional[str] = Field(None, max_length=50)


class ImportSampleSchema(BaseModel):
    """Схема для импорта образцов из CSV"""

    SampleRowID: int = Field(ge=1)
    IndexLetterID_FK: Optional[int] = Field(None, ge=1)
    StrainID_FK: Optional[int] = Field(None, ge=1)
    StorageID_FK: Optional[int] = Field(None, ge=1)
    OriginalSampleNumber: Optional[str] = Field(None, max_length=100)
    SourceID_FK: Optional[int] = Field(None, ge=1)
    LocationID_FK: Optional[int] = Field(None, ge=1)
    AppendixNoteID_FK: Optional[int] = Field(None, ge=1)
    CommentID_FK: Optional[int] = Field(None, ge=1)
    HasPhoto: Annotated[
        str, Field(pattern=r"^(true|false|True|False|1|0|да|нет|)$")
    ]
    IsIdentified: Annotated[
        str, Field(pattern=r"^(true|false|True|False|1|0|да|нет|)$")
    ]
    HasAntibioticActivity: Annotated[
        str, Field(pattern=r"^(true|false|True|False|1|0|да|нет|)$")
    ]
    HasGenome: Annotated[
        str, Field(pattern=r"^(true|false|True|False|1|0|да|нет|)$")
    ]
    HasBiochemistry: Annotated[
        str, Field(pattern=r"^(true|false|True|False|1|0|да|нет|)$")
    ]
    SEQStatus: Annotated[
        str, Field(pattern=r"^(true|false|True|False|1|0|да|нет|)$")
    ]


# Вспомогательные функции для валидации
def validate_boolean_from_csv(value: str) -> bool:
    """Конвертация строкового значения из CSV в булево"""
    if not value or value.strip() == "":
        return False
    return value.lower() in ["true", "1", "yes", "да", "+"]


def validate_csv_row(schema_class, row_data: dict, row_number: int = None):
    """
    Валидация строки CSV с помощью Pydantic схемы

    Args:
        schema_class: Класс Pydantic схемы
        row_data: Данные строки как словарь
        row_number: Номер строки для отчета об ошибке

    Returns:
        Валидированные данные

    Raises:
        ValueError: При ошибке валидации
    """
    try:
        return schema_class.model_validate(row_data)
    except Exception as e:
        error_msg = "Ошибка валидации"
        if row_number:
            error_msg += f" в строке {row_number}"
        error_msg += f": {str(e)}"
        raise ValueError(error_msg)


class SampleCharacteristicSchema(BaseModel):
    """Схема валидации для характеристик образцов"""
    
    id: int = Field(ge=1, description="ID характеристики")
    name: str = Field(
        min_length=1, max_length=100, description="Название характеристики"
    )
    display_name: str = Field(
        min_length=1, max_length=200, description="Отображаемое название"
    )
    characteristic_type: str = Field(
        min_length=1, max_length=20, description="Тип характеристики"
    )
    options: Optional[str] = Field(
        None, max_length=1000, description="Опции для выбора (JSON)"
    )
    is_active: bool = Field(default=True, description="Активна ли характеристика")
    order: int = Field(default=0, description="Порядок отображения")
    color: Optional[str] = Field(
        None, max_length=7, description="Цвет для отображения"
    )
    
    @field_validator("name", "display_name")
    @classmethod
    def validate_text_fields(cls, v: str) -> str:
        return v.strip()
    
    @field_validator("characteristic_type")
    @classmethod
    def validate_characteristic_type(cls, v: str) -> str:
        allowed_types = ['boolean', 'select', 'text']
        if v not in allowed_types:
            raise ValueError(f"Тип характеристики должен быть одним из: {', '.join(allowed_types)}")
        return v
    
    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError("Цвет должен быть в формате HEX (#RRGGBB)")
        return v


class SampleCharacteristicValueSchema(BaseModel):
    """Схема валидации для значений характеристик образцов"""
    
    id: int = Field(ge=1, description="ID значения характеристики")
    sample_id: int = Field(ge=1, description="ID образца")
    characteristic_id: int = Field(ge=1, description="ID характеристики")
    boolean_value: Optional[bool] = Field(None, description="Булево значение")
    text_value: Optional[str] = Field(
        None, max_length=500, description="Текстовое значение"
    )
    select_value: Optional[str] = Field(
        None, max_length=200, description="Значение выбора"
    )
    
    @field_validator("text_value", "select_value")
    @classmethod
    def validate_text_fields(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v


class UpdateSampleSchema(BaseModel):
    """Схема для обновления образца с динамическими характеристиками"""
    
    strain_id: Optional[int] = Field(None, ge=1, description="ID штамма")
    storage_id: Optional[int] = Field(None, ge=1, description="ID хранилища")
    original_sample_number: Optional[str] = Field(
        None, max_length=100, description="Оригинальный номер образца"
    )
    source_id: Optional[int] = Field(None, ge=1, description="ID источника")
    location_id: Optional[int] = Field(
        None, ge=1, description="ID местоположения"
    )
    appendix_note: Optional[str] = Field(
        None, max_length=1000, description="Текст примечания"
    )
    comment: Optional[str] = Field(None, max_length=1000, description="Текст комментария")
    
    # Статические характеристики
    has_photo: Optional[bool] = Field(None, description="Есть ли фото")
    mobilizes_phosphates: Optional[bool] = Field(None, description="Мобилизирует фосфаты")
    stains_medium: Optional[bool] = Field(None, description="Окрашивает среду")
    produces_siderophores: Optional[bool] = Field(None, description="Вырабатывает сидерофоры")
    
    iuk_color_id: Optional[int] = Field(None, ge=1, description="ID цвета ИУК")
    amylase_variant_id: Optional[int] = Field(None, ge=1, description="ID варианта амилазы")
    
    # Среды роста
    growth_media_ids: Optional[List[int]] = Field(None, description="Список ID сред роста")
    
    # Динамические характеристики
    characteristics: Optional[dict] = Field(
        None, description="Динамические характеристики (ID характеристики -> значение)"
    )
    
    @field_validator("original_sample_number", "appendix_note", "comment")
    @classmethod
    def validate_text_fields(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v
    
    @field_validator("growth_media_ids")
    @classmethod
    def validate_growth_media_ids(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is not None:
            # Убираем дубликаты и None значения
            v = list(set(filter(None, v)))
            return v if v else None
        return v

# Вспомогательные функции для валидации
def validate_boolean_from_csv(value: str) -> bool:
    """Конвертация строкового значения из CSV в булево"""
    if not value or value.strip() == "":
        return False
    return value.lower() in ["true", "1", "yes", "да", "+"]


def validate_csv_row(schema_class, row_data: dict, row_number: int = None):
    """
    Валидация строки CSV с помощью Pydantic схемы

    Args:
        schema_class: Класс Pydantic схемы
        row_data: Данные строки как словарь
        row_number: Номер строки для отчета об ошибке

    Returns:
        Валидированные данные

    Raises:
        ValueError: При ошибке валидации
    """
    try:
        return schema_class.model_validate(row_data)
    except Exception as e:
        error_msg = "Ошибка валидации"
        if row_number:
            error_msg += f" в строке {row_number}"
        error_msg += f": {str(e)}"
        raise ValueError(error_msg)
