from django.db import migrations


class Migration(migrations.Migration):
    """
    Squashed placeholder migration for new installations.

    This replaces the legacy chain (0001-0019) that created duplicated tables.
    Existing environments that already applied the original migrations keep
    their history; fresh environments will only see this no-op migration.
    """

    replaces = [
        ("collection_manager", "0001_initial"),
        ("collection_manager", "0002_alter_sample_storage"),
        ("collection_manager", "0003_add_search_indexes"),
        ("collection_manager", "0004_create_changelog"),
        ("collection_manager", "0005_storagebox_alter_storage_cell_id"),
        ("collection_manager", "0006_samplephoto"),
        ("collection_manager", "0007_alter_sample_appendix_note_alter_sample_comment"),
        ("collection_manager", "0008_auto_20250902_0738"),
        ("collection_manager", "0009_fix_db_sync"),
        ("collection_manager", "0010_fix_db_sync2"),
        ("collection_manager", "0011_fix_db_sync3"),
        ("collection_manager", "0012_remove_extra_fields"),
        ("collection_manager", "0013_add_missing_models_and_fields"),
        ("collection_manager", "0014_mark_sample_growth_media_created"),
        ("collection_manager", "0015_growthmedium_samplegrowthmedia"),
        ("collection_manager", "0016_remove_legacy_models"),
        ("collection_manager", "0017_remove_sample_amylase_variant_delete_appendixnote_and_more"),
        ("collection_manager", "0018_move_changelog_to_audit"),
        ("collection_manager", "0019_cleanup_legacy_changelog"),
    ]

    initial = True

    dependencies = [
        ("audit_logging", "0001_initial"),
    ]

    operations = []

