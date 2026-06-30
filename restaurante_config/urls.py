from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView 
from django.conf import settings
from django.conf.urls.static import static

# 👇 CORRECCIÓN: Importamos las vistas globales de tu proyecto (donde está el nuevo dashboard)
from restaurante_config import views as core_views

urlpatterns = [
    # LA RUTA RAÍZ: Ahora los manda al Dashboard por defecto.
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False), name='index'),
    
    # 📊 CORRECCIÓN: Ahora usamos la vista "dashboard_view" exclusiva para el diseño de Figma
    path('dashboard/', core_views.dashboard_view, name='dashboard'),

    path('admin/', admin.site.urls),
    
    # --- MÓDULOS DEL SISTEMA ERP ---
    path('usuarios/', include('apps.usuarios.urls')), 
    path('menu/', include('apps.menu.urls')),
    path('reservas/', include('apps.reservas.urls')),
    path('mesas/', include('apps.mesas.urls')),
    path('pedidos/', include('apps.pedidos.urls')),
    path('cocina/', include('apps.cocina.urls')),
    
    # 📊 MÓDULO DE REPORTES 
    path('reportes/', include('apps.reportes.urls')),
    
    path('facturacion/', include('apps.facturacion.urls')),

    path('publico/', include('apps.publico.urls')),
    
    # 🔥 AQUÍ AGREGAMOS EL MÓDULO DE AUDITORÍA (NUEVO)
    path('auditoria/', include('apps.auditoria.urls')),
    
    # --- SISTEMA PROFESIONAL DE RECUPERACIÓN DE CONTRASEÑAS ---
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='usuarios/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='usuarios/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='usuarios/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='usuarios/password_reset_complete.html'), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)