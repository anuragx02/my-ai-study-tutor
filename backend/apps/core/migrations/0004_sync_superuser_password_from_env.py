import os

from django.db import migrations


def sync_superuser_password_from_env(apps, schema_editor):
    email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip().lower()
    password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")
    name = os.getenv("DJANGO_SUPERUSER_NAME", "Admin").strip() or "Admin"

    # Skip when credentials are not provided.
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

    # Always sync password from env so login works predictably.
    user.set_password(password)
    user.save(using=db_alias)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_create_superuser_from_env"),
    ]

    operations = [
        migrations.RunPython(sync_superuser_password_from_env, migrations.RunPython.noop),
    ]
