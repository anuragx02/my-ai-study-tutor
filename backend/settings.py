from pathlib import Path
import os

import dj_database_url
from datetime import timedelta

import environ

BASE_DIR = Path(__file__).resolve().parent

env = environ.Env()

env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-insecure-key-change-me")
DEBUG = env.bool("DEBUG", default=False)

# On Render, RENDER_EXTERNAL_HOSTNAME is set automatically.
render_hostname = env("RENDER_EXTERNAL_HOSTNAME", default="").strip()
configured_hosts = [host.strip() for host in env.list("ALLOWED_HOSTS", default=[]) if host.strip()]

if render_hostname:
    configured_hosts.append(render_hostname)

# Keep common local hosts available for development.
configured_hosts.extend(["localhost", "127.0.0.1"])
ALLOWED_HOSTS = sorted(set(configured_hosts))
render_origin = f"https://{render_hostname}" if render_hostname else ""

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "backend.apps.core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR.parent / "frontend" / "dist"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"
ASGI_APPLICATION = "backend.asgi.application"

database_url = env("DATABASE_URL", default="").strip()

# Guard against a Windows-style sqlite path accidentally deployed to Linux,
# e.g. sqlite:///d:/heatmap/... which is invalid on Render.
if database_url.startswith("sqlite:///"):
    sqlite_path = database_url.removeprefix("sqlite:///")
    if os.name != "nt" and len(sqlite_path) > 1 and sqlite_path[1] == ":":
        database_url = ""

if not database_url:
    # Render Linux instances can always write to /tmp; use it for no-DB demo mode.
    fallback_sqlite = Path("/tmp/db.sqlite3") if os.name != "nt" else (BASE_DIR / "db.sqlite3")
    database_url = f"sqlite:///{fallback_sqlite.as_posix()}"

if database_url.startswith("sqlite:///"):
    sqlite_target = Path(database_url.removeprefix("sqlite:///"))
    sqlite_target.parent.mkdir(parents=True, exist_ok=True)

DATABASES = {
    "default": dj_database_url.parse(database_url)
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
_static_candidates = [
    BASE_DIR.parent / "static",
    BASE_DIR.parent / "frontend" / "dist",
]
STATICFILES_DIRS = [path for path in _static_candidates if path.exists()]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "core.User"

CORS_ALLOWED_ORIGINS = [origin.strip() for origin in env.list("CORS_ALLOWED_ORIGINS", default=[]) if origin.strip()]
if render_origin and render_origin not in CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS.append(render_origin)
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in env.list("CSRF_TRUSTED_ORIGINS", default=[]) if origin.strip()]
if render_origin and render_origin not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(render_origin)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "20/min", "user": "120/min"},
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

GROQ_API_KEY = env("GROQ_API_KEY")
GROQ_API_BASE = env("GROQ_API_BASE")
GROQ_MODEL = env("GROQ_MODEL")