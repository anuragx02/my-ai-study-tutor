from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_add_chat_history"),
    ]

    operations = [
        migrations.CreateModel(
            name="KnowledgeBaseChunk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("chunk_index", models.PositiveIntegerField()),
                ("chunk_text", models.TextField()),
                ("token_count", models.PositiveIntegerField(default=0)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "knowledge_base",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chunks",
                        to="core.knowledgebase",
                    ),
                ),
            ],
            options={
                "db_table": "kb_knowledge_base_chunk",
                "ordering": ["knowledge_base_id", "chunk_index"],
                "unique_together": {("knowledge_base", "chunk_index")},
            },
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="citations",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="retrieval_confidence",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="source_type",
            field=models.CharField(
                choices=[("none", "None"), ("kb", "Knowledge Base"), ("web", "Web"), ("mixed", "Mixed")],
                default="none",
                max_length=20,
            ),
        ),
    ]
