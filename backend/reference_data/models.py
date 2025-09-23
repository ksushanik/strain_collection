from django.db import models


class IndexLetter(models.Model):
    """Справочник индексных букв"""

    letter_value = models.CharField(
        max_length=10, unique=True, verbose_name="Индексная буква"
    )

    class Meta:
        verbose_name = "Индексная буква"
        verbose_name_plural = "Индексные буквы"
        ordering = ["letter_value"]

    def __str__(self):
        return self.letter_value


class Location(models.Model):
    """Справочник местоположений"""

    name = models.CharField(
        max_length=200, unique=True, verbose_name="Название местоположения"
    )

    class Meta:
        verbose_name = "Местоположение"
        verbose_name_plural = "Местоположения"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Source(models.Model):
    """Справочник источников образцов"""

    organism_name = models.CharField(
        max_length=300, verbose_name="Название организма"
    )
    source_type = models.CharField(
        max_length=100, verbose_name="Тип источника"
    )
    category = models.CharField(max_length=100, verbose_name="Категория")

    class Meta:
        verbose_name = "Источник"
        verbose_name_plural = "Источники"
        ordering = ["organism_name"]

    def __str__(self):
        return f"{self.organism_name} ({self.source_type})"


class IUKColor(models.Model):
    """Справочник цветов ИУК"""

    name = models.CharField(max_length=100, unique=True, verbose_name="Название цвета")
    hex_code = models.CharField(max_length=7, blank=True, null=True, verbose_name="HEX код цвета")

    class Meta:
        verbose_name = "Цвет ИУК"
        verbose_name_plural = "Цвета ИУК"
        ordering = ["name"]

    def __str__(self):
        return self.name


class AmylaseVariant(models.Model):
    """Справочник вариантов амилазы"""

    name = models.CharField(max_length=200, unique=True, verbose_name="Название варианта")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Вариант амилазы"
        verbose_name_plural = "Варианты амилазы"
        ordering = ["name"]

    def __str__(self):
        return self.name


class GrowthMedium(models.Model):
    """Справочник сред роста"""

    name = models.CharField(max_length=200, unique=True, verbose_name="Название среды роста")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Среда роста"
        verbose_name_plural = "Среды роста"
        ordering = ["name"]

    def __str__(self):
        return self.name
