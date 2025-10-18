from django.db import migrations


def copy_changelog_records(apps, schema_editor):
    connection = schema_editor.connection
    introspection = connection.introspection
    tables = {name.lower() for name in introspection.table_names()}

    legacy_table = "changelog"
    audit_table = "audit_changelog"

    if legacy_table not in tables or audit_table not in tables:
        return

    LegacyChangeLog = apps.get_model("collection_manager", "ChangeLog")
    AuditChangeLog = apps.get_model("audit_logging", "ChangeLog")

    existing_ids = set(
        AuditChangeLog.objects.values_list("id", flat=True)
    )

    to_create = []
    for entry in LegacyChangeLog.objects.all().iterator():
        if entry.id in existing_ids:
            continue
        to_create.append(
            AuditChangeLog(
                id=entry.id,
                content_type=entry.content_type,
                object_id=entry.object_id,
                action=entry.action,
                old_values=entry.old_values,
                new_values=entry.new_values,
                user_info=entry.user_info,
                ip_address=entry.ip_address,
                user_agent=entry.user_agent,
                comment=entry.comment,
                batch_id=entry.batch_id,
                created_at=entry.created_at,
            )
        )

    if not to_create:
        return

    AuditChangeLog.objects.bulk_create(to_create, batch_size=500)

    if connection.vendor == "postgresql":
        audit_db_table = AuditChangeLog._meta.db_table
        pk_column = AuditChangeLog._meta.pk.column
        quoted_table = connection.ops.quote_name(audit_db_table)
        with connection.cursor() as cursor:
            seq_sql = (
                f"SELECT setval(pg_get_serial_sequence(%s, %s), "
                f"(SELECT COALESCE(MAX(id), 1) FROM {quoted_table}))"
            )
            cursor.execute(seq_sql, [audit_db_table, pk_column])


class Migration(migrations.Migration):
    dependencies = [
        ("audit_logging", "0001_initial"),
        ("collection_manager", "0017_remove_sample_amylase_variant_delete_appendixnote_and_more"),
    ]

    operations = [
        migrations.RunPython(copy_changelog_records, migrations.RunPython.noop),
    ]
