from django.core.validators import RegexValidator
from django.db import models


class Storage(models.Model):
    """Информация о хранении (бокс и ячейка)"""

    box_id = models.CharField(max_length=20, verbose_name="ID бокса")
    cell_id = models.CharField(
        max_length=20,
        verbose_name="ID ячейки",
        validators=[
            RegexValidator(
                regex=r"^[A-Z][0-9]{1,2}$",
                message="Ячейка должна быть в формате букваA-Z + номер 1-99 (например A1, B12)",
            )
        ],
    )

    class Meta:
        verbose_name = "Хранилище"
        verbose_name_plural = "Хранилища"
        unique_together = ["box_id", "cell_id"]
        ordering = ["box_id", "cell_id"]

    def __str__(self):
        return f"Бокс {self.box_id}, ячейка {self.cell_id}"


class StorageBox(models.Model):
    """Модель бокса (контейнера) для хранения образцов.

    При создании бокса желательно автоматически генерировать все ячейки
    (Storage) через сервис/management-command, поэтому сама модель хранит
    только размерность и метаданные.
    """

    box_id = models.CharField(max_length=20, unique=True, verbose_name="ID бокса")
    rows = models.PositiveIntegerField(verbose_name="Количество рядов")
    cols = models.PositiveIntegerField(verbose_name="Количество колонок")
    description = models.TextField(null=True, blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Бокс"
        verbose_name_plural = "Боксы"
        ordering = ["box_id"]

    def __str__(self):
        return f"Бокс {self.box_id} ({self.rows}×{self.cols})"
