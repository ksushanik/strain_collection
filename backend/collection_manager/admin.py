from django.contrib import admin
from audit_logging.models import ChangeLog


class ChangeLogAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "content_type",
        "object_id",
        "action",
        "user_info",
        "get_short_comment",
    ]
    list_filter = ["action", "content_type", "created_at"]
    search_fields = ["object_id", "user_info", "comment"]
    readonly_fields = [
        "content_type",
        "object_id",
        "action",
        "old_values",
        "new_values",
        "user_info",
        "ip_address",
        "user_agent",
        "comment",
        "batch_id",
        "created_at",
    ]
    ordering = ["-created_at"]

    def get_short_comment(self, obj):
        if obj.comment:
            return (
                obj.comment[:50] + "..."
                if len(obj.comment) > 50
                else obj.comment
            )
        return "-"

    get_short_comment.short_description = "Комментарий"

    def has_add_permission(self, request):
        return False  # Запрещаем ручное создание записей

    def has_change_permission(self, request, obj=None):
        return False  # Запрещаем редактирование

    def has_delete_permission(self, request, obj=None):
        return False  # Запрещаем удаление (только для чтения)


# Register with custom admin site
from strain_tracker_project.admin import admin_site
admin_site.register(ChangeLog, ChangeLogAdmin)
