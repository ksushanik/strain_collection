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
    is_identified = models.BooleanField(
        default=False, verbose_name="Идентифицирован"
    )
    has_antibiotic_activity = models.BooleanField(
        default=False, verbose_name="Есть антибиотическая активность"
    )
    has_genome = models.BooleanField(default=False, verbose_name="Есть геном")
    has_biochemistry = models.BooleanField(
        default=False, verbose_name="Есть биохимия"
    )
    seq_status = models.BooleanField(
        default=False, verbose_name="Статус секвенирования"
    )

    # Новые характеристики
    mobilizes_phosphates = models.BooleanField(
        default=False, verbose_name="Мобилизирует фосфаты"
    )
    stains_medium = models.BooleanField(
        default=False, verbose_name="Окрашивает среду"
    )
    produces_siderophores = models.BooleanField(
        default=False, verbose_name="Вырабатывает сидерофоры"
    )

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


# Сигналы для автоматического обновления поля has_photo

@receiver([post_save, post_delete], sender=SamplePhoto)
def update_sample_has_photo(sender, instance, **kwargs):
    """Обновляем Sample.has_photo, чтобы отражать наличие фото."""
    sample = instance.sample
    has_photo_now = sample.photos.exists()
    if sample.has_photo != has_photo_now:
        Sample.objects.filter(id=sample.id).update(has_photo=has_photo_now)
