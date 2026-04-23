from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_quiz_focus_remove_topic"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatmessage",
            name="image_url",
            field=models.TextField(blank=True, default=""),
        ),
    ]
