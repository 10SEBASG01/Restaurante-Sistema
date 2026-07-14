"""
Configuración principal de la aplicación 'reservas'.

Registra la app en el ecosistema del proyecto e inicializa sus parámetros básicos.
"""

from django.apps import AppConfig

class ReservasConfig(AppConfig):
    """
    Clase de configuración para el módulo de gestión de reservas.
    """
    # Define la estrategia de generación de IDs automáticos (enteros grandes de 64 bits)
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Ruta completa del módulo en la estructura del proyecto
    name = 'apps.reservas'