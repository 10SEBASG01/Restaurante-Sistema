from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages  # 🔥 Para mandar alertas seguras al usuario
from django.db.models import ProtectedError  # 🔥 Para capturar el bloqueo de borrado si hay FK activas

# 🛡️ IMPORTAMOS EL GUARDIÁN UNIVERSAL
from apps.usuarios.views import requiere_permiso

from .models import Mesa, ZonaMesa
from .forms import CambiarEstadoMesaForm, AsignarMeseroForm, MesaForm, ZonaMesaForm  # 🔥 Importado ZonaMesaForm

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

    # 1. Aplicar filtro de estados
    if filtro == 'libres':
        mesas = mesas.filter(estado='libre')
    elif filtro == 'ocupadas':
        mesas = mesas.filter(estado='ocupada')
    elif filtro == 'reservadas':
        mesas = mesas.filter(estado='reservada')

    # 2. Filtramos usando la relación directa 'ubicacion'
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
            form.save()
            return redirect('estado_mesas')
    else:
        form = MesaForm()
    return render(request, 'mesas/crear_mesa.html', {'form': form})

# --- EDITAR MESA ---
@login_required
@requiere_permiso('modulo_mesas')  
def editar_mesa(request, pk):
    mesa = get_object_or_404(Mesa, pk=pk)
    if request.method == 'POST':
        form = MesaForm(request.POST, instance=mesa)
        if form.is_valid():
            form.save()
            return redirect('estado_mesas')
    else:
        form = MesaForm(instance=mesa)
        
    return render(request, 'mesas/editar_mesa.html', {'form': form, 'mesa': mesa})

# --- ELIMINAR MESA ---
@login_required
@requiere_permiso('modulo_mesas')  
def eliminar_mesa(request, pk):
    mesa = get_object_or_404(Mesa, pk=pk)
    if request.method == 'POST':
        mesa.delete()
        return redirect('estado_mesas')
        
    return render(request, 'mesas/eliminar_mesa.html', {'mesa': mesa})

# --- ACCIONES RÁPIDAS DEL PANEL LATERAL ---
@login_required
@requiere_permiso('modulo_mesas')  
def cambiar_estado_mesa(request, pk):
    mesa = get_object_or_404(Mesa, pk=pk)
    if request.method == 'POST':
        form = CambiarEstadoMesaForm(request.POST, instance=mesa)
        if form.is_valid():
            form.save()
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
            form.save()
            return redirect('estado_mesas')
    else:
        form = AsignarMeseroForm(instance=mesa)
    
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
    # Apunta a la nueva carpeta que vas a crear
    return render(request, 'mesas/zonas/lista_zonas.html', {'zonas': zonas})

@login_required
@requiere_permiso('modulo_mesas')
def crear_zona(request):
    if request.method == 'POST':
        form = ZonaMesaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_zonas')
    else:
        form = ZonaMesaForm()
    return render(request, 'mesas/zonas/crear_zona.html', {'form': form})

@login_required
@requiere_permiso('modulo_mesas')
def eliminar_zona(request, pk):
    zona = get_object_or_404(ZonaMesa, pk=pk)
    if request.method == 'POST':
        try:
            zona.delete()
            return redirect('listar_zonas')
        except ProtectedError:
            # Capturamos el error si hay mesas usando la zona y mandamos una notificación
            messages.error(request, f"No se puede eliminar la zona '{zona.nombre_zona}' porque hay mesas asignadas a ella. Reasigna las mesas primero.")
            return redirect('listar_zonas')
            
    return render(request, 'mesas/zonas/eliminar_zona.html', {'zona': zona})