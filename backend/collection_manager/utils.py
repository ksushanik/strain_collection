"""
Утилитные функции для collection_manager
"""

import uuid

from django.http import HttpRequest
from django.db import connection

from .models import ChangeLog


def get_client_ip(request: HttpRequest) -> str:
    """Получить IP адрес клиента"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_user_agent(request: HttpRequest) -> str:
    """Получить User Agent"""
    return request.META.get("HTTP_USER_AGENT", "")


def log_change(
    request: HttpRequest,
    content_type: str,
    object_id: int,
    action: str,
    old_values=None,
    new_values=None,
    comment=None,
    batch_id=None,
):
    """
    Логирование изменений

    Args:
        request: HTTP запрос
        content_type: тип объекта ('strain', 'sample', 'storage')
        object_id: ID объекта
        action: действие ('CREATE', 'UPDATE', 'DELETE', 'BULK_UPDATE', 'BULK_DELETE')
        old_values: старые значения (словарь)
        new_values: новые значения (словарь)
        comment: комментарий
        batch_id: ID массовой операции
    """
    try:
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        # Можно расширить для аутентификации
        user_info = f"API User ({ip_address})"

        ChangeLog.log_change(
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
    except Exception as e:
        # Логирование не должно ломать основной функционал
        print(f"Ошибка логирования изменений: {e}")


def generate_batch_id() -> str:
    """Генерировать уникальный ID для массовой операции"""
    return str(uuid.uuid4())


def reset_sequence(model):
    """Сбросить последовательность primary key, чтобы она соответствовала MAX(id)+1.

    Полезно, если база данных была импортирована вручную и последовательности
    не синхронизированы, что приводит к ошибке duplicate key value на вставке.
    """
    table_name = model._meta.db_table
    pk_column = model._meta.pk.column

    sql = (
        "SELECT setval(pg_get_serial_sequence(%s, %s), "
        "COALESCE((SELECT MAX(" + pk_column + ") FROM " + table_name + "), 1) + 1, false)"
    )

    with connection.cursor() as cursor:
        cursor.execute(sql, [table_name, pk_column])


def model_to_dict(instance, exclude_fields=None):
    """
    Конвертировать модель в словарь для логирования

    Args:
        instance: экземпляр модели Django
        exclude_fields: список полей для исключения
    """
    if exclude_fields is None:
        exclude_fields = ["created_at", "updated_at"]

    data = {}
    for field in instance._meta.get_fields():
        if field.name in exclude_fields:
            continue

        if hasattr(field, "related_model") and field.related_model:
            # Для внешних ключей сохраняем только ID
            if hasattr(instance, field.name + "_id"):
                data[field.name + "_id"] = getattr(
                    instance, field.name + "_id"
                )
        else:
            try:
                value = getattr(instance, field.name)
                # Преобразуем datetime в строку для JSON сериализации
                if hasattr(value, "isoformat"):
                    value = value.isoformat()
                data[field.name] = value
            except Exception:
                continue

    return data
