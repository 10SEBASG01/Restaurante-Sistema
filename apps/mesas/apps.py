from django.apps import AppConfig

class MesasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # 🔥 AQUÍ ESTÁ LA CORRECCIÓN: Agregamos "apps." al inicio
    name = 'apps.mesas'