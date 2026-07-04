"""
Django settings for restaurante_config project.
"""

from pathlib import Path
import os

import dj_database_url
from dotenv import load_dotenv

# ==========================
# CARGAR VARIABLES DE ENTORNO
# ==========================

load_dotenv()

# ==========================
# RUTAS
# ==========================

BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================
# SEGURIDAD
# ==========================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-c7d^amaaam&d$oen@yzgy(#x28$cv#yo1*s@ks9ak%*e37=!%g"
)

DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".onrender.com",
]

# ==========================
# APLICACIONES
# ==========================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'apps.usuarios',
    'apps.menu',
    'apps.reservas',
    'apps.mesas',
    'apps.pedidos',
    'apps.cocina',
    'apps.reportes',
    'apps.facturacion',
    'apps.auditoria',
    'apps.publico',
]

# ==========================
# MIDDLEWARE
# ==========================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'restaurante_config.urls'

# ==========================
# TEMPLATES
# ==========================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'restaurante_config.wsgi.application'

# ==========================
# BASE DE DATOS
# ==========================

if os.getenv("DB_ENGINE") == "postgres":

    DATABASES = {
        "default": dj_database_url.parse(
            os.getenv("DATABASE_URL")
        )
    }

else:

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ==========================
# VALIDADORES
# ==========================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ==========================
# INTERNACIONALIZACIÓN
# ==========================

LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/Guayaquil'

USE_I18N = True

USE_TZ = True

# ==========================
# ARCHIVOS ESTÁTICOS
# ==========================

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

# ==========================
# ARCHIVOS MEDIA
# ==========================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ==========================
# USUARIO PERSONALIZADO
# ==========================

AUTH_USER_MODEL = 'usuarios.Usuario'

# ==========================
# CSRF
# ==========================

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")

if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(
        f"https://{RENDER_EXTERNAL_HOSTNAME}"
    )

CSRF_USE_SESSIONS = True

# ==========================
# LOGIN
# ==========================

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'lista_usuarios'
LOGOUT_REDIRECT_URL = 'login'

# ==========================
# EMAIL
# ==========================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ==========================
# CLOUDINARY (DESCOMENTAR CUANDO LO INSTALES)
# ==========================


if os.getenv("CLOUDINARY_CLOUD_NAME"):

    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME"),
        "API_KEY": os.getenv("CLOUDINARY_API_KEY"),
        "API_SECRET": os.getenv("CLOUDINARY_API_SECRET"),
    }

    DEFAULT_FILE_STORAGE = (
        "cloudinary_storage.storage.MediaCloudinaryStorage"
    )


# ==========================
# DEFAULT PRIMARY KEY
# ==========================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'