"""
Django settings for the Quizly project.

The project configuration supports both local development and production.
Environment-specific and sensitive values are loaded from the `.env` file.
"""

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def get_required_env(name):
    """
    Return a required environment-variable value.

    Args:
        name: Name of the required environment variable.

    Returns:
        str: The configured environment-variable value.

    Raises:
        ImproperlyConfigured: If the variable is missing or empty.
    """
    value = os.getenv(name)

    if not value:
        raise ImproperlyConfigured(
            f"The required environment variable '{name}' is missing."
        )

    return value


def get_env_bool(name, default=False):
    """
    Convert an environment-variable value into a Boolean.

    Accepted true values are `1`, `true`, `yes`, and `on`.
    Comparison is case-insensitive.

    Args:
        name: Name of the environment variable.
        default: Value returned when the variable is not configured.

    Returns:
        bool: The converted Boolean value.
    """
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_env_list(name, default=""):
    """
    Convert a comma-separated environment variable into a list.

    Empty entries and surrounding whitespace are removed.

    Args:
        name: Name of the environment variable.
        default: Comma-separated fallback value.

    Returns:
        list[str]: The configured non-empty values.
    """
    value = os.getenv(name, default)

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


# Security and environment configuration

SECRET_KEY = get_required_env("SECRET_KEY")

DEBUG = get_env_bool("DEBUG", default=False)

ALLOWED_HOSTS = get_env_list(
    "ALLOWED_HOSTS",
    default="127.0.0.1,localhost",
)


# Application definition

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
    "accounts",
    "quizzes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "core.wsgi.application"


# Database

SQLITE_PATH = os.getenv(
    "SQLITE_PATH",
    str(BASE_DIR / "db.sqlite3"),
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(SQLITE_PATH),
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# Internationalization

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "accounts.authentication.CookieJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}


# JWT authentication

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# Cross-origin configuration

DEFAULT_CORS_ALLOWED_ORIGINS = (
    "http://127.0.0.1:5500,"
    "http://localhost:5500,"
    "http://127.0.0.1:5501,"
    "http://localhost:5501"
)

CORS_ALLOWED_ORIGINS = get_env_list(
    "CORS_ALLOWED_ORIGINS",
    default=DEFAULT_CORS_ALLOWED_ORIGINS,
)

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = get_env_list(
    "CSRF_TRUSTED_ORIGINS",
)


# Authentication cookies

ACCESS_TOKEN_COOKIE_NAME = "access_token"
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"

AUTH_COOKIE_HTTP_ONLY = True
AUTH_COOKIE_SECURE = get_env_bool(
    "AUTH_COOKIE_SECURE",
    default=not DEBUG,
)
AUTH_COOKIE_SAMESITE = os.getenv(
    "AUTH_COOKIE_SAMESITE",
    "Lax",
)


# HTTPS and reverse-proxy security

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG