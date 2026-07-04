from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import datetime
from .models import Auditoria

@login_required(login_url='login')
def auditoria_lista(request):
    # 🎯 OPTIMIZACIÓN: select_related evita consultas repetitivas por cada usuario en el bucle HTML
    logs = Auditoria.objects.all().select_related('id_usuario').order_by('-fecha_hora')
    
    # Captura de parámetros desde los formularios de filtrado en el HTML
    usuario_query = request.GET.get('usuario', '')
    fecha_query = request.GET.get('fecha', '')
    
    # Filtro por username, primer nombre o apellido
    if usuario_query:
        logs = logs.filter(
            Q(id_usuario__username__icontains=usuario_query) |
            Q(id_usuario__first_name__icontains=usuario_query) |
            Q(id_usuario__last_name__icontains=usuario_query)
        )
        
    # Filtro por fecha exacta (Año-Mes-Día)
    if fecha_query:
        try:
            fecha_obj = datetime.strptime(fecha_query, '%Y-%m-%d').date()
            logs = logs.filter(fecha_hora__date=fecha_obj)
        except ValueError:
            pass # Si la fecha viene corrupta o incompleta, ignora el filtro
            
    context = {
        'logs': logs,
        'usuario_query': usuario_query,
        'fecha_query': fecha_query,
    }
    
    return render(request, 'auditoria/lista.html', context)