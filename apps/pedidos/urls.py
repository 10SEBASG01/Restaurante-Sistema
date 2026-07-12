from django.urls import path
from . import views

# Definición del espacio de nombres para las plantillas (namespace)
app_name = 'pedidos'

urlpatterns = [
    # Vista: Interfaz principal para la creación de pedidos
    path('crear/', views.pedido_pantalla, name='pedido_pantalla'),
    
    # Endpoint API: Procesa el guardado del carrito mediante JSON
    path('guardar-api/', views.guardar_pedido_api, name='guardar_pedido_api'),

    # Vista: Listado de pedidos asociados al mesero en sesión
    path('mis-pedidos/', views.mis_pedidos_mesero, name='mis_pedidos_mesero'),

    # Endpoint API: Eliminación de un pedido específico por ID
    path('eliminar-api/<int:id_pedido>/', views.eliminar_pedido_api, name='eliminar_pedido_api'),
]