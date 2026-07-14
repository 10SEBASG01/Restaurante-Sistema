from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Reserva
from .forms import ReservaForm
from apps.mesas.models import Mesa

# 🎯 IMPORTAMOS AUDITORÍA
from apps.auditoria.models import Auditoria


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
    fecha = request.GET.get('fecha', '') # 🎯 NUEVO: Obtenemos el filtro de fecha

    reservas = Reserva.objects.all()

    if busqueda:
        # 🎯 CAMBIO AQUÍ: Filtramos por nombres o apellidos
        reservas = reservas.filter(
            Q(nombres__icontains=busqueda) |
            Q(apellidos__icontains=busqueda) |
            Q(telefono__icontains=busqueda) |
            Q(codigo__icontains=busqueda)
        )

    if estado:
        reservas = reservas.filter(
            estado=estado
        )
        
    if fecha: # 🎯 NUEVO: Aplicamos el filtro de fecha
        reservas = reservas.filter(
            fecha=fecha
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
        'estado_actual': estado,
        'fecha_actual': fecha # 🎯 NUEVO: Enviamos la fecha seleccionada al template
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
                numero_mesa = int(reserva.mesa.replace('Mesa ', ''))
                mesa = Mesa.objects.get(numero=numero_mesa)

                # 🎯 LÓGICA DE ESTADOS Y LIMPIEZA
                if reserva.estado == 'CONFIRMADA':
                    mesa.estado = 'ocupada'
                    mesa.cliente_nombre = f"{reserva.nombres} {reserva.apellidos}"
                    mesa.cliente_cedula = reserva.cedula
                    mesa.cliente_correo = reserva.correo
                    mesa.cliente_direccion = reserva.direccion
                else:
                    mesa.estado = 'reservada'
                    mesa.cliente_nombre = None
                    mesa.cliente_cedula = None
                    mesa.cliente_correo = None
                    mesa.cliente_direccion = None

                mesa.save()

            except Exception:
                pass

            # 🎯 AUDITORÍA: Creación de reserva
            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='reservas',
                accion='Reserva Creada',
                detalle=f"Reserva {reserva.codigo} a nombre de {reserva.nombres} {reserva.apellidos} para la {reserva.mesa} ({reserva.fecha} a las {reserva.hora})."
            )

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
            'reserva': None,
            'titulo': 'Nueva Reserva',
            'mesas_libres': Mesa.objects.filter(is_active=True).order_by('numero') # 🎯 Pasamos las mesas al template
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
    
    estado_anterior = reserva.get_estado_display()

    if request.method == 'POST':

        form = ReservaForm(
            request.POST,
            instance=reserva
        )

        if form.is_valid():

            reserva_actualizada = form.save()

            try:
                numero_mesa = int(reserva_actualizada.mesa.replace('Mesa ', ''))
                mesa = Mesa.objects.get(numero=numero_mesa)

                if reserva_actualizada.estado == 'CONFIRMADA':
                    mesa.estado = 'ocupada'
                    mesa.cliente_nombre = f"{reserva_actualizada.nombres} {reserva_actualizada.apellidos}"
                    mesa.cliente_cedula = reserva_actualizada.cedula
                    mesa.cliente_correo = reserva_actualizada.correo
                    mesa.cliente_direccion = reserva_actualizada.direccion

                elif reserva_actualizada.estado == 'CANCELADA':
                    mesa.estado = 'libre'
                    mesa.cliente_nombre = None
                    mesa.cliente_cedula = None
                    mesa.cliente_correo = None
                    mesa.cliente_direccion = None

                else:
                    mesa.estado = 'reservada'
                    mesa.cliente_nombre = None
                    mesa.cliente_cedula = None
                    mesa.cliente_correo = None
                    mesa.cliente_direccion = None

                mesa.save()

            except Exception:
                pass

            detalle_audit = f"Actualizó datos de la reserva {reserva_actualizada.codigo} de {reserva_actualizada.nombres} {reserva_actualizada.apellidos}."
            if estado_anterior != reserva_actualizada.get_estado_display():
                detalle_audit += f" (Estado pasó a {reserva_actualizada.get_estado_display()})"

            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='reservas',
                accion='Reserva Editada',
                detalle=detalle_audit
            )

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
            'reserva': reserva,
            'titulo': 'Editar Reserva',
            'mesas_libres': Mesa.objects.filter(is_active=True).order_by('numero') # 🎯 Pasamos las mesas al template
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

            mesa.cliente_nombre = None
            mesa.cliente_cedula = None
            mesa.cliente_correo = None
            mesa.cliente_direccion = None

            mesa.save()

        except Exception:
            pass
            
        codigo_reserva = reserva.codigo
        cliente_reserva = f"{reserva.nombres} {reserva.apellidos}"

        reserva.delete()
        
        Auditoria.objects.create(
            id_usuario=request.user,
            modulo='reservas',
            accion='Reserva Eliminada',
            detalle=f"Eliminó la reserva {codigo_reserva} a nombre de {cliente_reserva}."
        )

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
    return render(request, 'reservas/observacion_reserva.html', {'reserva': reserva})