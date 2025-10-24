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
    """Справочник источников образцов (упрощённая модель)"""

    name = models.CharField(
        max_length=300, unique=True, verbose_name="Название"
    )

    class Meta:
        verbose_name = "Источник"
        verbose_name_plural = "Источники"
        ordering = ["name"]

    def __str__(self):
        return self.name


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


class Comment(models.Model):
    """Справочник комментариев"""

    text = models.TextField(verbose_name="Текст комментария")

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return self.text[:50] + "..." if len(self.text) > 50 else self.text


class AppendixNote(models.Model):
    """Справочник примечаний"""

    text = models.TextField(verbose_name="Текст примечания")

    class Meta:
        verbose_name = "Примечание"
        verbose_name_plural = "Примечания"

    def __str__(self):
        return self.text[:50] + "..." if len(self.text) > 50 else self.text
