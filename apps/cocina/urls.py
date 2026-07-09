from django.urls import path
from . import views

# Namespace para organizar las rutas de la app 'cocina'
app_name = 'cocina'

urlpatterns = [
    # Vista principal: Tablero donde el staff visualiza las comandas
    path('tablero/', views.tablero_cocina, name='tablero_cocina'),

    # API: Endpoint para consultar las comandas que están pendientes
    path('api/comandas/', views.api_comandas_activas, name='api_comandas'),

    # API: Endpoint para avanzar el estado de una comanda (ej. de pendiente a lista)
    path('api/comandas/avanzar/', views.api_avanzar_comanda, name='api_avanzar'),
]