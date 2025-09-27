from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Strain


class StrainAdmin(admin.ModelAdmin):
    list_display = [
        "short_code", 
        "rrna_taxonomy", 
        "identifier", 
        "name_alt", 
        "rcam_collection_id",
        "get_samples_count",
        "created_at"
    ]
    list_filter = ["rrna_taxonomy", "created_at"]
    search_fields = [
        "short_code", 
        "rrna_taxonomy", 
        "identifier", 
        "name_alt", 
        "rcam_collection_id"
    ]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at", "get_samples_count"]
    
    fieldsets = (
        ("Основная информация", {
            "fields": ("short_code", "rrna_taxonomy", "identifier", "name_alt")
        }),
        ("Коллекция", {
            "fields": ("rcam_collection_id",)
        }),
        ("Системная информация", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def get_samples_count(self, obj):
        # Импортируем здесь, чтобы избежать циклических импортов
        from sample_management.models import Sample
        count = Sample.objects.filter(strain=obj).count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        return format_html('<span style="color: #999;">0</span>')
    
    get_samples_count.short_description = "Количество образцов"
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Добавляем аннотацию для оптимизации запросов
        return queryset.select_related()
    
    actions = ["export_selected_strains"]
    
    def export_selected_strains(self, request, queryset):
        # Простая реализация экспорта - можно расширить
        from django.http import HttpResponse
        import csv
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="strains.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Short Code', 'rRNA Taxonomy', 'Identifier', 
            'Alternative Name', 'RCAM Collection ID', 'Created At'
        ])
        
        for strain in queryset:
            writer.writerow([
                strain.short_code,
                strain.rrna_taxonomy,
                strain.identifier,
                strain.name_alt,
                strain.rcam_collection_id,
                strain.created_at.strftime('%Y-%m-%d %H:%M:%S') if strain.created_at else ''
            ])
        
        return response
    
    export_selected_strains.short_description = "Экспортировать выбранные штаммы в CSV"


# Register with custom admin site
from strain_tracker_project.admin import admin_site

admin_site.register(Strain, StrainAdmin)