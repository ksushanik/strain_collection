from django.contrib import admin
from django.utils.html import format_html

from .models import (
    IndexLetter,
    Location,
    Source,
    IUKColor,
    AmylaseVariant,
    GrowthMedium,
    Comment,
    AppendixNote,
)


class IndexLetterAdmin(admin.ModelAdmin):
    list_display = ["letter_value"]
    search_fields = ["letter_value"]
    ordering = ["letter_value"]


class LocationAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
    ordering = ["name"]




class SourceAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
    ordering = ["name"]


class IUKColorAdmin(admin.ModelAdmin):
    list_display = ["name", "hex_code", "color_preview"]
    search_fields = ["name"]
    ordering = ["name"]

    def color_preview(self, obj):
        if obj.hex_code:
            return format_html(
                '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; display: inline-block;"></div>',
                obj.hex_code,
            )
        return "-"

    color_preview.short_description = "Предварительный просмотр"


class AmylaseVariantAdmin(admin.ModelAdmin):
    list_display = ["name", "get_short_description"]
    search_fields = ["name", "description"]
    ordering = ["name"]

    def get_short_description(self, obj):
        if obj.description:
            return obj.description[:100] + "..." if len(obj.description) > 100 else obj.description
        return "-"

    get_short_description.short_description = "Описание"


class GrowthMediumAdmin(admin.ModelAdmin):
    list_display = ["name", "get_short_description"]
    search_fields = ["name", "description"]
    ordering = ["name"]

    def get_short_description(self, obj):
        if obj.description:
            return obj.description[:100] + "..." if len(obj.description) > 100 else obj.description
        return "-"

    get_short_description.short_description = "Описание"


class CommentAdmin(admin.ModelAdmin):
    list_display = ["get_short_text"]
    search_fields = ["text"]
    ordering = ["id"]

    def get_short_text(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text

    get_short_text.short_description = "Текст комментария"


class AppendixNoteAdmin(admin.ModelAdmin):
    list_display = ["get_short_text"]
    search_fields = ["text"]
    ordering = ["id"]

    def get_short_text(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text

    get_short_text.short_description = "Текст примечания"


from strain_tracker_project.admin import admin_site

admin_site.register(IndexLetter, IndexLetterAdmin)
admin_site.register(Location, LocationAdmin)
admin_site.register(Source, SourceAdmin)
admin_site.register(IUKColor, IUKColorAdmin)
admin_site.register(AmylaseVariant, AmylaseVariantAdmin)
admin_site.register(GrowthMedium, GrowthMediumAdmin)
admin_site.register(Comment, CommentAdmin)
admin_site.register(AppendixNote, AppendixNoteAdmin)
