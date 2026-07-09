from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import ProtectedError

# 🛡️ IMPORTAMOS EL GUARDIÁN UNIVERSAL
from apps.usuarios.views import requiere_permiso

# 🎯 IMPORTAMOS AUDITORÍA
from apps.auditoria.models import Auditoria

from .models import Mesa, ZonaMesa
from .forms import CambiarEstadoMesaForm, AsignarMeseroForm, MesaForm, ZonaMesaForm

# --- VISTA PRINCIPAL: ESTADO DE MESAS ---
@login_required
@requiere_permiso('modulo_mesas')  
def lista_mesas(request):
    filtro = request.GET.get('estado', 'todas')
    filtro_ubicacion = request.GET.get('ubicacion', 'todas') 
    
    mesas = Mesa.objects.all().select_related('ubicacion')
    zonas = ZonaMesa.objects.all() 

    total_libres = Mesa.objects.filter(estado='libre').count()
    total_ocupadas = Mesa.objects.filter(estado='ocupada').count()
    total_reservadas = Mesa.objects.filter(estado='reservada').count()

    if filtro == 'libres':
        mesas = mesas.filter(estado='libre')
    elif filtro == 'ocupadas':
        mesas = mesas.filter(estado='ocupada')
    elif filtro == 'reservadas':
        mesas = mesas.filter(estado='reservada')

    if filtro_ubicacion != 'todas':
        mesas = mesas.filter(ubicacion=filtro_ubicacion)

    context = {
        'mesas': mesas,
        'filtro_actual': filtro,
        'filtro_ubicacion': filtro_ubicacion,
        'ubicaciones': zonas, 
        'total_libres': total_libres,
        'total_ocupadas': total_ocupadas,
        'total_reservadas': total_reservadas,
    }
    return render(request, 'mesas/estado_mesas.html', context)

# --- CREAR MESA ---
@login_required
@requiere_permiso('modulo_mesas')  
def crear_mesa(request):
    if request.method == 'POST':
        form = MesaForm(request.POST)
        if form.is_valid():
            mesa = form.save()
            
            # 🎯 Auditoría
            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='mesas',
                accion='Mesa Creada',
                detalle=f"Registró la Mesa {mesa.numero} (Capacidad: {mesa.capacidad} pax)."
            )
            return redirect('estado_mesas')
    else:
        form = MesaForm()
        
        # 💡 TRUCO: Cambiamos las opciones del select para que muestre el Nombre Completo
        if 'mesero_assigned' in form.fields:
            form.fields['mesero_assigned'].label_from_instance = lambda obj: f"{obj.first_name} {obj.last_name}".strip() or obj.username
            
    return render(request, 'mesas/crear_mesa.html', {'form': form})

# --- EDITAR MESA ---
@login_required
@requiere_permiso('modulo_mesas')  
def editar_mesa(request, pk):
    mesa = get_object_or_404(Mesa, pk=pk)
    if request.method == 'POST':
        form = MesaForm(request.POST, instance=mesa)
        if form.is_valid():
            mesa_editada = form.save()
            
            # 🎯 Auditoría
            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='mesas',
                accion='Mesa Editada',
                detalle=f"Actualizó la configuración de la Mesa {mesa_editada.numero}."
            )
            return redirect('estado_mesas')
    else:
        form = MesaForm(instance=mesa)
        
        # 💡 TRUCO: Cambiamos las opciones del select para que muestre el Nombre Completo
        if 'mesero_assigned' in form.fields:
            form.fields['mesero_assigned'].label_from_instance = lambda obj: f"{obj.first_name} {obj.last_name}".strip() or obj.username
        
    return render(request, 'mesas/editar_mesa.html', {'form': form, 'mesa': mesa})

# --- ELIMINAR MESA ---
@login_required
@requiere_permiso('modulo_mesas')  
def eliminar_mesa(request, pk):
    mesa = get_object_or_404(Mesa, pk=pk)
    
    if request.method == 'POST':
        # 🔒 Validación de seguridad en el servidor (en minúsculas)
        if mesa.estado != 'libre':
            messages.error(request, f"No se puede eliminar la Mesa {mesa.numero} porque no está libre.")
            return redirect('estado_mesas')
            
        numero_mesa = mesa.numero
        
        try:
            mesa.delete()
            
            # 🎯 Auditoría
            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='mesas',
                accion='Mesa Eliminada',
                detalle=f"Eliminó permanentemente la Mesa {numero_mesa}."
            )
            return redirect('estado_mesas')
            
        except ProtectedError:
            messages.warning(
                request, 
                f'La Mesa {numero_mesa} está libre, pero no se puede borrar porque tiene pedidos o reservas vinculadas en el historial.'
            )
            return redirect('estado_mesas')
        
    return render(request, 'mesas/eliminar_mesa.html', {'mesa': mesa})

