from django.db import connection, migrations


def drop_legacy_changelog(apps, schema_editor):
    tables = {name.lower() for name in connection.introspection.table_names()}
    legacy_table = "changelog"
    if legacy_table not in tables:
        return

    AuditChangeLog = apps.get_model("audit_logging", "ChangeLog")

    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM changelog")
        legacy_count = cursor.fetchone()[0]

    if legacy_count:
        audit_count = AuditChangeLog.objects.count()
        if audit_count < legacy_count:
            raise RuntimeError(
                "Количество записей в 'audit_changelog' меньше, чем в legacy 'changelog'."
            )

    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS changelog CASCADE")


class Migration(migrations.Migration):
    dependencies = [
        ("collection_manager", "0018_move_changelog_to_audit"),
    ]

    operations = [
        migrations.RunPython(drop_legacy_changelog, migrations.RunPython.noop),
    ]
