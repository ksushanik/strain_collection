from django.contrib import admin
from django.db import models
from django import forms
from django.db.models import Count
from django.utils.html import format_html

from .models import (AppendixNote, ChangeLog, Comment, IndexLetter, Location,
                     Sample, Source, Storage, Strain)


@admin.register(IndexLetter)
class IndexLetterAdmin(admin.ModelAdmin):
    list_display = ["letter_value"]
    search_fields = ["letter_value"]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ["organism_name", "source_type", "category"]
    list_filter = ["source_type", "category"]
    search_fields = ["organism_name", "source_type"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["get_short_text"]
    search_fields = ["text"]

    def get_short_text(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text

    get_short_text.short_description = "Текст комментария"


@admin.register(AppendixNote)
class AppendixNoteAdmin(admin.ModelAdmin):
    list_display = ["get_short_text"]
    search_fields = ["text"]

    def get_short_text(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text

    get_short_text.short_description = "Текст примечания"


@admin.register(Storage)
class StorageAdmin(admin.ModelAdmin):
    list_display = ["box_id", "cell_id", "is_occupied"]
    list_filter = ["box_id"]
    search_fields = ["box_id", "cell_id"]
    ordering = ["box_id", "cell_id"]

    def is_occupied(self, obj):
        try:
            sample = obj.sample
            if sample.strain:
                return format_html('<span style="color: green;">Занята</span>')
            else:
                return format_html(
                    '<span style="color: orange;">Свободная ячейка</span>'
                )
        except AttributeError:
            return format_html('<span style="color: red;">Пустая</span>')

    is_occupied.short_description = "Статус"


class SampleInline(admin.TabularInline):
    model = Sample
    extra = 0
    fields = [
        "storage",
        "original_sample_number",
        "has_photo",
        "is_identified",
    ]
    readonly_fields = ["created_at"]


@admin.register(Strain)
class StrainAdmin(admin.ModelAdmin):
    list_display = [
        "short_code",
        "rrna_taxonomy",
        "rcam_collection_id",
        "sample_count",
        "created_at",
    ]
    list_filter = ["rrna_taxonomy", "created_at"]
    search_fields = ["short_code", "identifier", "rrna_taxonomy"]
    inlines = [SampleInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(_sample_count=Count("samples"))
        return queryset

    def sample_count(self, obj):
        return obj._sample_count

    sample_count.short_description = "Кол-во образцов"
    sample_count.admin_order_field = "_sample_count"


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = [
        "get_strain_code",
        "original_sample_number",
        "get_storage_info",
        "has_photo",
        "is_identified",
        "has_antibiotic_activity",
    ]
    list_filter = [
        "has_photo",
        "is_identified",
        "has_antibiotic_activity",
        "has_genome",
        "has_biochemistry",
        "seq_status",
        "strain__rrna_taxonomy",
        "location",
    ]
    search_fields = [
        "strain__short_code",
        "strain__identifier",
        "original_sample_number",
        "storage__box_id",
        "storage__cell_id",
    ]
    autocomplete_fields = ["strain", "source", "location"]

    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    fieldsets = (
        (
            "Основная информация",
            {"fields": ("strain", "original_sample_number", "index_letter")},
        ),
        ("Размещение", {"fields": ("storage", "location")}),
        (
            "Источник и дополнительно",
            {"fields": ("source", "appendix_note", "comment")},
        ),
        (
            "Характеристики",
            {
                "fields": (
                    "has_photo",
                    "is_identified",
                    "has_antibiotic_activity",
                    "has_genome",
                    "has_biochemistry",
                    "seq_status",
                )
            },
        ),
    )

    def get_strain_code(self, obj):
        return obj.strain.short_code if obj.strain else "Без штамма"

    get_strain_code.short_description = "Код штамма"
    get_strain_code.admin_order_field = "strain__short_code"

    def get_storage_info(self, obj):
        if obj.storage:
            return f"Бокс {obj.storage.box_id}, {obj.storage.cell_id}"
        return "Не указано"

    get_storage_info.short_description = "Хранение"
    get_storage_info.admin_order_field = "storage__box_id"


@admin.register(ChangeLog)
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
