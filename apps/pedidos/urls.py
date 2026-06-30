from django.urls import path
from . import views

app_name = 'pedidos'

urlpatterns = [
    # Ruta para ver la pantalla del menú de pedidos
    path('crear/', views.pedido_pantalla, name='pedido_pantalla'),
    
    # Ruta tipo API para recibir el JSON del carrito
    path('guardar-api/', views.guardar_pedido_api, name='guardar_pedido_api'),
]