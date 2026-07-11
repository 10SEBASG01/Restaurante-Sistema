from django.contrib import admin
from .models import Reserva

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    # 🎯 CAMBIO AQUÍ: Quitamos 'cliente' y ponemos 'nombres', 'apellidos'
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
    
    # 🎯 CAMBIO AQUÍ: También en la barra de búsqueda del admin
    search_fields = (
        'codigo', 
        'nombres', 
        'apellidos', 
        'cedula', 
        'telefono'
    )
    
    list_filter = (
        'estado', 
        'fecha', 
        'mesa'
    )