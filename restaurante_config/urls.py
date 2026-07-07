from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
# 👇 CORRECCIÓN: Añadido TemplateView aquí para evitar el error de definición
from django.views.generic import RedirectView, TemplateView 
from django.conf import settings
from django.conf.urls.static import static

# Importamos las vistas globales del proyecto
from restaurante_config import views as core_views

urlpatterns = [
    # LA RUTA RAÍZ: Manda al Dashboard por defecto.
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False), name='index'),
    
    # Vista "dashboard_view" exclusiva para el diseño de Figma
    path('dashboard/', core_views.dashboard_view, name='dashboard'),

    path('admin/', admin.site.urls),
    
    # --- MÓDULOS DEL SISTEMA ERP ---
    path('usuarios/', include('apps.usuarios.urls')), 
    path('menu/', include('apps.menu.urls')),
    path('reservas/', include('apps.reservas.urls')),
    path('mesas/', include('apps.mesas.urls')),
    path('pedidos/', include('apps.pedidos.urls')),
    path('cocina/', include('apps.cocina.urls')),
    
    # MÓDULO DE REPORTES 
    path('reportes/', include('apps.reportes.urls')),
    
    path('facturacion/', include('apps.facturacion.urls')),

    path('publico/', include('apps.publico.urls')),
    
    # MÓDULO DE AUDITORÍA
    path('auditoria/', include('apps.auditoria.urls')),
    
    # 👇 NUEVAS RUTAS PARA EL CIERRE DE SESIÓN CON CONFIRMACIÓN
    path('confirmar-salida/', TemplateView.as_view(template_name='errors/confirmar_cierre.html'), name='confirmar_logout'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/usuarios/login/'), name='logout'),
    
    # 💡 NUEVA RUTA: CAMBIO DE CONTRASEÑA (Apunta a la view personalizada para auditoría)
    path('mi-password/', core_views.cambiar_mi_password_view, name='cambiar_mi_password'),
    
    # --- SISTEMA PROFESIONAL DE RECUPERACIÓN DE CONTRASEÑAS ---
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='usuarios/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='usuarios/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='usuarios/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='usuarios/password_reset_complete.html'), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)