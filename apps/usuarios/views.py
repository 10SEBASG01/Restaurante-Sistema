from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission
from django.contrib.auth import logout
from django.db.models import Q
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages

# 🎯 IMPORTAMOS AUDITORÍA Y CONFIGURACIÓN
from apps.auditoria.models import Auditoria
from apps.facturacion.models import ConfiguracionFacturacion

from .models import Usuario
from .forms import CustomUserCreationForm, UsuarioEditForm

# =====================================================================
# 🛡️ 1. GUARDIÁN DE SEGURIDAD UNIVERSAL (MIDDLEWARE A MEDIDA)
# =====================================================================
def requiere_permiso(nombre_permiso):
    """
    🎯 DECORADOR DE AUTORIZACIÓN
    
    Actúa como un guardián antes de ejecutar cualquier vista. Verifica directamente 
    en la base de datos si el usuario autenticado posee el permiso modular requerido.
    Previene accesos no autorizados a URLs sensibles.
    
    Reglas de negocio:
    - Administradores y Superusuarios tienen "pase libre" (Bypass).
    - Si el usuario carece del permiso, es redirigido a la pantalla 403 (Acceso Denegado).
    """
    def decorador(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            usuario = request.user
            
            if usuario.is_authenticated:
                # 1. Pase libre para roles de máxima jerarquía
                if usuario.is_superuser or usuario.rol == 'administrador':
                    return view_func(request, *args, **kwargs)
                
                # 2. Verificación estricta del permiso en la matriz de la BD
                tiene_permiso = usuario.user_permissions.filter(codename=nombre_permiso).exists()
                
                if tiene_permiso:
                    return view_func(request, *args, **kwargs)
                    
            # 3. Candado rojo estándar (Bomba nuclear desactivada)
            return render(request, 'usuarios/acceso_denegado.html', status=403)
            
        return _wrapped_view
    return decorador


# =====================================================================
# 🔐 2. AUTENTICACIÓN Y ENRUTAMIENTO INTELIGENTE
# =====================================================================
@method_decorator(csrf_exempt, name='dispatch')
class CustomLoginView(LoginView):
    """
    🎯 VISTA DE INICIO DE SESIÓN
    
    Gestiona el acceso al ERP. Una vez validadas las credenciales, redirige al 
    usuario a su panel de trabajo correspondiente basándose en su rol y permisos 
    para optimizar su flujo de trabajo.
    """
    template_name = 'usuarios/login.html'
    
    def get_context_data(self, **kwargs):
        # Inyecta los datos corporativos (logo, nombre) al formulario de login
        context = super().get_context_data(**kwargs)
        context['config'] = ConfiguracionFacturacion.objects.first()
        return context
    
    def get_success_url(self):
        usuario = self.request.user
        
        # 1. Gerencia: Acceso directo a métricas (Dashboard)
        if usuario.is_superuser or usuario.rol == 'administrador':
            return reverse_lazy('dashboard') 
            
        # 2. Portal Público: Acceso a reservas para los clientes externos
        if usuario.rol == 'cliente':
            return reverse_lazy('reservas') 
            
        # 3. Personal Operativo: Enrutamiento según capacidades (Permisos)
        if usuario.user_permissions.filter(codename='modulo_dashboard').exists():
            return reverse_lazy('dashboard')
            
        if usuario.user_permissions.filter(codename='modulo_mesas').exists():
            return reverse_lazy('estado_mesas')
        
        # Ruta por defecto (Fallo seguro)
        return reverse_lazy('estado_mesas')


def cerrar_sesion(request):
    """Destruye la sesión activa de forma segura y expulsa al usuario al Login."""
    logout(request)
    return redirect('login')


# =====================================================================
# 👥 3. CRUD DE RECURSOS HUMANOS (MÓDULO USUARIOS)
# =====================================================================
@login_required
@requiere_permiso('modulo_usuarios')
def lista_usuarios(request):
    """
    🎯 PANEL DE CONTROL DE PERSONAL
    
    Renderiza el listado de empleados registrados. Filtra automáticamente las 
    cuentas "anonimizadas" y a los clientes públicos para mantener limpia la 
    vista de Recursos Humanos. Incluye motor de búsqueda multicampo.
    """
    # Excluye clientes y cuentas dadas de baja lógicamente
    usuarios = Usuario.objects.exclude(rol='cliente').exclude(es_anonimo=True)
    
    # Captura de parámetros GET para los filtros de la interfaz
    query = request.GET.get('q', '').strip()
    rol_filter = request.GET.get('rol', 'Todos')
    estado_filter = request.GET.get('estado', 'Todos')

    # Búsqueda tipo "LIKE" en nombre de usuario, nombre o apellido
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        )
        
    # Aplicación de filtros desplegables
    if rol_filter != 'Todos':
        usuarios = usuarios.filter(rol=rol_filter)
    if estado_filter == 'Activo':
        usuarios = usuarios.filter(is_active=True)
    elif estado_filter == 'Inactivo':
        usuarios = usuarios.filter(is_active=False)

    context = {
        'usuarios': usuarios,
        'total_usuarios': usuarios.count(),
        'usuarios_activos': usuarios.filter(is_active=True).count(),
        'query': query,
        'rol_filter': rol_filter,
        'estado_filter': estado_filter,
        'roles_disponibles': [r for r in Usuario.ROLES if r[0] != 'cliente']
    }
    return render(request, 'usuarios/lista_usuarios.html', context)


