"""
Enrutamiento de URLs para la aplicación interna de 'reservas'.

Define los endpoints utilizados por el personal y los administradores 
para gestionar el CRUD (Crear, Leer, Actualizar, Eliminar) completo 
de las reservas a través del panel de control del restaurante.
"""

from django.urls import path
from . import views

# Espacio de nombres (namespace) para evitar colisiones de nombres de rutas 
# con otras aplicaciones del sistema (ej. url 'reservas:lista')
app_name = 'reservas'

urlpatterns = [
    # =====================================
    # LISTADO GENERAL
    # =====================================
    # URL: /reservas/
    # Muestra la tabla principal con todas las reservas registradas
    path(
        '',
        views.lista_reservas,
        name='lista'
    ),

    # =====================================
    # CREACIÓN DE RESERVAS (ADMINISTRATIVA)
    # =====================================
    # URL: /reservas/crear/
    # Renderiza y procesa el formulario interno para agendar manualmente
    path(
        'crear/',
        views.crear_reserva,
        name='crear'
    ),

    # =====================================
    # EDICIÓN DE RESERVAS
    # =====================================
    # URL: /reservas/editar/<id>/
    # Permite modificar datos o cambiar el estado (ej. PENDIENTE a CONFIRMADA)
    path(
        'editar/<int:pk>/',
        views.editar_reserva,
        name='editar'
    ),

    # =====================================
    # ELIMINACIÓN DE RESERVAS
    # =====================================
    # URL: /reservas/eliminar/<id>/
    # Borrado físico o lógico del registro de agendamiento
    path(
        'eliminar/<int:pk>/',
        views.eliminar_reserva,
        name='eliminar'
    ),
    
    # =====================================
    # DETALLES / OBSERVACIONES
    # =====================================
    # URL: /reservas/observacion/<id>/
    # Modal o vista de solo lectura para ver notas especiales dejadas por el cliente
    path(
        'observacion/<int:id>/', 
        views.observacion_reserva, 
        name='observacion'
    ),
]