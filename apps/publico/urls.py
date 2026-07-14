"""
Enrutamiento de URLs para la aplicación 'publico'.

Define los endpoints accesibles para clientes no autenticados, 
incluyendo la página de aterrizaje (landing page), el menú digital y el portal de reservas.
"""

from django.urls import path
from . import views

# Espacio de nombres para las URLs de esta aplicación
app_name = 'publico'

urlpatterns = [
    # =====================================
    # PÁGINA PRINCIPAL (Landing Page)
    # =====================================
    # URL: /publico/inicio/
    path('inicio/', views.inicio_publico, name='inicio'),

    # =====================================
    # MENÚ PÚBLICO (Catálogo digital)
    # =====================================
    # URL: /publico/menu/
    path('menu/', views.menu_publico, name='menu_publico'),

    # =====================================
    # RESERVA PÚBLICA (Agendamiento web)
    # =====================================
    # URL: /publico/reservar/
    path('reservar/', views.reserva_publica, name='reserva_publica'),
]