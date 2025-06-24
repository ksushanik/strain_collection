# Generated manually to optimize search performance

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("collection_manager", "0002_alter_sample_storage"),
    ]

    operations = [
        # Базовые индексы для часто используемых полей поиска
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_strain_short_code ON collection_manager_strain (short_code);",
            reverse_sql="DROP INDEX IF EXISTS idx_strain_short_code;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_strain_identifier ON collection_manager_strain (identifier);",
            reverse_sql="DROP INDEX IF EXISTS idx_strain_identifier;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_strain_taxonomy ON collection_manager_strain (rrna_taxonomy);",
            reverse_sql="DROP INDEX IF EXISTS idx_strain_taxonomy;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_sample_original_number ON collection_manager_sample (original_sample_number);",
            reverse_sql="DROP INDEX IF EXISTS idx_sample_original_number;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_source_organism ON collection_manager_source (organism_name);",
            reverse_sql="DROP INDEX IF EXISTS idx_source_organism;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_source_type ON collection_manager_source (source_type);",
            reverse_sql="DROP INDEX IF EXISTS idx_source_type;",
        ),
        # Индексы для булевых полей (часто используемые в фильтрах)
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_sample_has_photo ON collection_manager_sample (has_photo);",
            reverse_sql="DROP INDEX IF EXISTS idx_sample_has_photo;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_sample_is_identified ON collection_manager_sample (is_identified);",
            reverse_sql="DROP INDEX IF EXISTS idx_sample_is_identified;",
        ),
        # Композитные индексы для часто используемых комбинаций
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_sample_strain_storage ON collection_manager_sample (strain_id, storage_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_sample_strain_storage;",
        ),
        # Индексы для дат
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_strain_created_at ON collection_manager_strain (created_at);",
            reverse_sql="DROP INDEX IF EXISTS idx_strain_created_at;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_sample_created_at ON collection_manager_sample (created_at);",
            reverse_sql="DROP INDEX IF EXISTS idx_sample_created_at;",
        ),
    ]
