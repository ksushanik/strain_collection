from django.contrib import admin
from .models import ChangeLog


@admin.register(ChangeLog)
class ChangeLogAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'content_type',
        'object_id',
        'action',
        'user_info',
        'created_at'
    ]
    list_filter = [
        'content_type',
        'action',
        'created_at'
    ]
    search_fields = [
        'object_id',
        'user_info',
        'comment'
    ]
    readonly_fields = [
        'content_type',
        'object_id',
        'action',
        'old_values',
        'new_values',
        'user_info',
        'ip_address',
        'user_agent',
        'comment',
        'batch_id',
        'created_at'
    ]
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        """Запрещаем добавление записей через админку"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Запрещаем изменение записей через админку"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Запрещаем удаление записей через админку"""
        return False