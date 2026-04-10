# Generated migration: add simplified KnowledgeBase model (PDF/TXT only, no chunking)

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_create_superuser_from_env'),
    ]

    operations = [
        migrations.CreateModel(
            name='KnowledgeBase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('file_type', models.CharField(choices=[('pdf', 'PDF'), ('txt', 'TXT')], max_length=10)),
                ('original_filename', models.CharField(max_length=255)),
                ('file_text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='knowledge_bases', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Knowledge Bases',
                'db_table': 'kb_knowledge_base',
            },
        ),
        migrations.AddIndex(
            model_name='knowledgebase',
            index=models.Index(fields=['user', '-created_at'], name='kb_user_created_idx'),
        ),
    ]
