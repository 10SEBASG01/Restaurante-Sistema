from django.contrib import admin
from .models import Reserva


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):

    list_display = (
        'codigo',
        'cliente',
        'fecha',
        'hora',
        'personas',
        'mesa',
        'estado'
    )

    search_fields = (
        'codigo',
        'cliente',
        'telefono'
    )

    list_filter = (
        'estado',
        'fecha'
    )