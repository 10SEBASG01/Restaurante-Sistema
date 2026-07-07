from django.urls import path
from .views import (
    CustomLoginView, 
    cerrar_sesion,
    lista_usuarios, 
    crear_usuario, 
    editar_usuario, 
    eliminar_usuario, 
    asignar_permisos,
    cambiar_password_admin
)

urlpatterns = [
    path('login/', CustomLoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', cerrar_sesion, name='logout'),
    
    # Rutas internas administrativas
    path('lista/', lista_usuarios, name='lista_usuarios'),
    path('crear/', crear_usuario, name='crear_usuario'),
    path('editar/<int:pk>/', editar_usuario, name='editar_usuario'),
    path('eliminar/<int:pk>/', eliminar_usuario, name='eliminar_usuario'),
    path('permisos/<int:pk>/', asignar_permisos, name='asignar_permisos'),
    path('<int:pk>/cambiar-password/', cambiar_password_admin, name='cambiar_password_admin'),
]