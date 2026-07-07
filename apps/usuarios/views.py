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

# 🎯 IMPORTAMOS AUDITORÍA
from apps.auditoria.models import Auditoria

from .models import Usuario
from .forms import CustomUserCreationForm, UsuarioEditForm

# =====================================================================
# 🛡️ GUARDIÁN DE SEGURIDAD UNIVERSAL (VERSIÓN FINAL Y LIMPIA)
# =====================================================================
def requiere_permiso(nombre_permiso):
    """
    Decorador universal para proteger vistas. 
    Verifica si el usuario tiene un permiso específico (saltándose la caché).
    Los Administradores y Superusuarios SIEMPRE tienen acceso libre.
    """
    def decorador(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            usuario = request.user
            
            if usuario.is_authenticated:
                # 1. Los Administradores y Superusuarios SIEMPRE tienen acceso libre
                if usuario.is_superuser or usuario.rol == 'administrador':
                    return view_func(request, *args, **kwargs)
                
                # 2. Verificamos DIRECTO en la base de datos 
                tiene_permiso = usuario.user_permissions.filter(codename=nombre_permiso).exists()
                
                if tiene_permiso:
                    return view_func(request, *args, **kwargs)
                    
            # 3. Candado rojo estándar (Bomba nuclear desactivada)
            return render(request, 'usuarios/acceso_denegado.html', status=403)
            
        return _wrapped_view
    return decorador


# --- ACCESO CON REDIRECCIÓN INTELIGENTE ---
@method_decorator(csrf_exempt, name='dispatch')
class CustomLoginView(LoginView):
    template_name = 'usuarios/login.html'
    
    def get_success_url(self):
        usuario = self.request.user
        
        # 1. Administradores y Superusuarios
        if usuario.is_superuser or usuario.rol == 'administrador':
            return reverse_lazy('dashboard') 
            
        # 2. Clientes
        if usuario.rol == 'cliente':
            return reverse_lazy('reservas') 
            
        # 3. EMPLEADOS: Redirección dinámica basada en sus permisos reales
        if usuario.user_permissions.filter(codename='modulo_dashboard').exists():
            return reverse_lazy('dashboard')
            
        if usuario.user_permissions.filter(codename='modulo_mesas').exists():
            return reverse_lazy('estado_mesas')
        
        # Último recurso por defecto
        return reverse_lazy('estado_mesas')


# --- CIERRE DE SESIÓN SEGURO ---
def cerrar_sesion(request):
    logout(request)
    return redirect('login')


# =====================================================================
# VISTAS DE USUARIOS (PROTEGIDAS CON EL NUEVO GUARDIÁN)
# =====================================================================

# --- VISTA PRINCIPAL: PANEL DE USUARIOS ---
@login_required
@requiere_permiso('modulo_usuarios')
def lista_usuarios(request):
    usuarios = Usuario.objects.exclude(rol='cliente')
    
    query = request.GET.get('q', '').strip()
    rol_filter = request.GET.get('rol', 'Todos')
    estado_filter = request.GET.get('estado', 'Todos')

    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        )
        
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


# --- CREAR NUEVO EMPLEADO ---
@login_required
@requiere_permiso('modulo_usuarios')
def crear_usuario(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            nuevo_usuario = form.save()
            
            # 🎯 AUDITORÍA: Creación de empleado
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


# --- EDITAR EMPLEADO ---
@login_required
@requiere_permiso('modulo_usuarios')
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    rol_anterior = usuario.get_rol_display()
    
    if request.user == usuario:
        return render(request, 'usuarios/acceso_denegado.html', {
            'mensaje_personalizado': 'No puedes editar tus propios permisos desde esta vista por seguridad.'
        }, status=403)
            
    if request.method == 'POST':
        form = UsuarioEditForm(request.POST, instance=usuario)
        if form.is_valid():
            usuario_editado = form.save()
            
            # 🎯 AUDITORÍA: Edición de empleado
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


# --- ELIMINAR EMPLEADO (SOFT DELETE + ANONIMIZACIÓN BALANCEADA) ---
@login_required
@requiere_permiso('modulo_usuarios')
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    
    if request.method == 'POST':
        usuario.is_active = False
        usuario.set_unusable_password() 
        
        # Guardamos datos para la auditoría antes de cambiarlos
        username_original = usuario.username
        fue_anonimizado = request.POST.get('anonimizar') == 'on'
        
        if fue_anonimizado:
            # Conservamos el alias original pero le añadimos una marca de inactivo.
            usuario.username = f"{username_original}_anon_{usuario.id}"
            
            # Borramos los datos personales reales (PII) que sí son sensibles
            usuario.email = f"anonimo_{usuario.id}@sistema.local"
            usuario.first_name = "Historial"
            usuario.last_name = f"({username_original})"
            
        usuario.save()
        
        # 🎯 AUDITORÍA: Eliminación / Desactivación
        accion_auditoria = 'Usuario Anonimizado' if fue_anonimizado else 'Usuario Desactivado'
        detalle_auditoria = f"Eliminó y anonimizó los datos de {username_original}." if fue_anonimizado else f"Desactivó el acceso al usuario: {username_original}."
        
        Auditoria.objects.create(
            id_usuario=request.user,
            modulo='usuarios',
            accion=accion_auditoria,
            detalle=detalle_auditoria
        )
        
        return redirect('lista_usuarios')
        
    return render(request, 'usuarios/eliminar_usuario.html', {'usuario_eliminado': usuario})

# --- ASIGNACIÓN DE PERMISOS POR MÓDULOS ---
@login_required
@requiere_permiso('modulo_usuarios')
def asignar_permisos(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    permisos = Permission.objects.filter(content_type__app_label='usuarios', codename__startswith='modulo_')
    
    if request.method == 'POST':
        permisos_ids = request.POST.getlist('permisos')
        usuario.user_permissions.set(permisos_ids)
        
        # 🎯 AUDITORÍA: Asignación de permisos
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