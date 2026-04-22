from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_remove_question_explanation_and_studyrecommendation"),
    ]

    operations = [
        migrations.DeleteModel(
            name="StudyMaterial",
        ),
    ]
