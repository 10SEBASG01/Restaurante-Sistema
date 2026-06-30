from django.urls import path

from . import views

app_name = 'reservas'

urlpatterns = [

    path(
        '',
        views.lista_reservas,
        name='lista'
    ),

    path(
        'crear/',
        views.crear_reserva,
        name='crear'
    ),

    path(
        'editar/<int:pk>/',
        views.editar_reserva,
        name='editar'
    ),

    path(
        'eliminar/<int:pk>/',
        views.eliminar_reserva,
        name='eliminar'
    ),
    path(
        'observacion/<int:id>/', 
        views.observacion_reserva, 
        name='observacion'
    ),
]