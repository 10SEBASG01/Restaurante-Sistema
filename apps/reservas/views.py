from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Reserva
from .forms import ReservaForm
from apps.mesas.models import Mesa


def acceso_reservas(request):

    usuario = request.user

    # Superusuario siempre entra
    if usuario.is_superuser:
        return True

    # Roles con acceso por defecto
    if usuario.rol in [
        'administrador',
        'secretaria'
    ]:
        return True

    # Permiso asignado manualmente
    tiene_permiso = usuario.user_permissions.filter(
        codename='modulo_reservas'
    ).exists()

    return tiene_permiso


@login_required
def lista_reservas(request):

    if not acceso_reservas(request):
        return render(
            request,
            'errors/acceso_denegado.html',
            status=403
        )

    busqueda = request.GET.get('q', '')
    estado = request.GET.get('estado', '')

    reservas = Reserva.objects.all()

    if busqueda:
        reservas = reservas.filter(
            Q(cliente__icontains=busqueda) |
            Q(telefono__icontains=busqueda) |
            Q(codigo__icontains=busqueda)
        )

    if estado:
        reservas = reservas.filter(
            estado=estado
        )

    context = {
        'reservas': reservas,

        'confirmadas': Reserva.objects.filter(
            estado='CONFIRMADA'
        ).count(),

        'pendientes': Reserva.objects.filter(
            estado='PENDIENTE'
        ).count(),

        'canceladas': Reserva.objects.filter(
            estado='CANCELADA'
        ).count(),

        'busqueda': busqueda,
        'estado_actual': estado
    }

    return render(
        request,
        'reservas/reservas_lista.html',
        context
    )


@login_required
def crear_reserva(request):

    if not acceso_reservas(request):
        return render(
            request,
            'errors/acceso_denegado.html',
            status=403
        )

    if request.method == 'POST':

        form = ReservaForm(request.POST)

        if form.is_valid():

            reserva = form.save()

            try:

                numero_mesa = int(
                    reserva.mesa.replace(
                        'Mesa ',
                        ''
                    )
                )

                mesa = Mesa.objects.get(
                    numero=numero_mesa
                )

                mesa.estado = 'reservada'

                # ==========================
                # DATOS TEMPORALES DEL CLIENTE
                # ==========================

                mesa.cliente_nombre = reserva.cliente
                mesa.cliente_cedula = reserva.cedula
                mesa.cliente_correo = reserva.correo
                mesa.cliente_direccion = reserva.direccion

                mesa.save()

            except Exception:
                pass

            messages.success(
                request,
                'Reserva creada correctamente.'
            )

            return redirect(
                'reservas:lista'
            )

    else:

        form = ReservaForm()

    return render(
        request,
        'reservas/reservas_form.html',
        {
            'form': form,
            'titulo': 'Nueva Reserva'
        }
    )


@login_required
def editar_reserva(request, pk):

    if not acceso_reservas(request):
        return render(
            request,
            'errors/acceso_denegado.html',
            status=403
        )

    reserva = get_object_or_404(
        Reserva,
        pk=pk
    )

    if request.method == 'POST':

        form = ReservaForm(
            request.POST,
            instance=reserva
        )

        if form.is_valid():

            reserva = form.save()

            # ==========================
            # ACTUALIZAR DATOS EN LA MESA
            # ==========================

            try:

                numero_mesa = int(
                    reserva.mesa.replace(
                        'Mesa ',
                        ''
                    )
                )

                mesa = Mesa.objects.get(
                    numero=numero_mesa
                )

                mesa.cliente_nombre = reserva.cliente
                mesa.cliente_cedula = reserva.cedula
                mesa.cliente_correo = reserva.correo
                mesa.cliente_direccion = reserva.direccion

                mesa.save()

            except Exception:
                pass

            messages.success(
                request,
                'Reserva actualizada correctamente.'
            )

            return redirect(
                'reservas:lista'
            )

    else:

        form = ReservaForm(
            instance=reserva
        )

    return render(
        request,
        'reservas/reservas_form.html',
        {
            'form': form,
            'titulo': 'Editar Reserva'
        }
    )


@login_required
def eliminar_reserva(request, pk):

    if not acceso_reservas(request):
        return render(
            request,
            'errors/acceso_denegado.html',
            status=403
        )

    reserva = get_object_or_404(
        Reserva,
        pk=pk
    )

    if request.method == 'POST':

        try:

            numero_mesa = int(
                reserva.mesa.replace(
                    'Mesa ',
                    ''
                )
            )

            mesa = Mesa.objects.get(
                numero=numero_mesa
            )

            mesa.estado = 'libre'

            mesa.cliente_nombre = ''
            mesa.cliente_cedula = ''
            mesa.cliente_correo = ''
            mesa.cliente_direccion = ''

            mesa.save()

        except Exception:
            pass

        reserva.delete()

        messages.success(
            request,
            'Reserva eliminada correctamente.'
        )

        return redirect(
            'reservas:lista'
        )

    return render(
        request,
        'reservas/reservas_confirm_delete.html',
        {
            'reserva': reserva
        }
    )

@login_required
def observacion_reserva(request, id):
    reserva = get_object_or_404(Reserva, id=id)
    # Aquí agregamos 'reservas/' antes del nombre del archivo 👇
    return render(request, 'reservas/observacion_reserva.html', {'reserva': reserva})