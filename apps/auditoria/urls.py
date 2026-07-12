from django.urls import path
from . import views

app_name = 'auditoria'
# Se define el namespace 'auditoria' para evitar conflictos de nombres en las URLs de la aplicación.
urlpatterns = [
    # Carga la lista de auditorías directamente al entrar a /auditoria/
    path('', views.auditoria_lista, name='auditoria_lista'),
]