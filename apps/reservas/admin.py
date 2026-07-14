"""
Configuración del panel de administración (Django Admin) para Reservas.

Permite a los superusuarios y personal autorizado gestionar directamente 
los registros de la base de datos a través de la interfaz nativa de Django.
"""

from django.contrib import admin
from .models import Reserva

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    """
    Personalización de la vista de lista y detalle para el modelo Reserva 
    en el panel administrativo.
    """
    
    # Columnas que se mostrarán en la tabla principal del listado de reservas
    list_display = (
        'codigo', 
        'nombres', 
        'apellidos', 
        'cedula', 
        'fecha', 
        'hora', 
        'mesa', 
        'estado'
    )
    
    # Campos por los cuales el administrador puede realizar búsquedas de texto
    search_fields = (
        'codigo', 
        'nombres', 
        'apellidos', 
        'cedula', 
        'telefono'
    )
    
    # Filtros laterales para segmentar la información rápidamente
    list_filter = (
        'estado', 
        'fecha', 
        'mesa'
    )