"""
Configuración principal de URLs (URLconf) del proyecto 'restaurante_config'.

Este módulo define el enrutamiento principal de la aplicación ERP, incluyendo:
- Redirección inicial y vista del dashboard principal.
- Acceso al panel de administración de Django.
- Inclusión de las rutas de los distintos módulos del sistema (usuarios, menú, etc.).
- Rutas para la gestión de sesiones (cierre de sesión con confirmación).
- Sistema completo de recuperación y cambio de contraseñas.
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

# Vistas genéricas utilizadas para redirecciones y renderizado de plantillas estáticas
from django.views.generic import RedirectView, TemplateView 
from django.conf import settings
from django.conf.urls.static import static

# Importamos las vistas globales del proyecto (núcleo del sistema)
from restaurante_config import views as core_views

urlpatterns = [
    # ==========================================
    # RUTAS PRINCIPALES Y DE NAVEGACIÓN GENERAL
    # ==========================================
    
    # Ruta raíz: Redirige automáticamente al Dashboard al acceder a la URL base.
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False), name='index'),
    
    # Dashboard principal: Vista exclusiva centralizada para la interfaz (diseño Figma).
    path('dashboard/', core_views.dashboard_view, name='dashboard'),

    # Panel de administración predeterminado de Django
    path('admin/', admin.site.urls),
    
    # ==========================================
    # INCLUSIÓN DE MÓDULOS DEL SISTEMA ERP
    # ==========================================
    
    # Gestión de cuentas y perfiles de usuario
    path('usuarios/', include('apps.usuarios.urls')), 
    
    # Gestión de platillos, categorías y disponibilidad
    path('menu/', include('apps.menu.urls')),
    
    # Sistema de reservas de clientes
    path('reservas/', include('apps.reservas.urls')),
    
    # Gestión del estado y distribución de las mesas
    path('mesas/', include('apps.mesas.urls')),
    
    # Toma de comandas y seguimiento de pedidos
    path('pedidos/', include('apps.pedidos.urls')),
    
    # Pantallas y control de flujo para el área de cocina
    path('cocina/', include('apps.cocina.urls')),
    
    # Módulo para la generación de estadísticas y reportes
    path('reportes/', include('apps.reportes.urls')),
    
    # Generación de cobros, tickets y facturas
    path('facturacion/', include('apps.facturacion.urls')),

    # Vistas destinadas al cliente final (menú digital, reservas web, etc.)
    path('publico/', include('apps.publico.urls')),
    
    # Módulo de auditoría para registrar las acciones y cambios en el sistema
    path('auditoria/', include('apps.auditoria.urls')),
    
    # ==========================================
    # GESTIÓN DE SESIONES Y SEGURIDAD
    # ==========================================
    
    # Pantalla intermedia de confirmación antes de cerrar la sesión
    path('confirmar-salida/', TemplateView.as_view(template_name='errors/confirmar_cierre.html'), name='confirmar_logout'),
    
    # Acción de cierre de sesión (redirige al login una vez completado)
    path('logout/', auth_views.LogoutView.as_view(next_page='/usuarios/login/'), name='logout'),
    
    # Cambio de contraseña para el usuario autenticado (con registro en auditoría)
    path('mi-password/', core_views.cambiar_mi_password_view, name='cambiar_mi_password'),
    
    # ==========================================
    # SISTEMA DE RECUPERACIÓN DE CONTRASEÑAS
    # ==========================================
    
    # 1. Formulario inicial para solicitar restablecimiento por correo
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='usuarios/password_reset.html'), name='password_reset'),
    
    # 2. Mensaje de confirmación de que el correo ha sido enviado
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='usuarios/password_reset_done.html'), name='password_reset_done'),
    
    # 3. Enlace con token (enviado al correo) para ingresar la nueva contraseña
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='usuarios/password_reset_confirm.html'), name='password_reset_confirm'),
    
    # 4. Mensaje de éxito indicando que la contraseña fue cambiada exitosamente
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='usuarios/password_reset_complete.html'), name='password_reset_complete'),
]

# ==========================================
# CONFIGURACIÓN DE ARCHIVOS MULTIMEDIA (MEDIA)
# ==========================================
# Permite servir archivos subidos por los usuarios (imágenes, documentos) durante el desarrollo local
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)