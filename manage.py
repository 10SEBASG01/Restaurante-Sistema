#!/usr/bin/env python
"""Utilidad de línea de comandos de Django para tareas administrativas."""
import os
import sys

def main():
    """Ejecuta las tareas administrativas."""
    
    # Aquí le decimos a Django dónde encontrar la configuración principal de tu sistema.
    # En este caso, apunta directamente a los settings de tu proyecto (restaurante_config).
    # Sin esto, Django no sabría dónde están tus apps, tus bases de datos o tus contraseñas.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurante_config.settings')
    
    try:
        # Intenta importar la herramienta interna de Django que se encarga de 
        # leer y ejecutar los comandos que escribes en la terminal.
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Si Django no se puede importar (casi siempre porque se te olvidó 
        # activar el entorno virtual antes de trabajar), te lanza este error 
        # amigable para avisarte qué pasó.
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
        
    # Si la importación fue exitosa, toma las palabras que escribiste en la terminal 
    # (por ejemplo, ['manage.py', 'runserver']) y ejecuta esa acción específica.
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    # Este es el punto de entrada de Python. Le dice al sistema que, si estás ejecutando 
    # este archivo directamente desde la terminal, debe arrancar la función main() de arriba.
    main()