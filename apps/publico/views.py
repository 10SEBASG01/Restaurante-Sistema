"""
Controladores (Vistas) para la interfaz pública del cliente.

Gestiona las peticiones GET y POST para mostrar información del restaurante, 
renderizar el menú digital con filtros, y procesar los formularios de reservas.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q

# Importaciones de modelos y formularios de otras aplicaciones del sistema
from apps.menu.models import GestionPlatillo, CategoriasPlato
from apps.reservas.models import Reserva
from apps.publico.forms import ReservaPublicaForm
from apps.mesas.models import Mesa
from apps.facturacion.models import ConfiguracionFacturacion  


# ======================================================
# PÁGINA PRINCIPAL PÚBLICA
# ======================================================

def inicio_publico(request):
    """
    Renderiza la página de inicio (Landing Page) del restaurante.
    Carga dinámicamente la configuración activa (logo, datos comerciales, etc.)
    para inyectarlos en la plantilla.
    """
    # Obtiene el primer registro de configuración activo del sistema
    config = ConfiguracionFacturacion.objects.first()
    
    return render(
        request,
        'publico/inicio.html',
        {'config': config} 
    )


# ======================================================
# MENÚ PÚBLICO
# ======================================================

def menu_publico(request):
    """
    Renderiza el menú digital interactivo para los clientes.
    Implementa un sistema de filtrado combinado por categoría exacta
    y búsqueda por texto en nombre o descripción del platillo.
    """
    categorias = CategoriasPlato.objects.all()
    
    # Parámetros capturados de la URL (GET)
    categoria_activa = request.GET.get('categoria', 'Todos')
    busqueda = request.GET.get('search', '').strip()

    # 1. Filtrado inicial por disponibilidad global o categoría específica
    if categoria_activa == 'Todos' or busqueda:
        platillos = GestionPlatillo.objects.filter(disponible=True, activo=True)
    else:
        platillos = GestionPlatillo.objects.filter(
            disponible=True,
            activo=True,
            id_categoria__nombre_categoria=categoria_activa
        )

    # 2. Filtrado secundario por término de búsqueda (coincidencia parcial)
    if busqueda:
        platillos = platillos.filter(
            Q(nombre_platillo__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )

    context = {
        'platillos': platillos,
        'categorias': categorias,
        'categoria_activa': categoria_activa,
        'search': busqueda,
    }

    return render(request, 'publico/menu_publico.html', context)


# ======================================================
# RESERVA PÚBLICA
# ======================================================

def reserva_publica(request):
    """
    Gestiona el flujo de creación de una nueva reserva desde el portal web.
    - Método GET: Renderiza el formulario vacío y la lista de mesas activas.
    - Método POST: Valida los datos, guarda la reserva en estado PENDIENTE 
      y muestra un mensaje de éxito.
    """
    if request.method == 'POST':
        form = ReservaPublicaForm(request.POST)

        if form.is_valid():
            # Genera la instancia sin guardarla aún en BD
            reserva = form.save(commit=False)
            # Fuerza el estado inicial del ciclo de vida de la reserva
            reserva.estado = 'PENDIENTE'
            reserva.save()
            
            # Envía un mensaje flash a la interfaz del usuario confirmando la acción
            messages.success(
                request, 
                'Su reserva fue registrada correctamente.', 
                extra_tags='reserva_publica' 
            )

            # Redirige para limpiar el formulario (evita doble reenvío de datos)
            return redirect('publico:reserva_publica')

    else:
        # Petición GET: Instancia un formulario en blanco
        form = ReservaPublicaForm()

    # Consulta solo las mesas disponibles y operativas para dibujar el mapa/selector
    mesas_libres = Mesa.objects.filter(is_active=True).order_by('numero')

    context = {
        'titulo': 'Reservar Mesa',
        'form': form,
        'mesas_libres': mesas_libres, 
    }

    return render(request, 'publico/reserva_publica.html', context)