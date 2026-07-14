"""
Controladores (Vistas) para la gestión interna de Reservas.

Este módulo orquesta la lógica de negocio central, incluyendo:
1. Seguridad (RBAC): Control de Acceso Basado en Roles para proteger las vistas.
2. Sincronización de Estados: Actualización en cascada del estado de las mesas 
   (ocupada, reservada, libre) según el ciclo de vida de la reserva.
3. Trazabilidad: Registro automático de eventos en el módulo de Auditoría 
   para mantener un historial de quién hizo qué y cuándo.
"""

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Reserva
from .forms import ReservaForm
from apps.mesas.models import Mesa

# Integración con el sistema de trazabilidad global
from apps.auditoria.models import Auditoria


def acceso_reservas(request):
    """
    Control de Acceso Basado en Roles (RBAC).
    
    Verifica si el usuario autenticado tiene los privilegios necesarios 
    para operar el módulo de reservas.
    
    Retorna:
        bool: True si el usuario está autorizado, False en caso contrario.
    """
    usuario = request.user

    # Nivel 1: El superusuario tiene acceso global irrestricto
    if usuario.is_superuser:
        return True

    # Nivel 2: Acceso por rol departamental implícito
    if usuario.rol in ['administrador', 'secretaria']:
        return True

    # Nivel 3: Acceso granular mediante permisos específicos de Django
    tiene_permiso = usuario.user_permissions.filter(
        codename='modulo_reservas'
    ).exists()

    return tiene_permiso


@login_required
def lista_reservas(request):
    """
    Panel principal (Dashboard) de Reservas.
    
    Procesa múltiples filtros (texto, estado, fecha) mediante objetos Q 
    para búsquedas complejas y calcula las métricas agregadas que se 
    muestran en los indicadores superiores de la interfaz.
    """
    # Validación de seguridad perimetral
    if not acceso_reservas(request):
        return render(request, 'errors/acceso_denegado.html', status=403)

    # Captura de parámetros de filtrado desde la URL (Petición GET)
    busqueda = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    fecha = request.GET.get('fecha', '')

    # QuerySet base
    reservas = Reserva.objects.all()

    # Filtro cruzado (OR) para la barra de búsqueda general
    if busqueda:
        reservas = reservas.filter(
            Q(nombres__icontains=busqueda) |
            Q(apellidos__icontains=busqueda) |
            Q(telefono__icontains=busqueda) |
            Q(codigo__icontains=busqueda)
        )

    # Filtro exacto por estado (PENDIENTE, CONFIRMADA, CANCELADA)
    if estado:
        reservas = reservas.filter(estado=estado)
        
    # Filtro cronológico
    if fecha:
        reservas = reservas.filter(fecha=fecha)

    # Inyección de datos y métricas para la renderización del template
    context = {
        'reservas': reservas,
        # Cálculos de agregación para los KPIs de la interfaz
        'confirmadas': Reserva.objects.filter(estado='CONFIRMADA').count(),
        'pendientes': Reserva.objects.filter(estado='PENDIENTE').count(),
        'canceladas': Reserva.objects.filter(estado='CANCELADA').count(),
        # Mantenimiento del estado de los filtros en la vista
        'busqueda': busqueda,
        'estado_actual': estado,
        'fecha_actual': fecha 
    }

    return render(request, 'reservas/reservas_lista.html', context)


@login_required
def crear_reserva(request):
    """
    Orquesta la creación de una nueva reserva, asegurando la consistencia 
    entre el agendamiento y el estado físico de la mesa en el restaurante.
    """
    if not acceso_reservas(request):
        return render(request, 'errors/acceso_denegado.html', status=403)

    if request.method == 'POST':
        form = ReservaForm(request.POST)

        if form.is_valid():
            # Guarda la reserva en la base de datos
            reserva = form.save()

            # Lógica de sincronización: Actualiza el estado de la Mesa vinculada
            try:
                # Extrae el número entero del string (ej. "Mesa 5" -> 5)
                numero_mesa = int(reserva.mesa.replace('Mesa ', ''))
                mesa = Mesa.objects.get(numero=numero_mesa)

                # Máquina de estados para la Mesa
                if reserva.estado == 'CONFIRMADA':
                    mesa.estado = 'ocupada'
                    # Transfiere los datos del cliente a la mesa para facturación rápida
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
                # Fallback silencioso: Si la mesa no existe temporalmente, 
                # la reserva se guarda igual sin romper el flujo de la aplicación.
                pass

            # Registro de la operación en el log de Auditoría
            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='reservas',
                accion='Reserva Creada',
                detalle=f"Reserva {reserva.codigo} a nombre de {reserva.nombres} {reserva.apellidos} para la {reserva.mesa} ({reserva.fecha} a las {reserva.hora})."
            )

            messages.success(request, 'Reserva creada correctamente.')
            return redirect('reservas:lista')
    else:
        # Petición GET: Carga el formulario vacío
        form = ReservaForm()

    return render(
        request,
        'reservas/reservas_form.html',
        {
            'form': form,
            'reserva': None,
            'titulo': 'Nueva Reserva',
            # Optimización: Solo se envían mesas operativas para prevenir agendamientos erróneos
            'mesas_libres': Mesa.objects.filter(is_active=True).order_by('numero') 
        }
    )


