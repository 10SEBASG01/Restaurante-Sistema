# Importa la clase base para la configuración de aplicaciones en Django
from django.apps import AppConfig

class FacturacionConfig(AppConfig):
    # LINEA IMPORTANTE: Configura el tipo de dato por defecto (BigAutoincrement) para las Llaves Primarias (IDs) de los modelos
    default_auto_field = 'django.db.models.BigAutoField'
    
    # LINEA IMPORTANTE: Define la ruta completa de importación del módulo dentro del proyecto (subcarpeta apps)
    name = 'apps.facturacion'