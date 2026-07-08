from django.urls import path
from . import views

app_name = 'pedidos'

urlpatterns = [
    # Ruta para ver la pantalla del menú de pedidos
    path('crear/', views.pedido_pantalla, name='pedido_pantalla'),
    
    # Ruta tipo API para recibir el JSON del carrito
    path('guardar-api/', views.guardar_pedido_api, name='guardar_pedido_api'),

    path('mis-pedidos/', views.mis_pedidos_mesero, name='mis_pedidos_mesero'),

    # Ruta tipo API para eliminar un pedido pendiente
    path('eliminar-api/<int:id_pedido>/', views.eliminar_pedido_api, name='eliminar_pedido_api'),
]