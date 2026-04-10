import os

from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_or_sync_superuser(apps, schema_editor):
    """Create superuser from env vars or sync if exists. Always sync password on run."""
    email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip().lower()
    password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")
    name = os.getenv("DJANGO_SUPERUSER_NAME", "Admin").strip() or "Admin"

    if not email or not password:
        return

    User = apps.get_model("core", "User")
    db_alias = schema_editor.connection.alias

    user = User.objects.using(db_alias).filter(email=email).first()
    if not user:
        user = User(
            email=email,
            name=name,
            role="student",
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
    else:
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        if name and not user.name:
            user.name = name

    user.password = make_password(password)
    user.save(using=db_alias)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_alter_user_role_student_only"),
    ]

    operations = [
        migrations.RunPython(create_or_sync_superuser, migrations.RunPython.noop),
    ]
