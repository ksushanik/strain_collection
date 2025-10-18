from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sample_management", "0005_remove_builtin_characteristic_fields"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="sample",
            index=models.Index(fields=["strain"], name="sample_strain_idx"),
        ),
        migrations.AddIndex(
            model_name="sample",
            index=models.Index(fields=["storage"], name="sample_storage_idx"),
        ),
        migrations.AddIndex(
            model_name="sample",
            index=models.Index(fields=["created_at"], name="sample_created_at_idx"),
        ),
        migrations.AddIndex(
            model_name="samplecharacteristicvalue",
            index=models.Index(
                fields=["characteristic", "boolean_value"],
                name="sample_char_bool_idx",
            ),
        ),
    ]
