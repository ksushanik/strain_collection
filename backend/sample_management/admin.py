from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Q
from .models import Sample, SamplePhoto, SampleGrowthMedia, SampleCharacteristic, SampleCharacteristicValue
from . import models


class SamplePhotoInline(admin.TabularInline):
    model = SamplePhoto
    extra = 1
    readonly_fields = ["photo_preview", "uploaded_at"]
    fields = ["image", "photo_preview", "uploaded_at"]
    
    def photo_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.image.url
            )
        return "Нет изображения"
    
    photo_preview.short_description = "Предварительный просмотр"


class SampleGrowthMediaInline(admin.TabularInline):
    model = SampleGrowthMedia
    extra = 1


class SampleCharacteristicValueInline(admin.TabularInline):
    """Inline для значений характеристик образца"""
    model = models.SampleCharacteristicValue
    extra = 0
    fields = ['characteristic', 'boolean_value', 'text_value', 'select_value']
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Показываем только активные характеристики
        formset.form.base_fields['characteristic'].queryset = models.SampleCharacteristic.objects.filter(is_active=True)
        return formset


class SamplePhotoAdmin(admin.ModelAdmin):
    list_display = ["sample", "image", "photo_preview", "uploaded_at"]
    list_filter = ["uploaded_at"]
    search_fields = ["sample__index_letter__letter_value", "sample__strain__short_code"]
    ordering = ["-uploaded_at"]
    readonly_fields = ["photo_preview", "uploaded_at"]
    
    def photo_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px;" />',
                obj.image.url
            )
        return "Нет изображения"
    
    photo_preview.short_description = "Предварительный просмотр"
    
    fieldsets = (
        ("Основная информация", {
            "fields": ("sample", "image")
        }),
        ("Предварительный просмотр", {
            "fields": ("photo_preview",),
            "classes": ("collapse",)
        }),
        ("Системная информация", {
            "fields": ("uploaded_at",),
            "classes": ("collapse",)
        }),
    )


@admin.register(SampleGrowthMedia)
class SampleGrowthMediaAdmin(admin.ModelAdmin):
    list_display = ["sample", "growth_medium", "get_sample_id"]
    list_filter = ["growth_medium"]
    search_fields = ["sample__index_letter__letter_value", "growth_medium__name"]
    ordering = ["sample"]
    
    def get_sample_id(self, obj):
        return f"{obj.sample.index_letter.letter_value if obj.sample.index_letter else ''}{obj.sample.id}" if obj.sample else "Не указан"
    
    get_sample_id.short_description = "ID образца"


