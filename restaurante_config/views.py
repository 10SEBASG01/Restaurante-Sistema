# Configuracion de entorno y herramientas
# Este bloque inicial importa las librerías necesarias para el procesamiento de
# datos, la gestión de fechas, la seguridad de acceso y la interacción con la base de datos.
import json
from datetime import timedelta, datetime
import zoneinfo
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, F, Count
from django.db.models.functions import TruncDate

# Importamos los modelos de las diferentes aplicaciones del sistema.
from apps.facturacion.models import Factura
from apps.pedidos.models import GestionPedido, DetallePedido
from apps.auditoria.models import Auditoria
from apps.mesas.models import Mesa
from apps.reservas.models import Reserva 
from apps.menu.models import GestionPlatillo # <-- AGREGADO: Importamos el modelo de Platillos

# Importamos el guardián de seguridad personalizado.
from apps.usuarios.views import requiere_permiso

# Protegemos la vista: solo usuarios logueados y con el permiso 'modulo_dashboard' pueden entrar.
@login_required(login_url='login') 
@requiere_permiso('modulo_dashboard')
def dashboard_view(request):
    # Configuramos la zona horaria a Guayaquil para asegurar que los cortes 
    # de caja y fechas de reservas coincidan exactamente con la hora local.
    zona_ecuador = zoneinfo.ZoneInfo('America/Guayaquil')
    
    # Verificamos si el usuario seleccionó una fecha específica en el calendario del dashboard.
    fecha_str = request.GET.get('fecha')
    
    if fecha_str:
        try:
            # Si hay fecha en la URL, la convertimos a formato fecha.
            hoy = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            # Si la fecha tiene un formato inválido, por seguridad tomamos la fecha actual.
            hoy = timezone.now().astimezone(zona_ecuador).date()
    else:
        # Por defecto, cargamos la información del día de hoy.
        hoy = timezone.now().astimezone(zona_ecuador).date()
        
    # Calculamos la fecha de hace 6 días para poder sacar el rango de la semana (7 días total).
    desde = hoy - timedelta(days=6)

    # 1. KPI: Ventas del Día
    ventas_hoy_query = Factura.objects.filter(
        fecha_emision__date=hoy
    ).aggregate(total_hoy=Sum('total'))
    ventas_hoy = ventas_hoy_query['total_hoy'] or 0

    # 2. KPI: Pedidos Activos
    pedidos_activos = GestionPedido.objects.filter(estado_pedido__in=['pendiente', 'en_preparacion']).count()

    # 3. KPI: Reservas del Día Seleccionado
    reservas_hoy = Reserva.objects.filter(fecha=hoy, estado='CONFIRMADA').count()

    # 4. KPI & Gráfica Dona: Estado de Mesas 
    mesas_totales = Mesa.objects.count()
    mesas_ocupadas = Mesa.objects.filter(estado='ocupada').count()
    mesas_libres = Mesa.objects.filter(estado='libre').count()
    mesas_reservadas = Mesa.objects.filter(estado='reservada').count()

    # 5. Gráfica de Líneas: Últimos 7 días
    facturas_semana = Factura.objects.filter(fecha_emision__date__range=(desde, hoy))
    
    ventas_diarias = facturas_semana.annotate(
        dia=TruncDate('fecha_emision')
    ).values('dia').annotate(
        total=Sum('total')
    ).order_by('dia')
    
    dias_semana_es = {
        'Monday': 'Lun', 'Tuesday': 'Mar', 'Wednesday': 'Mié',
        'Thursday': 'Jue', 'Friday': 'Vie', 'Saturday': 'Sáb', 'Sunday': 'Dom'
    }
    
    chart_labels = [dias_semana_es[r['dia'].strftime('%A')] for r in ventas_diarias]
    chart_data = [float(r['total']) for r in ventas_diarias]
    
    ventas_7_dias = sum(chart_data)

    # 6. Top 5 Productos (CORREGIDO)
    pedidos_facturados = GestionPedido.objects.filter(factura__in=facturas_semana)
    detalles_semana = DetallePedido.objects.filter(id_pedido__in=pedidos_facturados)
    
    # Primero obtenemos los IDs y calculamos totales
    top_detalles = detalles_semana.values(
        'id_platillo'
    ).annotate(
        cantidad_total=Sum('cantidad'),
        recaudado=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-recaudado')[:5]

    # Convertimos los resultados en instancias del modelo GestionPlatillo
    top_productos = []
    for detalle in top_detalles:
        try:
            platillo = GestionPlatillo.objects.get(pk=detalle['id_platillo'])
            # Le inyectamos temporalmente los valores calculados para usarlos en el HTML
            platillo.cantidad_total = detalle['cantidad_total']
            platillo.recaudado = detalle['recaudado']
            top_productos.append(platillo)
        except GestionPlatillo.DoesNotExist:
            continue

    # 7. Auditoría
    actividad_reciente = Auditoria.objects.all().order_by('-fecha_hora')[:5]

    context = {
        'ventas_hoy': ventas_hoy,          
        'pedidos_activos': pedidos_activos,
        'reservas_hoy': reservas_hoy,
        'mesas_ocupadas': mesas_ocupadas,  
        'mesas_totales': mesas_totales,
        'mesas_libres': mesas_libres,
        'mesas_reservadas': mesas_reservadas,
        'ventas_7_dias': ventas_7_dias,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'top_productos': top_productos,
        'actividad_reciente': actividad_reciente,
        'fecha_actual': hoy,
    }
    
    return render(request, 'panel_principal.html', context)