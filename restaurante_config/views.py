import json
from datetime import timedelta, datetime
import zoneinfo
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, F, Count
from django.db.models.functions import TruncDate

# Importamos tus modelos oficiales 
from apps.facturacion.models import Factura
from apps.pedidos.models import GestionPedido, DetallePedido
from apps.auditoria.models import Auditoria
from apps.mesas.models import Mesa
from apps.reservas.models import Reserva 

# 🔥 AGREGADO: Importamos tu guardián de seguridad desde usuarios
from apps.usuarios.views import requiere_permiso

@login_required(login_url='login') 
@requiere_permiso('modulo_dashboard') # 🔥 CANDADO DE SEGURIDAD ASIGNADO
def dashboard_view(request):
    zona_ecuador = zoneinfo.ZoneInfo('America/Guayaquil')
    fecha_str = request.GET.get('fecha')
    
    if fecha_str:
        try:
            hoy = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            hoy = timezone.now().astimezone(zona_ecuador).date()
    else:
        hoy = timezone.now().astimezone(zona_ecuador).date()
        
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

    # 6. Top 5 Productos
    pedidos_facturados = GestionPedido.objects.filter(factura__in=facturas_semana)
    detalles_semana = DetallePedido.objects.filter(id_pedido__in=pedidos_facturados)
    
    top_productos = detalles_semana.values(
        'id_platillo__nombre_platillo', 
        'id_platillo__imagen'
    ).annotate(
        cantidad_total=Sum('cantidad'),
        recaudado=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-recaudado')[:5]

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