# Custom filters for advanced filtering
class HasPhotoFilter(admin.SimpleListFilter):
    title = 'наличие фото'
    parameter_name = 'has_photo_filter'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Есть фото'),
            ('no', 'Нет фото'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(has_photo=True)
        if self.value() == 'no':
            return queryset.filter(has_photo=False)


class EmptyCellFilter(admin.SimpleListFilter):
    title = 'статус ячейки'
    parameter_name = 'empty_cell_filter'

    def lookups(self, request, model_admin):
        return (
            ('empty', 'Пустые ячейки'),
            ('occupied', 'Занятые ячейки'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'empty':
            return queryset.filter(strain__isnull=True, original_sample_number__isnull=True)
        if self.value() == 'occupied':
            return queryset.filter(Q(strain__isnull=False) | Q(original_sample_number__isnull=False))


class BiochemicalPropertiesFilter(admin.SimpleListFilter):
    title = 'биохимические свойства'
    parameter_name = 'biochemical_filter'

    def lookups(self, request, model_admin):
        return (
            # Фильтры теперь основаны на динамических характеристиках
            # Можно добавить фильтры по динамическим характеристикам при необходимости
        )

    def queryset(self, request, queryset):
        # Логика фильтрации теперь должна работать с динамическими характеристиками
        return queryset


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = [
        "get_sample_id", "strain", "storage", "source", "location",
        "has_photo_display", "get_photo_count", "get_growth_media_count", 
        "get_biochemical_summary", "created_at"
    ]
    list_filter = [
        HasPhotoFilter, EmptyCellFilter, BiochemicalPropertiesFilter,
        "created_at", "updated_at", "source", "location",
        "storage__box_id"
    ]
    search_fields = [
        "index_letter__letter_value", "strain__short_code", "strain__name_alt",
        "storage__box_id", "storage__cell_id", "source__name", "location__name",
        "appendix_note", "comment"
    ]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at", "get_sample_id", "get_photo_count", "get_growth_media_count"]
    inlines = [SamplePhotoInline, SampleGrowthMediaInline, SampleCharacteristicValueInline]
    
    fieldsets = (
        ("Основная информация", {
            "fields": ("index_letter", "strain", "storage", "original_sample_number")
        }),
        ("Происхождение", {
            "fields": ("source", "location")
        }),
        ("Характеристики", {
            "fields": ("iuk_color", "amylase_variant")
        }),
        ("Статус", {
            "fields": ("has_photo",)
        }),
        ("Дополнительная информация", {
            "fields": ("appendix_note", "comment"),
            "classes": ("collapse",)
        }),
        ("Статистика", {
            "fields": ("get_photo_count", "get_growth_media_count"),
            "classes": ("collapse",)
        }),
        ("Системная информация", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def get_sample_id(self, obj):
        return f"{obj.index_letter.letter_value if obj.index_letter else ''}{obj.id}"
    
    get_sample_id.short_description = "ID образца"
    
    def get_photo_count(self, obj):
        return obj.photos.count()
    
    get_photo_count.short_description = "Фото"
    
    def get_growth_media_count(self, obj):
        return obj.growth_media.count()
    
    get_growth_media_count.short_description = "Среды"
    
    def has_photo_display(self, obj):
        if obj.has_photo:
            return format_html('<span style="color: green; font-size: 16px;">●</span>')
        return format_html('<span style="color: red; font-size: 16px;">○</span>')
    
    has_photo_display.short_description = "Фото"
    has_photo_display.admin_order_field = "has_photo"
    
    def get_biochemical_summary(self, obj):
        """Краткое отображение биохимических свойств"""
        # Теперь характеристики хранятся как динамические значения
        # Можно получить их через obj.characteristic_values.all()
        properties = []
        
        for char_value in obj.characteristic_values.all():
            if char_value.value == 'True':
                properties.append(f'<span style="color: blue;">{char_value.characteristic.name}</span>')
        
        return format_html(' | '.join(properties)) if properties else '-'
    
    get_biochemical_summary.short_description = "Свойства"
    
    actions = [
        "export_selected_samples",
        "bulk_add_photos",
        "generate_sample_report"
    ]
    

    
    def export_selected_samples(self, request, queryset):
        from django.http import HttpResponse
        import csv
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="samples.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Index Letter', 'Strain', 'Storage', 'Source', 'Location',
            'IUK Color', 'Amylase Variant', 'Has Photo', 'Created At'
        ])
        
        for sample in queryset:
            writer.writerow([
                sample.index_letter.letter_value if sample.index_letter else '',
                sample.strain.short_code if sample.strain else '',
                f"{sample.storage.box_id}-{sample.storage.cell_id}" if sample.storage else '',
                sample.source.name if sample.source else '',
                sample.location.name if sample.location else '',
                sample.iuk_color.name if sample.iuk_color else '',
                sample.amylase_variant.name if sample.amylase_variant else '',
                'Да' if sample.has_photo else 'Нет',
                sample.created_at.strftime('%Y-%m-%d %H:%M:%S') if sample.created_at else ''
            ])
        
        return response
    
    export_selected_samples.short_description = "Экспортировать выбранные образцы в CSV"
    
    def generate_sample_report(self, request, queryset):
        from django.http import HttpResponse
        import csv
        from django.db.models import Count
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sample_report.csv"'
        
        writer = csv.writer(response)
        
        # Заголовок отчета
        writer.writerow(['ОТЧЕТ ПО ОБРАЗЦАМ'])
        writer.writerow([''])
        
        # Общая статистика
        total_samples = queryset.count()
        with_photos = queryset.filter(has_photo=True).count()
        
        writer.writerow(['ОБЩАЯ СТАТИСТИКА'])
        writer.writerow(['Всего образцов:', total_samples])
        writer.writerow(['С фотографими:', with_photos])
        writer.writerow([''])
        
        # Статистика по источникам
        writer.writerow(['СТАТИСТИКА ПО ИСТОЧНИКАМ'])
        source_stats = queryset.values('source__name').annotate(count=Count('id')).order_by('-count')
        for stat in source_stats:
            writer.writerow([stat['source__name'] or 'Не указан', stat['count']])
        
        writer.writerow([''])
        writer.writerow(['ДЕТАЛЬНЫЕ ДАННЫЕ'])
        writer.writerow([
            'ID', 'Штамм', 'Хранение', 'Источник', 'Локация', 'Фото'
        ])
        
        for sample in queryset:
            writer.writerow([
                f"{sample.index_letter.letter_value if sample.index_letter else ''}{sample.id}",
                sample.strain.short_code if sample.strain else '',
                f"{sample.storage.box_id}-{sample.storage.cell_id}" if sample.storage else '',
                sample.source.name if sample.source else '',
                sample.location.name if sample.location else '',
                'Да' if sample.has_photo else 'Нет'
            ])
        
        return response
    
    generate_sample_report.short_description = "Сгенерировать подробный отчет"
    
    def bulk_add_photos(self, request, queryset):
        # Простая реализация - можно расширить для массовой загрузки
        count = queryset.filter(has_photo=False).count()
        self.message_user(
            request,
            f"Выбрано {count} образцов без фото. Используйте inline редактирование для добавления фотографий."
        )
    
    bulk_add_photos.short_description = "Подготовить к массовому добавлению фото"
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'index_letter', 'strain', 'storage', 'source', 
            'location', 'iuk_color', 'amylase_variant'
        ).prefetch_related('photos', 'growth_media')


@admin.register(models.SampleCharacteristic)
class SampleCharacteristicAdmin(admin.ModelAdmin):
    """Админ для управления характеристиками образцов"""
    list_display = ['display_name', 'name', 'characteristic_type', 'is_active', 'order', 'color', 'created_at']
    list_filter = ['characteristic_type', 'is_active', 'color']
    search_fields = ['name', 'display_name']
    ordering = ['order', 'display_name']
    list_editable = ['is_active', 'order']
    
    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'display_name', 'characteristic_type']
        }),
        ('Настройки отображения', {
            'fields': ['color', 'order', 'is_active']
        }),
        ('Варианты выбора', {
            'fields': ['options'],
            'description': 'Для типа "Выбор из списка" укажите варианты в формате JSON массива, например: ["Вариант 1", "Вариант 2"]'
        }),
    ]
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Редактирование существующего объекта
            return ['name']  # Не позволяем менять системное имя
        return []
    
    actions = ['activate_characteristics', 'deactivate_characteristics']
    
    def activate_characteristics(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f"{updated} характеристик активировано."
        )
    activate_characteristics.short_description = "Активировать выбранные характеристики"
    
    def deactivate_characteristics(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{updated} характеристик деактивировано."
        )
    deactivate_characteristics.short_description = "Деактивировать выбранные характеристики"


@admin.register(models.SampleCharacteristicValue)
class SampleCharacteristicValueAdmin(admin.ModelAdmin):
    """Админ для значений характеристик образцов"""
    list_display = ['sample', 'characteristic', 'get_value_display']
    list_filter = ['characteristic', 'characteristic__characteristic_type']
    search_fields = ['sample__id', 'characteristic__display_name']
    ordering = ['sample', 'characteristic__order']
    
    def get_value_display(self, obj):
        """Отображение значения в зависимости от типа"""
        if obj.characteristic.characteristic_type == 'boolean':
            return "Да" if obj.boolean_value else "Нет"
        elif obj.characteristic.characteristic_type == 'select':
            return obj.select_value or "Не выбрано"
        else:
            return obj.text_value or "Не указано"
    get_value_display.short_description = "Значение"


# Register with custom admin site
from strain_tracker_project.admin import admin_site

admin_site.register(Sample, SampleAdmin)
admin_site.register(SamplePhoto, SamplePhotoAdmin)
admin_site.register(SampleGrowthMedia, SampleGrowthMediaAdmin)
admin_site.register(models.SampleCharacteristic, SampleCharacteristicAdmin)
admin_site.register(models.SampleCharacteristicValue, SampleCharacteristicValueAdmin)