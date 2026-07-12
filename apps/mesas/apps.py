from django.apps import AppConfig

class MesasConfig(AppConfig):
    # Tipo de dato por defecto para las llaves primarias (IDs autoincrementales)
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Ruta completa del módulo dentro de la subcarpeta 'apps'
    name = 'apps.mesas'