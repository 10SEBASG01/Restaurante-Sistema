from django.apps import AppConfig

class PedidosConfig(AppConfig):
    # Configura el tipo de ID por defecto (entero de 64 bits para evitar desbordamientos)
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Define el path completo donde reside la aplicación (clave para que Django la reconozca)
    name = 'apps.pedidos'