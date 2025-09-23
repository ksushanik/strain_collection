from django.db import models


class Strain(models.Model):
    """Штаммы микроорганизмов"""

    short_code = models.CharField(
        max_length=100, verbose_name="Короткий код штамма"
    )
    rrna_taxonomy = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="rRNA таксономия"
    )
    identifier = models.CharField(
        max_length=200, verbose_name="Идентификатор штамма"
    )
    name_alt = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Альтернативное название",
    )
    rcam_collection_id = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="ID коллекции RCAM"
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Штамм"
        verbose_name_plural = "Штаммы"
        ordering = ["short_code"]

    def __str__(self):
        return f"{self.short_code} - {self.identifier}"
