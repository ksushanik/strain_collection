from django.core.validators import RegexValidator
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


class Storage(models.Model):
    """Информация о хранении (бокс и ячейка)"""

    box_id = models.CharField(max_length=20, verbose_name="ID бокса")
    cell_id = models.CharField(
        max_length=20,
        verbose_name="ID ячейки",
        validators=[
            RegexValidator(
                regex=r"^[A-I][1-9]$",
                message="Ячейка должна быть в формате A1-I9",
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


class Sample(models.Model):
    """Образцы штаммов"""

    index_letter = models.ForeignKey(
        IndexLetter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Индексная буква",
    )
    strain = models.ForeignKey(
        Strain,
        on_delete=models.CASCADE,
        related_name="samples",
        null=True,
        blank=True,
        verbose_name="Штамм",
    )
    storage = models.ForeignKey(
        Storage,
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
        Source,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Источник",
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Местоположение",
    )
    appendix_note = models.ForeignKey(
        AppendixNote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Примечание",
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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


class ChangeLog(models.Model):
    """Модель для отслеживания изменений записей"""

    ACTION_CHOICES = [
        ("CREATE", "Создание"),
        ("UPDATE", "Обновление"),
        ("DELETE", "Удаление"),
        ("BULK_UPDATE", "Массовое обновление"),
        ("BULK_DELETE", "Массовое удаление"),
    ]

    CONTENT_TYPE_CHOICES = [
        ("strain", "Штамм"),
        ("sample", "Образец"),
        ("storage", "Хранилище"),
    ]

    content_type = models.CharField(
        max_length=20, choices=CONTENT_TYPE_CHOICES, verbose_name="Тип объекта"
    )
    object_id = models.IntegerField(verbose_name="ID объекта")
    action = models.CharField(
        max_length=20, choices=ACTION_CHOICES, verbose_name="Действие"
    )

    # Данные до изменения (JSON)
    old_values = models.JSONField(
        null=True, blank=True, verbose_name="Старые значения"
    )
    # Данные после изменения (JSON)
    new_values = models.JSONField(
        null=True, blank=True, verbose_name="Новые значения"
    )

    # Кто выполнил изменение
    user_info = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Пользователь"
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name="IP адрес"
    )
    user_agent = models.TextField(
        null=True, blank=True, verbose_name="User Agent"
    )

    # Дополнительная информация
    comment = models.TextField(
        null=True, blank=True, verbose_name="Комментарий"
    )
    batch_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="ID массовой операции",
    )

    # Временные метки
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата изменения"
    )

    class Meta:
        db_table = "changelog"
        verbose_name = "Журнал изменений"
        verbose_name_plural = "Журнал изменений"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["batch_id"]),
        ]

    def __str__(self):
        return f"{self.get_action_display()} {self.get_content_type_display()} #{self.object_id}"

    @classmethod
    def log_change(
        cls,
        content_type,
        object_id,
        action,
        old_values=None,
        new_values=None,
        user_info=None,
        ip_address=None,
        user_agent=None,
        comment=None,
        batch_id=None,
    ):
        """Удобный метод для записи изменений"""
        return cls.objects.create(
            content_type=content_type,
            object_id=object_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            user_info=user_info,
            ip_address=ip_address,
            user_agent=user_agent,
            comment=comment,
            batch_id=batch_id,
        )
