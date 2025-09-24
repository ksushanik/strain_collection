from django.db import models


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
