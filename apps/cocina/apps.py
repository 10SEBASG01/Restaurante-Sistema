from django.apps import AppConfig

class CocinaConfig(AppConfig):
    # Configura el tipo de ID autoincremental para las tablas (64 bits)
    default_auto_field = 'django.db.models.BigAutoField'
    # Nombre oficial del paquete de la aplicación
    name = 'apps.cocina'