@login_required
def editar_reserva(request, pk):
    """
    Gestiona la modificación de una reserva existente, evaluando 
    transiciones de estado (ej. de PENDIENTE a CANCELADA) para liberar 
    o bloquear la mesa correspondiente.
    """
    if not acceso_reservas(request):
        return render(request, 'errors/acceso_denegado.html', status=403)

    reserva = get_object_or_404(Reserva, pk=pk)
    # Captura el estado original para evaluar si hubo cambios en la auditoría
    estado_anterior = reserva.get_estado_display()

    if request.method == 'POST':
        form = ReservaForm(request.POST, instance=reserva)

        if form.is_valid():
            reserva_actualizada = form.save()

            # Sincronización del ciclo de vida con la Mesa física
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
                    # Si se cancela, la mesa vuelve a estar disponible para "walk-ins"
                    mesa.estado = 'libre'
                    mesa.cliente_nombre = None
                    mesa.cliente_cedula = None
                    mesa.cliente_correo = None
                    mesa.cliente_direccion = None

                else:
                    # Estado PENDIENTE
                    mesa.estado = 'reservada'
                    mesa.cliente_nombre = None
                    mesa.cliente_cedula = None
                    mesa.cliente_correo = None
                    mesa.cliente_direccion = None

                mesa.save()
            except Exception:
                pass

            # Construcción inteligente del detalle de auditoría
            detalle_audit = f"Actualizó datos de la reserva {reserva_actualizada.codigo} de {reserva_actualizada.nombres} {reserva_actualizada.apellidos}."
            if estado_anterior != reserva_actualizada.get_estado_display():
                detalle_audit += f" (Estado pasó a {reserva_actualizada.get_estado_display()})"

            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='reservas',
                accion='Reserva Editada',
                detalle=detalle_audit
            )

            messages.success(request, 'Reserva actualizada correctamente.')
            return redirect('reservas:lista')
    else:
        form = ReservaForm(instance=reserva)

    return render(
        request,
        'reservas/reservas_form.html',
        {
            'form': form,
            'reserva': reserva,
            'titulo': 'Editar Reserva',
            'mesas_libres': Mesa.objects.filter(is_active=True).order_by('numero') 
        }
    )


@login_required
def eliminar_reserva(request, pk):
    """
    Ejecuta el borrado físico de la reserva, aplicando primero un proceso 
    de limpieza (cleanup) sobre la mesa afectada para evitar dependencias fantasmas.
    """
    if not acceso_reservas(request):
        return render(request, 'errors/acceso_denegado.html', status=403)

    reserva = get_object_or_404(Reserva, pk=pk)

    if request.method == 'POST':
        # 1. Limpieza de dependencias en cascada (Liberar la mesa)
        try:
            numero_mesa = int(reserva.mesa.replace('Mesa ', ''))
            mesa = Mesa.objects.get(numero=numero_mesa)

            mesa.estado = 'libre'
            mesa.cliente_nombre = None
            mesa.cliente_cedula = None
            mesa.cliente_correo = None
            mesa.cliente_direccion = None
            mesa.save()
        except Exception:
            pass
            
        # 2. Respaldo temporal de datos críticos para la trazabilidad
        codigo_reserva = reserva.codigo
        cliente_reserva = f"{reserva.nombres} {reserva.apellidos}"

        # 3. Borrado físico del registro
        reserva.delete()
        
        # 4. Registro de la eliminación
        Auditoria.objects.create(
            id_usuario=request.user,
            modulo='reservas',
            accion='Reserva Eliminada',
            detalle=f"Eliminó la reserva {codigo_reserva} a nombre de {cliente_reserva}."
        )

        messages.success(request, 'Reserva eliminada correctamente.')
        return redirect('reservas:lista')

    # Si es GET, muestra la pantalla de confirmación (Seguridad contra CSRF)
    return render(
        request,
        'reservas/reservas_confirm_delete.html',
        {'reserva': reserva}
    )

@login_required
def observacion_reserva(request, id):
    """
    Vista de solo lectura (Modal/Detalle).
    Extrae un registro único para consultar especificaciones o notas 
    dejadas por el cliente (ej. requerimientos de accesibilidad, alergias).
    """
    reserva = get_object_or_404(Reserva, id=id)
    return render(request, 'reservas/observacion_reserva.html', {'reserva': reserva})