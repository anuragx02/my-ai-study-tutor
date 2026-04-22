from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_question_explanation"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="question",
            name="explanation",
        ),
        migrations.DeleteModel(
            name="StudyRecommendation",
        ),
    ]
