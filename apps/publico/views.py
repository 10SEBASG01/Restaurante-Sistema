from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q

from apps.menu.models import GestionPlatillo, CategoriasPlato
from apps.reservas.models import Reserva
from apps.publico.forms import ReservaPublicaForm

# 🔥 NUEVO: Importamos el modelo Mesa
from apps.mesas.models import Mesa


# ======================================================
# PÁGINA PRINCIPAL PÚBLICA
# ======================================================

def inicio_publico(request):

    return render(
        request,
        'publico/inicio.html'
    )


# ======================================================
# MENÚ PÚBLICO
# ======================================================

def menu_publico(request):

    categorias = CategoriasPlato.objects.all()

    categoria_activa = request.GET.get(
        'categoria',
        'Todos'
    )

    busqueda = request.GET.get(
        'search',
        ''
    ).strip()

    if categoria_activa == 'Todos' or busqueda:

        platillos = GestionPlatillo.objects.filter(
            disponible=True,
            activo=True
        )

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

    return render(

        request,

        'publico/menu_publico.html',

        context

    )


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
            
            # 🎯 CORRECCIÓN: Agregamos extra_tags para que el HTML lo detecte
            messages.success(
                request, 
                'Su reserva fue registrada correctamente.', 
                extra_tags='reserva_publica' 
            )

            return redirect('publico:reserva_publica')

    else:

        form = ReservaPublicaForm()

    # 🔥 NUEVO: Traemos explícitamente las mesas que están libres desde la BD
    mesas_libres = Mesa.objects.filter(estado='libre')

    context = {

        'titulo': 'Reservar Mesa',

        'form': form,

        'mesas_libres': mesas_libres,  # 🔥 Lo pasamos al HTML

    }

    return render(

        request,

        'publico/reserva_publica.html',

        context

    )