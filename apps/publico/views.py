from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q

from apps.menu.models import GestionPlatillo, CategoriasPlato
from apps.reservas.models import Reserva
from apps.publico.forms import ReservaPublicaForm
from apps.mesas.models import Mesa
# 🎯 IMPORTANTE: Importamos tu modelo de configuración
from apps.facturacion.models import ConfiguracionFacturacion  

# ======================================================
# PÁGINA PRINCIPAL PÚBLICA
# ======================================================

def inicio_publico(request):
    # Traemos el registro de configuración activo
    config = ConfiguracionFacturacion.objects.first()
    
    return render(
        request,
        'publico/inicio.html',
        {'config': config} # 🎯 Pasamos la configuración como contexto al HTML
    )


# ======================================================
# MENÚ PÚBLICO
# ======================================================

def menu_publico(request):

    categorias = CategoriasPlato.objects.all()
    categoria_activa = request.GET.get('categoria', 'Todos')
    busqueda = request.GET.get('search', '').strip()

    if categoria_activa == 'Todos' or busqueda:
        platillos = GestionPlatillo.objects.filter(disponible=True, activo=True)
    else:
        platillos = GestionPlatillo.objects.filter(
            disponible=True,
            activo=True,
            id_categoria__nombre_categoria=categoria_activa
        )

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
    if request.method == 'POST':
        form = ReservaPublicaForm(request.POST)

        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.estado = 'PENDIENTE'
            reserva.save()
            
            messages.success(
                request, 
                'Su reserva fue registrada correctamente.', 
                extra_tags='reserva_publica' 
            )

            return redirect('publico:reserva_publica')

    else:
        form = ReservaPublicaForm()

    # 🎯 CORRECCIÓN: Traemos TODAS las mesas, no solo las 'libres'.
    # Mantenemos el nombre de la variable 'mesas_libres' para no romper tu código en HTML
    mesas_libres = Mesa.objects.all().order_by('numero')

    context = {
        'titulo': 'Reservar Mesa',
        'form': form,
        'mesas_libres': mesas_libres, 
    }

    return render(request, 'publico/reserva_publica.html', context)