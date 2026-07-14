"""
Configuración de la aplicación 'publico'.

Este módulo registra la aplicación dentro del proyecto Django y define 
configuraciones predeterminadas, como el tipo de campo autoincremental a usar.
"""

from django.apps import AppConfig

class PublicoConfig(AppConfig):
    """
    Clase de configuración principal para el módulo de vistas públicas.
    Maneja el portal orientado al cliente (menú digital, inicio y reservas web).
    """
    # Define el tipo de clave primaria por defecto para los modelos de esta app
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Ruta de importación de la aplicación
    name = 'apps.publico'