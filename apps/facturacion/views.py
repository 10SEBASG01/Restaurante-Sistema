from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP  
from django.db.models import Q

# Importaciones de tus aplicaciones locales
from apps.pedidos.models import GestionPedido
from apps.mesas.models import Mesa
from .models import Factura, FacturaDetalle, ConfiguracionFacturacion  
from .forms import FacturaForm


# =========================================================================
# BLOQUE 1: FUNCIONES AUXILIARES Y CONTROL DE PERMISOS
# =========================================================================

def interpolar_dos_decimales(valor):
    # LINEA IMPORTANTE: Redondeo matemático estricto a 2 decimales para evitar discrepancias con JS
    return Decimal(str(valor)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def acceso_facturacion(request):
    # Control de seguridad: Filtra accesos por superusuario, roles asignados o permisos explícitos
    usuario = request.user
    if usuario.is_superuser:
        return True
    if hasattr(usuario, 'rol') and usuario.rol in ['administrador', 'secretaria']:
        return True
    return usuario.user_permissions.filter(codename='modulo_facturacion').exists()


# =========================================================================
# BLOQUE 2: CONSOLA DE CAJA (LISTADO DE PENDIENTES)
# =========================================================================

@login_required
def listar_pedidos_por_facturar(request):
    if not acceso_facturacion(request):
        return render(request, 'errors/acceso_denegado.html', status=403)
        
    # LINEA IMPORTANTE: select_related evita consultas repetitivas (N+1) al traer la mesa asociada
    pedidos = GestionPedido.objects.filter(factura__isnull=True).select_related('id_mesa')
    return render(request, 'facturacion/listar_pedidos.html', {'pedidos': pedidos})


# =========================================================================
# BLOQUE 3: PROCESAMIENTO GENERAL DE FACTURACIÓN (CHECKOUT)
# =========================================================================

@login_required
def crear_factura(request, id_pedido=None):
    if not acceso_facturacion(request):
        return render(request, 'errors/acceso_denegado.html', status=403)

    pedido = None
    detalles_pedido = None
    mesas_disponibles = []

    # Carga base de consumos aptos para liquidar
    pedidos_pendientes = GestionPedido.objects.filter(
        estado_pedido__in=['listo', 'entregado'], 
        factura__isnull=True
    )

    # SUB-BLOQUE: Enrutamiento de Flujo (Manual vs Directo por Mesa)
    if id_pedido is None:
        mesas_disponibles = list({p.id_mesa for p in pedidos_pendientes if p.id_mesa})
        mesa_id = request.GET.get('mesa_id')
        if mesa_id:
            pedido = pedidos_pendientes.filter(id_mesa=mesa_id).first()
            if not pedido:
                messages.warning(request, "La mesa seleccionada no tiene pedidos listos para cobrar.")
    else:
        pedido = get_object_or_404(GestionPedido, id_pedido=id_pedido)

    # SUB-BLOQUE: Validaciones previas del estado del pedido
    if pedido:
        if Factura.objects.filter(id_pedido=pedido).exists():
            messages.error(request, f"El pedido #{pedido.id_pedido} ya fue facturado anteriormente.")
            return redirect('listar_pedidos_por_facturar')

        if pedido.estado_pedido not in ['listo', 'entregado']:
            messages.error(request, "El pedido aún no está listo para ser cobrado.")
            return redirect('listar_pedidos_por_facturar')

        detalles_pedido = pedido.detalles.all().select_related('id_platillo')
        if not detalles_pedido.exists():
            messages.error(request, "El pedido no contiene platillos para facturar.")
            return redirect('listar_pedidos_por_facturar')

        # LINEA IMPORTANTE: Pre-calcula y limpia decimales del subtotal acumulado inicial
        subtotal_acumulado = sum(Decimal(str(d.cantidad)) * Decimal(str(d.precio_unitario)) for d in detalles_pedido)
        subtotal_acumulado = interpolar_dos_decimales(subtotal_acumulado)
    else:
        subtotal_acumulado = Decimal('0.00')

    # Obtención dinámica de impuestos comerciales
    config_emisor = ConfiguracionFacturacion.objects.first()
    porcentaje_iva = config_emisor.iva_porcentaje if config_emisor else 12
    factor_iva = Decimal(str(porcentaje_iva)) / Decimal('100.00')

    subtotal_12 = subtotal_acumulado
    subtotal_0 = Decimal('0.00')
    iva_valor = interpolar_dos_decimales(subtotal_12 * factor_iva)
    total_general = interpolar_dos_decimales(subtotal_12 + iva_valor)

    # SUB-BLOQUE: Procesamiento de Guardado de la Venta
    if request.method == 'POST':
        if not pedido:
            messages.error(request, "Operación inválida. Debe seleccionar una mesa con consumos válidos.")
            return redirect('listar_pedidos_por_facturar')

        form = FacturaForm(request.POST)
        if form.is_valid():
            try:
                # LINEA IMPORTANTE: atomic() garantiza que si falla un detalle, no se guarde la cabecera (Rollback)
                with transaction.atomic():
                    factura = form.save(commit=False)
                    factura.id_pedido = pedido
                    factura.id_cajero = request.user
                    
                    # LINEA IMPORTANTE: Resguardo estático de datos fiscales (Inmutabilidad histórica frente a cambios en config)
                    if config_emisor:
                        factura.emisor_nombre_comercial = config_emisor.nombre_comercial
                        factura.emisor_razon_social = config_emisor.razon_social
                        factura.emisor_ruc = config_emisor.ruc
                        factura.emisor_direccion = config_emisor.direccion
                        factura.emisor_provincia = config_emisor.provincia
                        factura.iva_porcentaje_aplicado = porcentaje_iva
                    else:
                        factura.emisor_nombre_comercial = "Sabor y Arte"
                        factura.emisor_ruc = "20456789012"
                        factura.emisor_direccion = "Av. Gastronomía 455, Miraflores"
                        factura.iva_porcentaje_aplicado = 12
                    
                    try:
                        porcentaje_descuento = int(request.POST.get('descuento', 0))
                    except (ValueError, TypeError):
                        porcentaje_descuento = 0
                    
                    # Cálculos económicos intermedios con redondeo estándar
                    descuento_en_dinero = interpolar_dos_decimales((subtotal_12 * Decimal(str(porcentaje_descuento))) / Decimal('100.00'))
                    nuevo_subtotal_afectado = interpolar_dos_decimales(subtotal_12 - descuento_en_dinero)
                    iva_recalculado = interpolar_dos_decimales(nuevo_subtotal_afectado * factor_iva)
                    
                    factura.subtotal_12 = subtotal_12
                    factura.subtotal_0 = subtotal_0
                    factura.descuento = descuento_en_dinero  
                    factura.descuento_porcentaje = porcentaje_descuento  
                    factura.subtotal_neto = nuevo_subtotal_afectado      
                    factura.iva_valor = iva_recalculado 
                    factura.total = interpolar_dos_decimales(nuevo_subtotal_afectado + iva_recalculado)
                    
                    # LINEA IMPORTANTE: Generación automática y secuencial del número de factura fiscal (FAC-XXXXXXXX)
                    ultimo_registro = Factura.objects.order_by('-id_factura').first()
                    num_secuencial = (ultimo_registro.id_factura + 1) if (ultimo_registro and ultimo_registro.id_factura) else 1
                    factura.secuencial = f"FAC-{num_secuencial:08d}"
                    
                    factura.save()

                    # LINEA IMPORTANTE: Copia los platillos actuales al histórico de la factura para congelar precios y nombres
                    for item in detalles_pedido:
                        FacturaDetalle.objects.create(
                            id_factura=factura,
                            id_platillo=item.id_platillo,
                            nombre_historico=item.id_platillo.nombre_platillo if hasattr(item.id_platillo, 'nombre_platillo') else f"Platillo ID {item.id_platillo_id}",
                            cantidad=item.cantidad,
                            precio_unitario_historico=item.precio_unitario
                        )

                    # LINEA IMPORTANTE: Libera y blanquea la mesa en el salón físico para que pueda recibir nuevos clientes
                    mesa_afectada = pedido.id_mesa
                    mesa_afectada.estado = 'libre'
                    mesa_afectada.cliente_nombre = None
                    mesa_afectada.cliente_cedula = None
                    mesa_afectada.cliente_correo = None
                    mesa_afectada.cliente_direccion = None
                    mesa_afectada.mesero_assigned = None
                    mesa_afectada.save()
                    
                    # Log de auditoría del sistema
                    from apps.auditoria.models import Auditoria
                    Auditoria.objects.create(
                        id_usuario=request.user,
                        modulo='facturacion',
                        accion='Factura Emitida',
                        detalle=f"Factura {factura.secuencial} - Cliente: {factura.cliente_nombre} - Total: ${factura.total}"
                    )

                    messages.success(request, f"Factura {factura.secuencial} emitida con éxito. Mesa {mesa_afectada.numero} liberada.")
                    return redirect('ver_detalle_factura', id_factura=factura.id_factura)

            except Exception as e:
                messages.error(request, f"Error crítico al guardar la factura: {str(e)}")
        else:
            messages.error(request, "Por favor, verifique que los datos del cliente estén completos y correctos.")

    # SUB-BLOQUE: Renderizado Inicial (GET) con carga de estados iniciales
    else:
        if pedido:
            mesa = pedido.id_mesa
            form = FacturaForm(initial={
                'cliente_nombre': mesa.cliente_nombre if mesa.cliente_nombre else "Consumidor Final",
                'cliente_identificacion': mesa.cliente_cedula if mesa.cliente_cedula else "9999999999",
                'cliente_correo': mesa.cliente_correo if mesa.cliente_correo else "",
                'cliente_direccion': mesa.cliente_direccion if mesa.cliente_direccion else ""
            })
        else:
            form = FacturaForm()

    return render(request, 'facturacion/nueva_factura.html', {
        'form': form,
        'pedido': pedido,
        'detalles_pedido': detalles_pedido,
        'mesas_disponibles': mesas_disponibles,
        'subtotal_12': subtotal_12,
        'iva_valor': iva_valor,
        'iva_porcentaje': porcentaje_iva, 
        'total_general': total_general,
        'fecha_actual': timezone.localtime(timezone.now()),
        'hora_actual': timezone.localtime(timezone.now()).strftime('%H:%M'),
        'config_emisor': config_emisor,
    })


# =========================================================================
# BLOQUE 4: VISUALIZACIÓN, BÚSQUEDA Y HISTORIAL DE AUDITORÍA
# =========================================================================

@login_required
def ver_detalle_factura(request, id_factura):
    if not acceso_facturacion(request):
        return render(request, 'errors/acceso_denegado.html', status=403)

    factura = get_object_or_404(Factura, id_factura=id_factura)
    return render(request, 'facturacion/detalle_factura.html', {
        'factura':       factura,
        'detalles':      factura.detalles_factura.all()  
    })


def historial_facturas(request):
    if not acceso_facturacion(request):
        return render(request, 'errors/acceso_denegado.html', status=403)

    search_query = request.GET.get('search', '').strip()
    fecha_query = request.GET.get('fecha', '').strip()
    facturas = Factura.objects.all()

    # LINEA IMPORTANTE: Uso del operador Q para realizar búsquedas avanzadas y cruzadas con los datos del cajero
    if search_query:
        facturas = facturas.filter(
            Q(cliente_nombre__icontains=search_query) |
            Q(cliente_identificacion__icontains=search_query) |
            Q(secuencial__icontains=search_query) |
            Q(id_cajero__first_name__icontains=search_query) |
            Q(id_cajero__last_name__icontains=search_query) |
            Q(id_cajero__username__icontains=search_query)
        )

    if fecha_query:
        facturas = facturas.filter(fecha_emision__date=fecha_query)

    return render(request, 'facturacion/historial_facturas.html', {
        'facturas': facturas,
        'search_query': search_query,
        'fecha_query': fecha_query
    })


# =========================================================================
# BLOQUE 5: GESTIÓN DE CONFIGURACIÓN DINÁMICA DE FACTURACIÓN (TABS)
# =========================================================================

@login_required
def configuracion_facturacion(request):
    config, created = ConfiguracionFacturacion.objects.get_or_create(id=1)
    tab_activa = 'empresa'

    if request.method == 'POST':
        from apps.auditoria.models import Auditoria
        
        # SUB-BLOQUE POST: Modificación de Datos del Emisor
        if 'action_emisor' in request.POST:
            tab_activa = 'empresa'
            config.nombre_comercial = request.POST.get('nombre_comercial')
            config.razon_social = request.POST.get('razon_social')
            config.ruc = request.POST.get('ruc')
            config.provincia = request.POST.get('ciudad_provincia')
            config.direccion = request.POST.get('direccion')
            config.telefono = request.POST.get('telefono')
            config.save()
            
            Auditoria.objects.create(id_usuario=request.user, modulo='facturacion', accion='Configuración de Emisor', detalle="Actualizó los datos del emisor.")
            messages.success(request, "Datos del emisor actualizados correctamente.")
            
        # SUB-BLOQUE POST: Modificación de Tasa de Impuestos
        elif 'action_iva' in request.POST:
            tab_activa = 'impuestos'
            try:
                config.iva_porcentaje = int(request.POST.get('iva_comercial', 12))
                config.save()
                
                Auditoria.objects.create(id_usuario=request.user, modulo='facturacion', accion='Configuración de Impuestos', detalle=f"Actualizó la tasa de IVA a {config.iva_porcentaje}%.")
                messages.success(request, "Configuración de impuestos guardada.")
            except ValueError:
                messages.error(request, "Porcentaje de IVA inválido.")
                
        # SUB-BLOQUE POST: Modificación de Archivos de Marca (Logo)
        elif 'action_marca' in request.POST:
            tab_activa = 'marca'
            
            # LINEA IMPORTANTE: Remueve físicamente el logo del servidor si se solicita explícitamente su eliminación
            if request.POST.get('eliminar_logo') == '1':
                if config.logo_restaurante:
                    config.logo_restaurante.delete(save=False) 
                    config.logo_restaurante = None
                config.save()
                
                Auditoria.objects.create(id_usuario=request.user, modulo='facturacion', accion='Configuración de Marca', detalle="Eliminó el logo del sistema.")
                messages.success(request, "Logo eliminado correctamente.")
            else:
                if 'logo_restaurante' in request.FILES:
                    config.logo_restaurante = request.FILES['logo_restaurante']
                config.save()
                
                Auditoria.objects.create(id_usuario=request.user, modulo='facturacion', accion='Configuración de Marca', detalle="Actualizó el logo del sistema.")
                messages.success(request, "Logo actualizado correctamente.")
                
        return redirect(f"{request.path}?tab={tab_activa}")

    tab_solicitada = request.GET.get('tab', 'empresa')

    return render(request, 'facturacion/configuracion_facturacion.html', {
        'config': config,
        'tab_solicitada': tab_solicitada
    })

@login_required
def configuracion_sistema(request):
    # Enrutador de compatibilidad para evitar enlaces rotos hacia el panel de configuraciones
    return redirect('configuracion_facturacion')