from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_create_superuser_from_env"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="explanation",
            field=models.TextField(blank=True),
        ),
    ]
