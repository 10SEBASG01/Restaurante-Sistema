from django.urls import path
from .views import (
    lista_mesas, 
    cambiar_estado_mesa, 
    asignar_mesero_mesa, 
    crear_mesa, 
    editar_mesa, 
    eliminar_mesa,
    listar_zonas,   # 🔥 AGREGADO
    crear_zona,     # 🔥 AGREGADO
    eliminar_zona,  # 🔥 AGREGADO
)

urlpatterns = [
    path('estado/', lista_mesas, name='estado_mesas'),
    path('crear/', crear_mesa, name='crear_mesa'),
    path('cambiar-estado/<int:pk>/', cambiar_estado_mesa, name='cambiar_estado_mesa'),
    path('asignar-mesero/<int:pk>/', asignar_mesero_mesa, name='asignar_mesero_mesa'),
    path('editar/<int:pk>/', editar_mesa, name='editar_mesa'),
    path('eliminar/<int:pk>/', eliminar_mesa, name='eliminar_mesa'),
    
    # 🔥 NUEVAS RUTAS PARA EL MÓDULO INDEPENDIENTE DE ZONAS
    path('zonas/', listar_zonas, name='listar_zonas'),
    path('zonas/crear/', crear_zona, name='crear_zona'),
    path('zonas/eliminar/<int:pk>/', eliminar_zona, name='eliminar_zona'),
]