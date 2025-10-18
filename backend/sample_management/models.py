from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class Sample(models.Model):
    """Образец штамма"""

    # Связи с другими моделями
    index_letter = models.ForeignKey(
        "reference_data.IndexLetter",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Индексная буква",
    )
    strain = models.ForeignKey(
        "strain_management.Strain",
        on_delete=models.CASCADE,
        related_name="samples",
        null=True,
        blank=True,
        verbose_name="Штамм",
    )
    storage = models.ForeignKey(
        "storage_management.Storage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Место хранения",
    )
    original_sample_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Оригинальный номер образца",
    )
    source = models.ForeignKey(
        "reference_data.Source",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Источник",
    )
    location = models.ForeignKey(
        "reference_data.Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Местоположение",
    )
    appendix_note = models.TextField(
        blank=True,
        null=True,
        verbose_name="Примечание",
    )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Комментарий",
    )

    # Булевы поля
    has_photo = models.BooleanField(default=False, verbose_name="Есть фото")

    # Поля с вариантами выбора
    iuk_color = models.ForeignKey(
        "reference_data.IUKColor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Цвет окраски ИУК"
    )
    amylase_variant = models.ForeignKey(
        "reference_data.AmylaseVariant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Вариант амилазы"
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Образец"
        verbose_name_plural = "Образцы"
        ordering = ["strain__short_code", "original_sample_number"]
        indexes = [
            models.Index(fields=["strain"], name="sample_strain_idx"),
            models.Index(fields=["storage"], name="sample_storage_idx"),
            models.Index(fields=["created_at"], name="sample_created_at_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["storage"], name="sample_storage_unique"),
        ]

    def __str__(self):
        strain_info = (
            f"{self.strain.short_code}" if self.strain else "Без штамма"
        )
        sample_num = (
            f" ({self.original_sample_number})"
            if self.original_sample_number
            else ""
        )
        return f"{strain_info}{sample_num}"

    @property
    def is_empty_cell(self):
        """Проверка, является ли ячейка пустой (свободной)"""
        return not self.strain and not self.original_sample_number


class SampleGrowthMedia(models.Model):
    """Связь образцов со средами роста (многие-ко-многим)"""

    sample = models.ForeignKey(
        Sample,
        on_delete=models.CASCADE,
        related_name="growth_media",
        verbose_name="Образец"
    )
    growth_medium = models.ForeignKey(
        "reference_data.GrowthMedium",
        on_delete=models.CASCADE,
        verbose_name="Среда роста",
        db_column="growthmedium_id"
    )

    class Meta:
        db_table = 'sample_growth_media'
        verbose_name = "Среда роста образца"
        verbose_name_plural = "Среды роста образцов"
        unique_together = ["sample", "growth_medium"]

    def __str__(self):
        return f"{self.sample} - {self.growth_medium}"


class SamplePhoto(models.Model):
    """Фотография, связанная с образцом"""

    sample = models.ForeignKey(
        Sample,
        on_delete=models.CASCADE,
        related_name="photos",
        verbose_name="Образец",
    )
    image = models.ImageField(
        upload_to="samples/%Y/%m/%d/",
        verbose_name="Изображение",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    class Meta:
        verbose_name = "Фотография образца"
        verbose_name_plural = "Фотографии образцов"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"Фото {self.id} для образца {self.sample_id}"


class SampleCharacteristic(models.Model):
    """Модель для управления характеристиками образцов"""
    
    CHARACTERISTIC_TYPES = [
        ('boolean', 'Да/Нет'),
        ('select', 'Выбор из списка'),
        ('text', 'Текстовое поле'),
    ]
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название характеристики"
    )
    display_name = models.CharField(
        max_length=150,
        verbose_name="Отображаемое название"
    )
    characteristic_type = models.CharField(
        max_length=20,
        choices=CHARACTERISTIC_TYPES,
        default='boolean',
        verbose_name="Тип характеристики"
    )
    options = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Варианты выбора (для типа 'select')",
        help_text="JSON массив с вариантами выбора, например: [\"Вариант 1\", \"Вариант 2\"]"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна"
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок отображения"
    )
    color = models.CharField(
        max_length=20,
        default='blue',
        verbose_name="Цвет для отображения",
        help_text="Цвет для чекбокса или бейджа (blue, green, red, purple, yellow, orange, pink, cyan, indigo)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    class Meta:
        verbose_name = "Характеристика образца"
        verbose_name_plural = "Характеристики образцов"
        ordering = ['order', 'display_name']
    
    def __str__(self):
        return self.display_name


class SampleCharacteristicValue(models.Model):
    """Значения характеристик для конкретных образцов"""
    
    sample = models.ForeignKey(
        Sample,
        on_delete=models.CASCADE,
        related_name="characteristic_values",
        verbose_name="Образец"
    )
    characteristic = models.ForeignKey(
        SampleCharacteristic,
        on_delete=models.CASCADE,
        related_name="values",
        verbose_name="Характеристика"
    )
    boolean_value = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Логическое значение"
    )
    text_value = models.TextField(
        null=True,
        blank=True,
        verbose_name="Текстовое значение"
    )
    select_value = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Выбранное значение"
    )
    
    class Meta:
        verbose_name = "Значение характеристики образца"
        verbose_name_plural = "Значения характеристик образцов"
        unique_together = ['sample', 'characteristic']
        indexes = [
            models.Index(
                fields=["characteristic", "boolean_value"],
                name="sample_char_bool_idx",
            ),
        ]
    
    def __str__(self):
        if self.characteristic.characteristic_type == 'boolean':
            value = "Да" if self.boolean_value else "Нет"
        elif self.characteristic.characteristic_type == 'select':
            value = self.select_value or "Не выбрано"
        else:
            value = self.text_value or "Не указано"
        
        return f"{self.sample} - {self.characteristic.display_name}: {value}"
    
    @property
    def value(self):
        """Возвращает значение в зависимости от типа характеристики"""
        if self.characteristic.characteristic_type == 'boolean':
            return self.boolean_value
        elif self.characteristic.characteristic_type == 'select':
            return self.select_value
        else:
            return self.text_value


