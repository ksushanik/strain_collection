from django.contrib import admin
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.urls import path
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from django.db import connection

from sample_management.models import Sample
from strain_management.models import Strain
from storage_management.models import Storage
from reference_data.models import Location
from collection_manager.models import ChangeLog


class CustomAdminSite(AdminSite):
    site_title = _('Strain Collection Admin')
    site_header = _('Strain Collection Management')
    index_title = _('Collection Dashboard')

    def index(self, request, extra_context=None):
        """
        Display the main admin index page with custom statistics.
        """
        extra_context = extra_context or {}
        
        # Calculate statistics
        total_samples = Sample.objects.count()
        total_strains = Strain.objects.count()
        total_locations = Location.objects.count()
        
        # Sample statistics
        identified_samples = Sample.objects.filter(is_identified=True).count()
        samples_with_photos = Sample.objects.filter(has_photo=True).count()
        samples_with_biochemistry = Sample.objects.filter(has_biochemistry=True).count()
        samples_with_genome = Sample.objects.filter(has_genome=True).count()
        
        # Storage statistics - используем ту же логику что и в storage_summary API
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as total_cells,
                    COUNT(CASE WHEN sam.strain_id IS NOT NULL THEN 1 ELSE NULL END) as occupied_cells
                FROM storage_management_storage s
                LEFT JOIN sample_management_sample sam ON s.id = sam.storage_id
            """)
            row = cursor.fetchone()
            total_storage_cells, occupied_cells = row
        
        # Calculate samples that have storage assigned
        samples_with_storage = Sample.objects.filter(storage__isnull=False).count()
        
        storage_occupancy = 0
        if total_storage_cells > 0:
            storage_occupancy = round((occupied_cells / total_storage_cells) * 100, 1)
        
        extra_context.update({
            'total_samples': total_samples,
            'total_strains': total_strains,
            'total_locations': total_locations,
            'identified_samples': identified_samples,
            'samples_with_photos': samples_with_photos,
            'samples_with_biochemistry': samples_with_biochemistry,
            'samples_with_genome': samples_with_genome,
            'storage_occupancy': storage_occupancy,
            'total_storage_cells': total_storage_cells,
            'occupied_cells': occupied_cells,
            'samples_with_storage': samples_with_storage,
        })
        
        return super().index(request, extra_context)


# Create custom admin site instance
admin_site = CustomAdminSite(name='custom_admin')