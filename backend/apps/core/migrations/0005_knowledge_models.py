from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_sync_superuser_password_from_env"),
    ]

    operations = [
        migrations.CreateModel(
            name="KnowledgeDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                (
                    "source_type",
                    models.CharField(
                        choices=[("pdf", "PDF"), ("docx", "DOCX"), ("txt", "TXT"), ("md", "Markdown"), ("image", "Image")],
                        max_length=20,
                    ),
                ),
                ("tags", models.JSONField(blank=True, default=list)),
                ("original_filename", models.CharField(max_length=255)),
                ("content", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("ready", "Ready"), ("failed", "Failed")], default="ready", max_length=20)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="knowledge_documents", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "db_table": "kb_document",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="KnowledgeChunk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("chunk_index", models.PositiveIntegerField()),
                ("content", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "document",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chunks", to="core.knowledgedocument"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="knowledge_chunks", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "db_table": "kb_chunk",
                "ordering": ["document_id", "chunk_index"],
                "unique_together": {("document", "chunk_index")},
            },
        ),
    ]
