from django.apps import AppConfig
#Se define la configuración de la aplicación "usuarios" dentro del proyecto Django. 
class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.usuarios'  # <-- ¡Esta es la línea clave que debes modificar!