# Сигналы для автоматического обновления поля has_photo

@receiver([post_save, post_delete], sender=SamplePhoto)
def update_sample_has_photo(sender, instance, **kwargs):
    """Обновляем Sample.has_photo, чтобы отражать наличие фото."""
    sample = instance.sample
    has_photo_now = sample.photos.exists()
    if sample.has_photo != has_photo_now:
        Sample.objects.filter(id=sample.id).update(has_photo=has_photo_now)


class SampleStorageAllocation(models.Model):
    """Связь образца с несколькими местами хранения (ячейками).
    Поддерживает флаг основного места (`is_primary`) и обеспечивает
    эксклюзивность ячейки: одна ячейка — один образец.
    """

    sample = models.ForeignKey(
        Sample,
        on_delete=models.CASCADE,
        related_name="storage_allocations",
        verbose_name="Образец",
    )
    storage = models.ForeignKey(
        "storage_management.Storage",
        on_delete=models.CASCADE,
        related_name="allocations",
        verbose_name="Место хранения",
    )
    is_primary = models.BooleanField(default=False, verbose_name="Основное место")
    allocated_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата размещения")

    class Meta:
        verbose_name = "Размещение образца"
        verbose_name_plural = "Размещения образцов"
        unique_together = ["sample", "storage"]
        indexes = [
            models.Index(fields=["sample"], name="sample_alloc_sample_idx"),
            models.Index(fields=["storage"], name="sample_alloc_storage_idx"),
        ]
        constraints = [
            # Одна ячейка не может содержать более одного образца
            models.UniqueConstraint(fields=["storage"], name="unique_storage_cell_allocation"),
            # Только одно основное место для образца
            models.UniqueConstraint(
                fields=["sample"],
                condition=models.Q(is_primary=True),
                name="unique_primary_allocation_per_sample",
            ),
        ]

    def __str__(self):
        return f"{self.sample} → {self.storage} ({'primary' if self.is_primary else 'extra'})"
