from django.urls import path
from . import views

# CRÍTICO: El 'app_name' define el espacio de nombres (Namespace) de la aplicación.
# Evita colisiones si otras apps tienen rutas llamadas igual (ej. 'eliminar') 
# y permite invocarlas en HTML/views como 'menu:menu_gestion'.
app_name = 'menu'

urlpatterns = [
    # --- VISTA PRINCIPAL DEL PANEL ---
    path('gestion/', views.menu_gestion, name='menu_gestion'),
    
    # --- OPERACIONES CRUD DE PLATILLOS ---
    # Ruta estándar para procesar el formulario de inserción de nuevos platos
    path('crear/', views.crear_platillo, name='crear_platillo'), 
    
    # CRÍTICO: '<int:id_platillo>' actúa como convertidor de ruta dinámico. 
    # Captura la Primary Key numérica del platillo desde la URL y la transfiere a la vista.
    path('editar/<int:id_platillo>/', views.editar_platillo, name='editar_platillo'),
    path('eliminar/<int:id_platillo>/', views.eliminar_platillo, name='eliminar_platillo'),
    
    # --- OPERACIONES CRUD DE CATEGORÍAS ---
    path('categorias/nueva/', views.crear_categoria, name='crear_categoria'),
    
    # CRÍTICO: '<str:nombre_categoria>' captura una cadena de texto directamente de la URL. 
    # Útil para identificar y procesar la eliminación basada en el campo único 'nombre_categoria'.
    path('categorias/eliminar/<str:nombre_categoria>/', views.eliminar_categoria, name='eliminar_categoria'),
]