# --- ACCIONES RÁPIDAS DEL PANEL LATERAL ---
@login_required
@requiere_permiso('modulo_mesas')  
def cambiar_estado_mesa(request, pk):
    mesa = get_object_or_404(Mesa, pk=pk)
    estado_anterior = mesa.get_estado_display()
    
    if request.method == 'POST':
        form = CambiarEstadoMesaForm(request.POST, instance=mesa)
        if form.is_valid():
            mesa_actualizada = form.save()
            
            # 🎯 Auditoría
            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='mesas',
                accion='Cambio de Estado',
                detalle=f"Mesa {mesa_actualizada.numero} pasó de '{estado_anterior}' a '{mesa_actualizada.get_estado_display()}'."
            )
            return redirect('estado_mesas')
    else:
        form = CambiarEstadoMesaForm(instance=mesa)
    
    return render(request, 'mesas/accion_mesa.html', {
        'form': form, 'mesa': mesa, 
        'titulo': 'Cambiar Estado', 
        'subtitulo': 'Actualiza la disponibilidad de la mesa en tiempo real.'
    })

@login_required
@requiere_permiso('modulo_mesas')  
def asignar_mesero_mesa(request, pk):
    mesa = get_object_or_404(Mesa, pk=pk)
    if request.method == 'POST':
        form = AsignarMeseroForm(request.POST, instance=mesa)
        if form.is_valid():
            mesa_actualizada = form.save()
            
            mesero = mesa_actualizada.mesero_assigned.get_full_name() if mesa_actualizada.mesero_assigned else "Ninguno"
            cliente = mesa_actualizada.cliente_nombre if mesa_actualizada.cliente_nombre else "No especificado"
            
            # 🎯 Auditoría
            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='mesas',
                accion='Asignación de Servicio',
                detalle=f"Mesa {mesa_actualizada.numero}: Mesero ({mesero}) - Cliente ({cliente})."
            )
            return redirect('estado_mesas')
    else:
        form = AsignarMeseroForm(instance=mesa)
        
        # 💡 TRUCO: Cambiamos las opciones del select para que muestre el Nombre Completo
        # Sobrescribimos el método que Django usa para etiquetar cada opción del select
        if 'mesero_assigned' in form.fields:
            form.fields['mesero_assigned'].label_from_instance = lambda obj: f"{obj.first_name} {obj.last_name}".strip() or obj.username
    
    return render(request, 'mesas/accion_mesa.html', {
        'form': form, 'mesa': mesa, 
        'titulo': 'Asignar Servicio', 
        'subtitulo': 'Vincula un mesero y registra al cliente para esta mesa.'
    })

# =======================================================
# 🔥 NUEVAS VISTAS: MÓDULO INDEPENDIENTE (CRUD DE ZONAS)
# =======================================================

@login_required
@requiere_permiso('modulo_mesas')
def listar_zonas(request):
    zonas = ZonaMesa.objects.all()
    return render(request, 'mesas/zonas/lista_zonas.html', {'zonas': zonas})

@login_required
@requiere_permiso('modulo_mesas')
def crear_zona(request):
    if request.method == 'POST':
        form = ZonaMesaForm(request.POST)
        if form.is_valid():
            zona = form.save()
            
            # 🎯 Auditoría
            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='mesas',
                accion='Zona Creada',
                detalle=f"Añadió la nueva zona: {zona.nombre_zona}."
            )
            return redirect('listar_zonas')
    else:
        form = ZonaMesaForm()
    return render(request, 'mesas/zonas/crear_zona.html', {'form': form})

@login_required
@requiere_permiso('modulo_mesas')
def eliminar_zona(request, pk):
    zona = get_object_or_404(ZonaMesa, pk=pk)
    if request.method == 'POST':
        nombre_zona = zona.nombre_zona
        try:
            zona.delete()
            
            # 🎯 Auditoría
            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='mesas',
                accion='Zona Eliminada',
                detalle=f"Eliminó la zona: {nombre_zona}."
            )
            return redirect('listar_zonas')
        except ProtectedError:
            messages.error(request, f"No se puede eliminar la zona '{zona.nombre_zona}' porque hay mesas asignadas a ella. Reasigna las mesas primero.")
            return redirect('listar_zonas')
            
    return render(request, 'mesas/zonas/eliminar_zona.html', {'zona': zona})