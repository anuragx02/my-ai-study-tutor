import os

from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_superuser_from_env(apps, schema_editor):
    email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip().lower()
    password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")
    name = os.getenv("DJANGO_SUPERUSER_NAME", "Admin").strip() or "Admin"

    # Skip silently when env vars are not provided.
    if not email or not password:
        return

    User = apps.get_model("core", "User")
    db_alias = schema_editor.connection.alias

    user = User.objects.using(db_alias).filter(email=email).first()
    if user:
        changed = False
        if not user.is_staff:
            user.is_staff = True
            changed = True
        if not user.is_superuser:
            user.is_superuser = True
            changed = True
        if not user.is_active:
            user.is_active = True
            changed = True
        if changed:
            user.save(using=db_alias)
        return

    user = User(
        email=email,
        name=name,
        role="student",
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )
    user.password = make_password(password)
    user.save(using=db_alias)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_alter_user_role_student_only"),
    ]

    operations = [
        migrations.RunPython(create_superuser_from_env, migrations.RunPython.noop),
    ]
