# Configuracion de entorno y herramientas
# Este bloque inicial importa las librerías necesarias para el procesamiento de
# datos, la gestión de fechas, la seguridad de acceso y la interacción con la base de datos.
# Se incluyen utilidades estándar de Python (json, datetime), herramientas de 
# configuración regional (zoneinfo), decoradores de control de acceso de Django, 
# y funciones avanzadas del ORM para realizar cálculos estadísticos y 
# transformaciones de fechas requeridas en los reportes del dashboard.
import json
from datetime import timedelta, datetime
import zoneinfo
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, F, Count
from django.db.models.functions import TruncDate

# Importamos los modelos de las diferentes aplicaciones del sistema.
# Esto nos permite consultar las tablas de la base de datos.
from apps.facturacion.models import Factura
from apps.pedidos.models import GestionPedido, DetallePedido
from apps.auditoria.models import Auditoria
from apps.mesas.models import Mesa
from apps.reservas.models import Reserva 

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
    # Suma el total de todas las facturas emitidas en la fecha seleccionada.
    ventas_hoy_query = Factura.objects.filter(
        fecha_emision__date=hoy
    ).aggregate(total_hoy=Sum('total'))
    # Si no hay ventas, asignamos 0 para evitar errores en la vista.
    ventas_hoy = ventas_hoy_query['total_hoy'] or 0

    # 2. KPI: Pedidos Activos
    # Cuenta cuántos pedidos están pendientes de entrar a cocina o en preparación.
    pedidos_activos = GestionPedido.objects.filter(estado_pedido__in=['pendiente', 'en_preparacion']).count()

    # 3. KPI: Reservas del Día Seleccionado
    # Cuenta cuántas mesas están reservadas para hoy y ya fueron confirmadas.
    reservas_hoy = Reserva.objects.filter(fecha=hoy, estado='CONFIRMADA').count()

    # 4. KPI & Gráfica Dona: Estado de Mesas 
    # Extraemos el total de mesas y cómo están distribuidas según su estado.
    mesas_totales = Mesa.objects.count()
    mesas_ocupadas = Mesa.objects.filter(estado='ocupada').count()
    mesas_libres = Mesa.objects.filter(estado='libre').count()
    mesas_reservadas = Mesa.objects.filter(estado='reservada').count()

    # 5. Gráfica de Líneas: Últimos 7 días
    # Obtenemos todas las facturas de la última semana.
    facturas_semana = Factura.objects.filter(fecha_emision__date__range=(desde, hoy))
    
    # Agrupamos esas facturas por día y sumamos el total recaudado diariamente.
    ventas_diarias = facturas_semana.annotate(
        dia=TruncDate('fecha_emision')
    ).values('dia').annotate(
        total=Sum('total')
    ).order_by('dia')
    
    # Diccionario para traducir los días al español y mostrarlos bonitos en la gráfica.
    dias_semana_es = {
        'Monday': 'Lun', 'Tuesday': 'Mar', 'Wednesday': 'Mié',
        'Thursday': 'Jue', 'Friday': 'Vie', 'Saturday': 'Sáb', 'Sunday': 'Dom'
    }
    
    # Preparamos las listas exactas que necesita JavaScript para dibujar la gráfica.
    chart_labels = [dias_semana_es[r['dia'].strftime('%A')] for r in ventas_diarias]
    chart_data = [float(r['total']) for r in ventas_diarias]
    
    # Calculamos el total de dinero que entró en esos 7 días.
    ventas_7_dias = sum(chart_data)

    # 6. Top 5 Productos
    # Buscamos qué platillos se vendieron en las facturas de esta semana.
    pedidos_facturados = GestionPedido.objects.filter(factura__in=facturas_semana)
    detalles_semana = DetallePedido.objects.filter(id_pedido__in=pedidos_facturados)
    
    # Agrupamos por platillo, sumamos la cantidad vendida y multiplicamos por el precio para saber cuánto recaudó cada uno.
    # El order_by('-recaudado') ordena de mayor a menor y el [:5] nos devuelve solo los 5 mejores.
    top_productos = detalles_semana.values(
        'id_platillo__nombre_platillo', 
        'id_platillo__imagen'
    ).annotate(
        cantidad_total=Sum('cantidad'),
        recaudado=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-recaudado')[:5]

    # 7. Auditoría
    # Trae los 5 eventos más recientes del sistema (logins, modificaciones, etc.) para el historial.
    actividad_reciente = Auditoria.objects.all().order_by('-fecha_hora')[:5]

    # Empaquetamos todas las variables que calculamos en un diccionario ('context').
    # Esto es lo que le enviamos al archivo HTML para que pueda imprimir los datos.
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
    
    # Renderizamos la plantilla con toda la información calculada.
    return render(request, 'panel_principal.html', context)