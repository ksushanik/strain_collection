"""
Схемы валидации данных с использованием Pydantic
"""

import re
from typing import Optional
from datetime import datetime

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
    """Схема валидации для источников"""

    id: int = Field(ge=1, description="ID источника")
    organism_name: str = Field(
        min_length=1, max_length=200, description="Название организма"
    )
    source_type: str = Field(
        min_length=1, max_length=100, description="Тип источника"
    )
    category: str = Field(
        min_length=1, max_length=100, description="Категория источника"
    )

    @field_validator("organism_name", "source_type", "category")
    @classmethod
    def validate_text_fields(cls, v: str) -> str:
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


class GrowthMediumSchema(BaseModel):
    """Схема валидации для сред роста"""

    id: int = Field(ge=1, description="ID среды роста")
    name: str = Field(
        min_length=1, max_length=200, description="Название среды роста"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Описание среды роста"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


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
    appendix_note_id: Optional[int] = Field(
        None, ge=1, description="ID примечания (устаревшее поле)"
    )
    comment_id: Optional[int] = Field(
        None, ge=1, description="ID комментария (устаревшее поле)"
    )

    # Новые текстовые поля для комментариев
    comment_text: Optional[str] = Field(
        None, max_length=1000, description="Текст комментария"
    )
    appendix_note_text: Optional[str] = Field(
        None, max_length=1000, description="Текст примечания"
    )

    # Существующие булевые поля
    has_photo: bool = Field(default=False, description="Есть ли фото")
    is_identified: bool = Field(
        default=False, description="Идентифицирован ли"
    )
    has_antibiotic_activity: bool = Field(
        default=False, description="Есть ли антибиотическая активность"
    )
    has_genome: bool = Field(default=False, description="Есть ли геном")
    has_biochemistry: bool = Field(
        default=False, description="Есть ли биохимия"
    )
    seq_status: bool = Field(
        default=False, description="Статус секвенирования"
    )

    # Новые характеристики образцов
    mobilizes_phosphates: bool = Field(
        default=False, description="Мобилизует фосфаты"
    )
    stains_medium: bool = Field(
        default=False, description="Окрашивает среду"
    )
    produces_siderophores: bool = Field(
        default=False, description="Вырабатывает сидерофоры"
    )
    produces_iuk: bool = Field(
        default=False, description="Вырабатывает ИУК"
    )
    produces_amylase: bool = Field(
        default=False, description="Вырабатывает амилазу"
    )

    # Дополнительные поля для новых характеристик
    iuk_color: Optional[str] = Field(
        None, max_length=100, description="Цвет окраски ИУК"
    )
    amylase_variant: Optional[str] = Field(
        None, max_length=100, description="Вариант амилазы"
    )

    # Поля для отслеживания времени
    created_at: str = Field(description="Дата и время создания")
    updated_at: str = Field(description="Дата и время последнего обновления")

    @field_validator("original_sample_number")
    @classmethod
    def validate_sample_number(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    @field_validator("comment_text", "appendix_note_text")
    @classmethod
    def validate_text_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    @field_validator("iuk_color", "amylase_variant")
    @classmethod
    def validate_optional_text_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
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
    """Схема для импорта источников из CSV"""

    SourceID: int = Field(ge=1)
    SourceOrganismName: str = Field(min_length=1, max_length=200)
    SourceTypeName: str = Field(min_length=1, max_length=100)
    SourceCategoryName: str = Field(min_length=1, max_length=100)


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
