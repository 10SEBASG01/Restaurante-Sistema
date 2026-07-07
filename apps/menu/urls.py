from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('gestion/', views.menu_gestion, name='menu_gestion'),
    path('crear/', views.crear_platillo, name='crear_platillo'), # Tu ruta original de creación
    path('editar/<int:id_platillo>/', views.editar_platillo, name='editar_platillo'),
    path('eliminar/<int:id_platillo>/', views.eliminar_platillo, name='eliminar_platillo'),
    path('categorias/nueva/', views.crear_categoria, name='crear_categoria'),
    # ... tus otras rutas ...
    path('categorias/eliminar/<str:nombre_categoria>/', views.eliminar_categoria, name='eliminar_categoria'),
]