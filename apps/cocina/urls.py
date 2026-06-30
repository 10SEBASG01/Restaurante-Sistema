from django.urls import path
from . import views

app_name = 'cocina'

urlpatterns = [
    path('tablero/', views.tablero_cocina, name='tablero_cocina'),
    path('api/comandas/', views.api_comandas_activas, name='api_comandas'),
    path('api/comandas/avanzar/', views.api_avanzar_comanda, name='api_avanzar'),
]