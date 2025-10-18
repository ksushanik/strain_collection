from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("strain_management", "0002_auto_20250924_1206"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="strain",
            index=models.Index(fields=["short_code"], name="strain_short_code_idx"),
        ),
    ]
