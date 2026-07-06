"""
Configuración WSGI para el proyecto restaurante_config.

Expone el invocable WSGI como una variable a nivel de módulo llamada ``application``.
"""

import os
# Importa la función interna de Django encargada de crear la aplicación WSGI.
from django.core.wsgi import get_wsgi_application

# Al igual que en manage.py, esto le indica al servidor dónde encontrar 
# las configuraciones principales de tu sistema (restaurante_config).
# Es fundamental para que el servidor de producción sepa cómo conectar
# la base de datos, y dónde están tus módulos de cocina y facturación.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurante_config.settings')

# Aquí se inicializa la aplicación. 
# Esta variable 'application' es la que Gunicorn va a tomar y mantener corriendo 
# en el servidor para que tu sistema web pueda recibir tráfico de usuarios reales.
application = get_wsgi_application()