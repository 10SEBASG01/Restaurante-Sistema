from django.apps import AppConfig

#Se define la configuración de la aplicación de auditoría, 
#que es responsable de registrar todas las acciones críticas 
#realizadas por los usuarios dentro del ERP "Sabor & Arte".
class AuditoriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.auditoria'
