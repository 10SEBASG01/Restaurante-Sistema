from django.urls import path

from . import views

app_name = 'publico'

urlpatterns = [

    # =====================================
    # PÁGINA PRINCIPAL
    # =====================================

    path('inicio/', views.inicio_publico, name='inicio'),

    # =====================================
    # MENÚ PÚBLICO
    # =====================================

    path(
        'menu/',
        views.menu_publico,
        name='menu_publico'
    ),

    # =====================================
    # RESERVA PÚBLICA
    # =====================================

    path(
        'reservar/',
        views.reserva_publica,
        name='reserva_publica'
    ),

]