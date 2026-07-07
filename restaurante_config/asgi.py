"""
Configuración ASGI para el proyecto restaurante_config.
Expone la aplicación ASGI para servidores web asíncronos.
"""

import os
from django.core.asgi import get_asgi_application

# 1. Configuración del entorno
# Indicamos a Django dónde encontrar los ajustes principales del proyecto.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurante_config.settings')

# 2. Inicialización de la aplicación
# Creamos la instancia ASGI que los servidores usarán para recibir las peticiones.
application = get_asgi_application()