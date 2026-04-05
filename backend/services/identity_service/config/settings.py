import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "infrastructure.db.core.apps.CoreConfig",
    "drf_spectacular",
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "ticketing"),
        "USER": os.environ.get("POSTGRES_USER", "ticketing"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "ticketing"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Identity Service API",
    "DESCRIPTION": "OpenAPI 3 schema for the Identity Service",
    "VERSION": "v1",
}

CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5176",
).split(",")

FRONTEND_APP_URL = os.environ.get("FRONTEND_APP_URL", "http://localhost:5176")
INVITE_TOKEN_TTL_HOURS = int(os.environ.get("INVITE_TOKEN_TTL_HOURS", "72"))

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", os.environ.get("SMTP_HOST", ""))
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", os.environ.get("SMTP_PORT", "587")))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", os.environ.get("SMTP_USER", ""))
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", os.environ.get("SMTP_PASSWORD", ""))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", os.environ.get("SMTP_USE_TLS", "1")).lower() in ("1", "true", "yes")
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", os.environ.get("SMTP_USE_SSL", "0")).lower() in ("1", "true", "yes")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", os.environ.get("SMTP_FROM_EMAIL", "no-reply@localhost"))