@login_required
@requiere_permiso('modulo_usuarios')
def crear_usuario(request):
    """Crea una nueva cuenta de empleado y registra la acción en la Auditoría."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            nuevo_usuario = form.save()
            
            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='usuarios',
                accion='Usuario Creado',
                detalle=f"Registró al empleado: {nuevo_usuario.username} con rol de {nuevo_usuario.get_rol_display()}."
            )
            return redirect('lista_usuarios')
    else:
        form = CustomUserCreationForm()
    return render(request, 'usuarios/crear_usuario.html', {'form': form})


@login_required
@requiere_permiso('modulo_usuarios')
def editar_usuario(request, pk):
    """
    Modifica el perfil de un empleado existente. 
    Previene que un administrador se edite o se bloquee a sí mismo accidentalmente.
    """
    usuario = get_object_or_404(Usuario, pk=pk)
    rol_anterior = usuario.get_rol_display()
    
    # Candado: No permite auto-edición en esta vista
    if request.user == usuario:
        return render(request, 'usuarios/acceso_denegado.html', {
            'mensaje_personalizado': 'No puedes editar tus propios permisos desde esta vista por seguridad.'
        }, status=403)
            
    if request.method == 'POST':
        form = UsuarioEditForm(request.POST, instance=usuario)
        if form.is_valid():
            usuario_editado = form.save()
            
            # Rastrea si hubo un ascenso/descenso de rol para la bitácora
            detalle_audit = f"Actualizó los datos del empleado: {usuario_editado.username}."
            if rol_anterior != usuario_editado.get_rol_display():
                detalle_audit += f" (Cambió su rol de {rol_anterior} a {usuario_editado.get_rol_display()})."
                
            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='usuarios',
                accion='Usuario Editado',
                detalle=detalle_audit
            )
            return redirect('lista_usuarios')
    else:
        form = UsuarioEditForm(instance=usuario)
    return render(request, 'usuarios/editar_usuario.html', {'form': form, 'usuario_editado': usuario})


@login_required
@requiere_permiso('modulo_usuarios')
def eliminar_usuario(request, pk):
    """
    🎯 BORRADO LÓGICO / ANONIMIZACIÓN (SOFT DELETE)
    
    En lugar de hacer un `delete()` que destruiría las facturas o pedidos procesados 
    por este empleado, desactiva la cuenta y muta sus datos de acceso para liberar
    su correo electrónico e impedir que vuelva a iniciar sesión.
    """
    usuario = get_object_or_404(Usuario, pk=pk)
    
    if request.method == 'POST':
        username_original = usuario.username
        
        # Desactiva la sesión, destruye la contraseña y lo marca como anónimo
        usuario.is_active = False
        usuario.set_unusable_password() 
        usuario.es_anonimo = True
        
        # Muta los datos únicos para permitir que el correo se reuse en un futuro
        usuario.username = f"{username_original}_eliminado_{usuario.id}"
        usuario.email = f"eliminado_{usuario.id}_{usuario.email}"
        
        usuario.save()
        
        Auditoria.objects.create(
            id_usuario=request.user,
            modulo='usuarios',
            accion='Usuario Eliminado',
            detalle=f"Eliminó del panel al empleado: {username_original}."
        )
        return redirect('lista_usuarios')
        
    return render(request, 'usuarios/eliminar_usuario.html', {'usuario_eliminado': usuario})


# =====================================================================
# 🎛️ 4. GESTIÓN AVANZADA DE PERMISOS Y SEGURIDAD
# =====================================================================
@login_required
@requiere_permiso('modulo_usuarios')
def asignar_permisos(request, pk):
    """
    🎯 MATRIZ DE AUTORIZACIONES (ACL)
    
    Permite marcar qué módulos específicos del ERP puede visualizar u operar
    un empleado. Los permisos se extraen dinámicamente de la clase Meta del modelo.
    """
    usuario = get_object_or_404(Usuario, pk=pk)
    # Filtra solo los permisos personalizados que creamos (empiezan con modulo_)
    permisos = Permission.objects.filter(content_type__app_label='usuarios', codename__startswith='modulo_')
    
    if request.method == 'POST':
        # Captura todos los checkboxes marcados y actualiza la relación N:M
        permisos_ids = request.POST.getlist('permisos')
        usuario.user_permissions.set(permisos_ids)
        
        Auditoria.objects.create(
            id_usuario=request.user,
            modulo='usuarios',
            accion='Permisos Modificados',
            detalle=f"Actualizó la matriz de permisos para el empleado: {usuario.username}."
        )
        return redirect('lista_usuarios')
        
    usuario_permisos_ids = list(usuario.user_permissions.values_list('id', flat=True))
        
    return render(request, 'usuarios/permisos_usuario.html', {
        'usuario': usuario, 
        'permisos': permisos,
        'usuario_permisos_ids': usuario_permisos_ids
    })


@login_required
@requiere_permiso('modulo_usuarios')
def cambiar_password_admin(request, pk):
    """
    Permite al administrador resetear o cambiar la contraseña de un empleado
    en caso de pérdida o compromiso de la cuenta. 
    Requiere validación de la propia contraseña del administrador por seguridad.
    """
    usuario_objetivo = get_object_or_404(Usuario, pk=pk)
    
    if request.method == 'POST':
        form = PasswordChangeForm(user=usuario_objetivo, data=request.POST)
        if form.is_valid():
            form.save()
            
            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='usuarios',
                accion='Contraseña Modificada',
                detalle=f"Se modificó la contraseña del usuario {usuario_objetivo.username} tras validar su clave actual."
            )
            
            messages.success(request, f'La contraseña de {usuario_objetivo.username} se ha actualizado con éxito.')
            return redirect('lista_usuarios')
    else:
        form = PasswordChangeForm(user=usuario_objetivo)
        
        # Inyección de estilos CSS para mantener consistencia visual
        for field_name, field in form.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'style': 'width: 100%; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 15px;'
            })
            
    return render(request, 'usuarios/cambiar_password.html', {
        'form': form, 
        'usuario_objetivo': usuario_objetivo
    })