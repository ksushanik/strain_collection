from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Q
from .models import Sample, SamplePhoto, SampleGrowthMedia


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
            ('has_biochemistry', 'Есть биохимия'),
            ('has_antibiotic_activity', 'Есть антибиотическая активность'),
            ('has_genome', 'Есть геном'),
            ('is_identified', 'Идентифицирован'),
            ('mobilizes_phosphates', 'Мобилизирует фосфаты'),
            ('stains_medium', 'Окрашивает среду'),
            ('produces_siderophores', 'Вырабатывает сидерофоры'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'has_biochemistry':
            return queryset.filter(has_biochemistry=True)
        if self.value() == 'has_antibiotic_activity':
            return queryset.filter(has_antibiotic_activity=True)
        if self.value() == 'has_genome':
            return queryset.filter(has_genome=True)
        if self.value() == 'is_identified':
            return queryset.filter(is_identified=True)
        if self.value() == 'mobilizes_phosphates':
            return queryset.filter(mobilizes_phosphates=True)
        if self.value() == 'stains_medium':
            return queryset.filter(stains_medium=True)
        if self.value() == 'produces_siderophores':
            return queryset.filter(produces_siderophores=True)


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
        "storage__box_id", "has_biochemistry", "has_antibiotic_activity",
        "has_genome", "is_identified", "mobilizes_phosphates", "stains_medium", "produces_siderophores"
    ]
    search_fields = [
        "index_letter__letter_value", "strain__short_code", "strain__name_alt",
        "storage__box_id", "storage__cell_id", "source__name", "location__name",
        "appendix_note", "comment"
    ]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at", "get_sample_id", "get_photo_count", "get_growth_media_count"]
    inlines = [SamplePhotoInline, SampleGrowthMediaInline]
    
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
        ("Биохимические свойства", {
            "fields": (
                ("has_biochemistry", "has_antibiotic_activity"),
                ("has_genome", "is_identified"),
                ("mobilizes_phosphates", "stains_medium"),
                "produces_siderophores"
            )
        }),
        ("Статус", {
            "fields": ("has_photo", "seq_status")
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
        properties = []
        
        if obj.has_biochemistry:
            properties.append('<span style="color: blue;">Биохим</span>')
        
        if obj.has_antibiotic_activity:
            properties.append('<span style="color: green;">Антибиот</span>')
        
        if obj.has_genome:
            properties.append('<span style="color: purple;">Геном</span>')
        
        if obj.is_identified:
            properties.append('<span style="color: orange;">Идент</span>')
        
        if obj.mobilizes_phosphates:
            properties.append('<span style="color: red;">Фосф</span>')
        
        if obj.stains_medium:
            properties.append('<span style="color: brown;">Окраш</span>')
        
        if obj.produces_siderophores:
            properties.append('<span style="color: darkgreen;">Сидер</span>')
        
        return format_html(' | '.join(properties)) if properties else '-'
    
    get_biochemical_summary.short_description = "Свойства"
    
    actions = [
        "mark_has_biochemistry",
        "mark_has_antibiotic_activity", 
        "mark_has_genome",
        "mark_identified",
        "export_selected_samples",
        "bulk_add_photos",
        "set_mobilizes_phosphates",
        "set_stains_medium",
        "set_produces_siderophores",
        "generate_sample_report"
    ]
    
    def mark_has_biochemistry(self, request, queryset):
        updated = queryset.update(has_biochemistry=True)
        self.message_user(
            request,
            f"{updated} образцов отмечено как имеющие биохимию."
        )
    
    mark_has_biochemistry.short_description = "Отметить как имеющие биохимию"
    
    def mark_has_antibiotic_activity(self, request, queryset):
        updated = queryset.update(has_antibiotic_activity=True)
        self.message_user(
            request,
            f"{updated} образцов отмечено как имеющие антибиотическую активность."
        )
    
    mark_has_antibiotic_activity.short_description = "Отметить как имеющие антибиотическую активность"
    
    def mark_has_genome(self, request, queryset):
        updated = queryset.update(has_genome=True)
        self.message_user(
            request,
            f"{updated} образцов отмечено как имеющие геном."
        )
    
    mark_has_genome.short_description = "Отметить как имеющие геном"
    
    def mark_identified(self, request, queryset):
        updated = queryset.update(is_identified=True)
        self.message_user(
            request,
            f"{updated} образцов отмечено как идентифицированные."
        )
    
    mark_identified.short_description = "Отметить как идентифицированные"
    
    def set_mobilizes_phosphates(self, request, queryset):
        updated = queryset.update(mobilizes_phosphates=True)
        self.message_user(
            request,
            f"{updated} образцов отмечено как мобилизирующие фосфаты."
        )
    
    set_mobilizes_phosphates.short_description = "Отметить как мобилизирующие фосфаты"
    
    def set_stains_medium(self, request, queryset):
        updated = queryset.update(stains_medium=True)
        self.message_user(
            request,
            f"{updated} образцов отмечено как окрашивающие среду."
        )
    
    set_stains_medium.short_description = "Отметить как окрашивающие среду"
    
    def set_produces_siderophores(self, request, queryset):
        updated = queryset.update(produces_siderophores=True)
        self.message_user(
            request,
            f"{updated} образцов отмечено как вырабатывающие сидерофоры."
        )
    
    set_produces_siderophores.short_description = "Отметить как вырабатывающие сидерофоры"
    
    def export_selected_samples(self, request, queryset):
        from django.http import HttpResponse
        import csv
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="samples.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Index Letter', 'Strain', 'Storage', 'Source', 'Location',
            'IUK Color', 'Amylase Variant', 'Has Photo', 'Has Biochemistry',
            'Has Antibiotic Activity', 'Has Genome', 'Is Identified',
            'Mobilizes Phosphates', 'Stains Medium', 'Produces Siderophores', 'Created At'
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
                'Да' if sample.has_biochemistry else 'Нет',
                'Да' if sample.has_antibiotic_activity else 'Нет',
                'Да' if sample.has_genome else 'Нет',
                'Да' if sample.is_identified else 'Нет',
                'Да' if sample.mobilizes_phosphates else 'Нет',
                'Да' if sample.stains_medium else 'Нет',
                'Да' if sample.produces_siderophores else 'Нет',
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
        with_biochemistry = queryset.filter(has_biochemistry=True).count()
        with_genome = queryset.filter(has_genome=True).count()
        identified = queryset.filter(is_identified=True).count()
        
        writer.writerow(['ОБЩАЯ СТАТИСТИКА'])
        writer.writerow(['Всего образцов:', total_samples])
        writer.writerow(['С фотографими:', with_photos])
        writer.writerow(['С биохимией:', with_biochemistry])
        writer.writerow(['С геномом:', with_genome])
        writer.writerow(['Идентифицированных:', identified])
        writer.writerow([''])
        
        # Статистика по источникам
        writer.writerow(['СТАТИСТИКА ПО ИСТОЧНИКАМ'])
        source_stats = queryset.values('source__name').annotate(count=Count('id')).order_by('-count')
        for stat in source_stats:
            writer.writerow([stat['source__name'] or 'Не указан', stat['count']])
        
        writer.writerow([''])
        writer.writerow(['ДЕТАЛЬНЫЕ ДАННЫЕ'])
        writer.writerow([
            'ID', 'Штамм', 'Хранение', 'Источник', 'Локация',
            'Фото', 'Биохимия', 'Геном', 'Идентификация', 'Антибиотики'
        ])
        
        for sample in queryset:
            writer.writerow([
                f"{sample.index_letter.letter_value if sample.index_letter else ''}{sample.id}",
                sample.strain.short_code if sample.strain else '',
                f"{sample.storage.box_id}-{sample.storage.cell_id}" if sample.storage else '',
                sample.source.name if sample.source else '',
                sample.location.name if sample.location else '',
                'Да' if sample.has_photo else 'Нет',
                'Да' if sample.has_biochemistry else 'Нет',
                'Да' if sample.has_genome else 'Нет',
                'Да' if sample.is_identified else 'Нет',
                'Да' if sample.has_antibiotic_activity else 'Нет'
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


# Register with custom admin site
from strain_tracker_project.admin import admin_site

admin_site.register(Sample, SampleAdmin)
admin_site.register(SamplePhoto, SamplePhotoAdmin)
admin_site.register(SampleGrowthMedia, SampleGrowthMediaAdmin)