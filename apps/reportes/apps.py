from django.apps import AppConfig

#Se define la configuración de la aplicación de reportes, 
#que es responsable de generar informes y reportes detallados
class ReportesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reportes'

from django.apps import AppConfig
class ReportesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    
    # 🔥 EL ARREGLO ESTÁ AQUÍ: Añadir 'apps.' antes del nombre
    name = 'apps.reportes'