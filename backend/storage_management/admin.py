from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Storage, StorageBox


class StorageInline(admin.TabularInline):
    model = Storage
    extra = 0
    fields = ["cell_id", "get_sample_info", "get_occupancy_status"]
    readonly_fields = ["get_sample_info", "get_occupancy_status"]
    fk_name = "box_id"  # Указываем связь через box_id
    
    def get_sample_info(self, obj):
        # Проверяем есть ли образец в этой ячейке
        from sample_management.models import Sample
        try:
            sample = Sample.objects.get(storage=obj)
            return format_html(
                '<strong>{}</strong><br/>Штамм: {}<br/>Источник: {}',
                f"{sample.index_letter.letter_value if sample.index_letter else ''}{sample.id}",
                sample.strain.short_code if sample.strain else "Не указан",
                sample.source.name if sample.source else "Не указан"
            )
        except Sample.DoesNotExist:
            return "Пустая ячейка"
    
    get_sample_info.short_description = "Информация об образце"
    
    def get_occupancy_status(self, obj):
        from sample_management.models import Sample
        if Sample.objects.filter(storage=obj).exists():
            return format_html('<span style="color: red;">●</span> Занята')
        return format_html('<span style="color: green;">●</span> Свободна')
    
    get_occupancy_status.short_description = "Статус"


class StorageBoxAdmin(admin.ModelAdmin):
    list_display = [
        "box_id", 
        "description", 
        "rows", 
        "cols", 
        "get_total_cells",
        "get_occupied_cells",
        "get_occupancy_percentage",
        "created_at"
    ]
    list_filter = ["rows", "cols", "created_at"]
    search_fields = ["box_id", "description"]
    ordering = ["box_id"]
    readonly_fields = [
        "created_at", 
        "get_total_cells", 
        "get_occupied_cells", 
        "get_occupancy_percentage"
    ]
    
    fieldsets = (
        ("Основная информация", {
            "fields": ("box_id", "description")
        }),
        ("Размеры", {
            "fields": ("rows", "cols")
        }),
        ("Статистика", {
            "fields": ("get_total_cells", "get_occupied_cells", "get_occupancy_percentage"),
            "classes": ("collapse",)
        }),
        ("Системная информация", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )
    
    def get_total_cells(self, obj):
        return obj.rows * obj.cols
    
    get_total_cells.short_description = "Всего ячеек"
    
    def get_occupied_cells(self, obj):
        from sample_management.models import Sample
        return Sample.objects.filter(storage__box_id=obj.box_id).count()
    
    get_occupied_cells.short_description = "Занято ячеек"
    
    def get_occupancy_percentage(self, obj):
        total = self.get_total_cells(obj)
        occupied = self.get_occupied_cells(obj)
        if total > 0:
            percentage = (occupied / total) * 100
            return f"{percentage:.1f}%"
        return "0%"
    
    get_occupancy_percentage.short_description = "Заполненность"
    
    actions = ["create_storage_cells"]
    
    def create_storage_cells(self, request, queryset):
        """Автоматически создает ячейки хранения для выбранных боксов"""
        created_count = 0
        
        for box in queryset:
            for row in range(1, box.rows + 1):
                for col in range(1, box.cols + 1):
                    cell_id = f"{chr(64 + row)}{col:02d}"  # A01, A02, B01, etc.
                    storage, created = Storage.objects.get_or_create(
                        box_id=box.box_id,
                        cell_id=cell_id
                    )
                    if created:
                        created_count += 1
        
        self.message_user(
            request,
            f"Создано {created_count} новых ячеек хранения."
        )
    
    create_storage_cells.short_description = "Создать ячейки хранения для выбранных боксов"


class StorageAdmin(admin.ModelAdmin):
    list_display = [
        "box_id", 
        "cell_id", 
        "get_sample_info",
        "get_occupancy_status"
    ]
    list_filter = ["box_id"]
    search_fields = ["box_id", "cell_id"]
    ordering = ["box_id", "cell_id"]
    
    def get_sample_info(self, obj):
        from sample_management.models import Sample
        try:
            sample = Sample.objects.get(storage=obj)
            return format_html(
                '<strong>{}</strong><br/>Штамм: {}',
                f"{sample.index_letter.letter_value if sample.index_letter else ''}{sample.id}",
                sample.strain.short_code if sample.strain else "Не указан"
            )
        except Sample.DoesNotExist:
            return "Пустая ячейка"
    
    get_sample_info.short_description = "Информация об образце"
    
    def get_occupancy_status(self, obj):
        from sample_management.models import Sample
        if Sample.objects.filter(storage=obj).exists():
            return format_html('<span style="color: red;">●</span> Занята')
        return format_html('<span style="color: green;">●</span> Свободна')
    
    get_occupancy_status.short_description = "Статус"
    
    actions = ["find_free_cells"]
    
    def find_free_cells(self, request, queryset):
        """Показывает свободные ячейки"""
        from sample_management.models import Sample
        free_cells = []
        
        for storage in queryset:
            try:
                Sample.objects.get(storage=storage)
            except Sample.DoesNotExist:
                free_cells.append(f"{storage.box_id}-{storage.cell_id}")
        
        if free_cells:
            self.message_user(
                request,
                f"Свободные ячейки: {', '.join(free_cells[:10])}" + 
                (f" и еще {len(free_cells) - 10}" if len(free_cells) > 10 else "")
            )
        else:
            self.message_user(request, "Все выбранные ячейки заняты.")
    
    find_free_cells.short_description = "Найти свободные ячейки"


# Register with custom admin site
from strain_tracker_project.admin import admin_site

admin_site.register(StorageBox, StorageBoxAdmin)
admin_site.register(Storage, StorageAdmin)