"""
Configuración principal de Django para el proyecto 'restaurante_config'.

Este archivo centraliza todas las configuraciones del sistema ERP, incluyendo:
- Carga de variables de entorno (.env) para proteger datos sensibles.
- Configuración de aplicaciones, middleware y plantillas.
- Conexión a base de datos dinámica (PostgreSQL para producción, SQLite para desarrollo local).
- Gestión avanzada de archivos estáticos y multimedia usando Whitenoise y Cloudinary.
- Políticas de seguridad y configuraciones específicas para el despliegue en Render.
"""

from pathlib import Path
import os

import dj_database_url
from dotenv import load_dotenv

# ==========================================
# VARIABLES DE ENTORNO
# ==========================================
# Carga las variables de entorno desde el archivo .env ubicado en la raíz del proyecto.
# Esto asegura que credenciales y claves secretas no se suban al repositorio (Git).
load_dotenv()

# ==========================================
# RUTAS PRINCIPALES DEL PROYECTO
# ==========================================
# BASE_DIR apunta a la raíz del proyecto (el directorio que contiene manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================
# CONFIGURACIÓN DE SEGURIDAD
# ==========================================

# Clave secreta para hashes criptográficos. En producción SIEMPRE debe venir del .env.
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-c7d^amaaam&d$oen@yzgy(#x28$cv#yo1*s@ks9ak%*e37=!%g"
)

# Modo depuración: 'True' muestra errores detallados. NUNCA usar 'True' en producción.
# Se lee del .env y se convierte a booleano.
DEBUG = os.getenv("DEBUG", "True") == "True"

# Dominios desde los cuales se puede acceder a la aplicación.
# Incluye localhost para desarrollo y '.onrender.com' para el despliegue.
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".onrender.com",
]

# ==========================================
# APLICACIONES INSTALADAS
# ==========================================
INSTALLED_APPS = [
    # Aplicaciones nativas de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Aplicaciones de terceros (Integración con Cloudinary para imágenes)
    'cloudinary',
    'cloudinary_storage',
    
    # Módulos del Sistema ERP (Aplicaciones locales)
    'apps.usuarios',      # Gestión de usuarios y perfiles
    'apps.menu',          # Platos y categorías
    'apps.reservas',      # Agendamiento de clientes
    'apps.mesas',         # Control de estado de las mesas
    'apps.pedidos',       # Gestión de comandas
    'apps.cocina',        # Monitor de órdenes para preparación
    'apps.reportes',      # Estadísticas y métricas
    'apps.facturacion',   # Cobros y recibos
    'apps.auditoria',     # Registro de eventos y seguridad
    'apps.publico',       # Vistas para el cliente final
]

# ==========================================
# MIDDLEWARE
# ==========================================
# Capas de procesamiento que se ejecutan en cada petición (request/response).
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Whitenoise: Permite a Django servir archivos estáticos eficientemente en producción
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Archivo raíz donde Django buscará las URLs principales
ROOT_URLCONF = 'restaurante_config.urls'

# ==========================================
# PLANTILLAS (TEMPLATES)
# ==========================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Directorio global para plantillas base o genéricas
        'DIRS': [BASE_DIR / 'templates'],
        # Indica a Django que busque carpetas 'templates' dentro de cada aplicación
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

# Interfaz estándar de Python para ejecutar aplicaciones web (usada por servidores como Gunicorn)
WSGI_APPLICATION = 'restaurante_config.wsgi.application'

# ==========================================
# BASE DE DATOS
# ==========================================
# Lógica dinámica: Si la variable DB_ENGINE es 'postgres', se conecta a PostgreSQL.
# De lo contrario, utiliza SQLite para desarrollo local ágil.
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

# ==========================================
# VALIDADORES DE CONTRASEÑAS
# ==========================================
# Reglas de seguridad para las contraseñas de los usuarios.
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==========================================
# INTERNACIONALIZACIÓN Y ZONA HORARIA
# ==========================================
LANGUAGE_CODE = 'es'                   # Idioma predeterminado (Español)
TIME_ZONE = 'America/Guayaquil'        # Zona horaria del restaurante
USE_I18N = True                        # Activa sistema de traducción
USE_TZ = True                          # Usa fechas conscientes de la zona horaria

# ==========================================
# ARCHIVOS ESTÁTICOS (CSS, JS, Imágenes del sistema) Y MEDIA (Subidas de usuario)
# ==========================================
STATIC_URL = "/static/"
# Carpeta donde collectstatic reunirá todos los archivos estáticos para producción
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
# Carpeta local para archivos subidos (solo se usa si no hay Cloudinary configurado)
MEDIA_ROOT = BASE_DIR / "media"

# Configuración centralizada de almacenamientos (Nuevo en Django 4.2+)
STORAGES = {
    "default": {
        # Si hay credenciales de Cloudinary, guarda los archivos media en la nube. 
        # Si no, los guarda localmente.
        "BACKEND": (
            "cloudinary_storage.storage.MediaCloudinaryStorage"
            if os.getenv("CLOUDINARY_CLOUD_NAME")
            else "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        # Whitenoise comprime y genera hashes para cachear eficientemente los estáticos
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ==========================================
# AUTENTICACIÓN Y USUARIO PERSONALIZADO
# ==========================================
# Le indica a Django que utilice nuestro modelo extendido en lugar del modelo User por defecto.
AUTH_USER_MODEL = 'usuarios.Usuario'

# ==========================================
# PROTECCIÓN CSRF Y SEGURIDAD PARA PRODUCCIÓN (RENDER)
# ==========================================
# Orígenes de confianza para evitar ataques CSRF (Cross-Site Request Forgery)
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

CSRF_USE_SESSIONS = True

# 1. Informa a Django que el servidor proxy (Render) está manejando el tráfico HTTPS.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 2. Incrementa la seguridad de las cookies en producción (cuando DEBUG=False)
if not DEBUG:
    SESSION_COOKIE_SECURE = True   # Las cookies de sesión solo viajan cifradas
    CSRF_COOKIE_SECURE = True      # Las cookies CSRF solo viajan cifradas

# ==========================================
# REDIRECCIONES DE SESIÓN
# ==========================================
LOGIN_URL = 'login'                           # URL donde se redirige si un usuario no autenticado intenta acceder a zona protegida
LOGIN_REDIRECT_URL = 'lista_usuarios'         # URL a donde va el usuario luego de un login exitoso (se puede cambiar al dashboard)
LOGOUT_REDIRECT_URL = 'login'                 # URL post-cierre de sesión

# ==========================================
# CONFIGURACIÓN DE CORREO ELECTRÓNICO
# ==========================================
# Útil para la recuperación de contraseñas durante el desarrollo. 
# Imprime los correos en la consola (terminal) en lugar de intentar enviarlos por SMTP.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ==========================================
# CREDENCIALES DE CLOUDINARY
# ==========================================
# Se leen estrictamente del entorno para proteger las API keys.
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY"),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET"),
}

# ==========================================
# CLAVE PRIMARIA POR DEFECTO
# ==========================================
# Tipo de campo autoincremental que usarán los modelos que no definan un 'id' explícitamente.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'