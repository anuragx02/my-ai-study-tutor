from django.db import migrations, models


def backfill_quiz_focus(apps, schema_editor):
    Quiz = apps.get_model("core", "Quiz")

    for quiz in Quiz.objects.select_related("topic").all():
        focus = "General Study"
        if quiz.topic_id and quiz.topic and quiz.topic.title:
            focus = quiz.topic.title
        quiz.focus = focus
        quiz.save(update_fields=["focus"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_remove_studymaterial"),
    ]

    operations = [
        migrations.AddField(
            model_name="quiz",
            name="focus",
            field=models.CharField(blank=True, default="General Study", max_length=255),
        ),
        migrations.RunPython(backfill_quiz_focus, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="quiz",
            name="focus",
            field=models.CharField(default="General Study", max_length=255),
        ),
        migrations.RemoveField(
            model_name="quiz",
            name="topic",
        ),
        migrations.DeleteModel(
            name="Topic",
        ),
    ]
