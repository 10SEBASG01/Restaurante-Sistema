from django.apps import AppConfig


class ReportesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reportes'
from django.apps import AppConfig

class ReportesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    
    # 🔥 EL ARREGLO ESTÁ AQUÍ: Añadir 'apps.' antes del nombre
    name = 'apps.reportes'