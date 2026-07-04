from django.urls import path
from . import views

app_name = 'auditoria'

urlpatterns = [
    # Carga la lista de auditorías directamente al entrar a /auditoria/
    path('', views.auditoria_lista, name='auditoria_lista'),
]