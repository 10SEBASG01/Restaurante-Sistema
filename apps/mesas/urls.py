from django.urls import path
from .views import (
    lista_mesas, 
    cambiar_estado_mesa, 
    asignar_mesero_mesa, 
    crear_mesa, 
    editar_mesa, 
    eliminar_mesa,
    listar_zonas,  
    crear_zona,    
    eliminar_zona, 
)

urlpatterns = [
    # =========================================================================
    # --- BLOQUE OPERATIVO: GESTIÓN DE MESAS ---
    # =========================================================================
    path('estado/', lista_mesas, name='estado_mesas'),
    path('crear/', crear_mesa, name='crear_mesa'),
    
    # LÍNEAS IMPORTANTES: Parámetros dinámicos (<int:pk>) para acciones directas en mesas
    path('cambiar-estado/<int:pk>/', cambiar_estado_mesa, name='cambiar_estado_mesa'),
    path('asignar-mesero/<int:pk>/', asignar_mesero_mesa, name='asignar_mesero_mesa'),
    path('editar/<int:pk>/', editar_mesa, name='editar_mesa'),
    path('eliminar/<int:pk>/', eliminar_mesa, name='eliminar_mesa'),
    
    # =========================================================================
    # --- BLOQUE COMPLEMENTARIO: GESTIÓN DE ZONAS ---
    # =========================================================================
    path('zonas/', listar_zonas, name='listar_zonas'),
    path('zonas/crear/', crear_zona, name='crear_zona'),
    
    # LÍNEA IMPORTANTE: Identificador numérico obligatorio para ejecutar el borrado de la zona
    path('zonas/eliminar/<int:pk>/', eliminar_zona, name='eliminar_zona'),
]