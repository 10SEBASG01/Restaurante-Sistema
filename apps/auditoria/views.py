from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import datetime
from .models import Auditoria

@login_required(login_url='login')
def auditoria_lista(request):
    # 1. Empezamos con todos los registros
    logs = Auditoria.objects.all().order_by('-fecha_hora')
    
    # 2. Atrapamos lo que el usuario escribió en los filtros
    usuario_query = request.GET.get('usuario', '')
    fecha_query = request.GET.get('fecha', '')
    
    # 3. Si escribió algo en "usuario", filtramos por username, nombre o apellido
    if usuario_query:
        logs = logs.filter(
            Q(id_usuario__username__icontains=usuario_query) |
            Q(id_usuario__first_name__icontains=usuario_query) |
            Q(id_usuario__last_name__icontains=usuario_query)
        )
        
    # 4. Si seleccionó una fecha exacta, filtramos el día
    if fecha_query:
        try:
            fecha_obj = datetime.strptime(fecha_query, '%Y-%m-%d').date()
            logs = logs.filter(fecha_hora__date=fecha_obj)
        except ValueError:
            pass
            
    # 5. Pasamos los datos filtrados y también las palabras buscadas 
    # para que no se borren de las cajitas de texto al recargar la página
    context = {
        'logs': logs,
        'usuario_query': usuario_query,
        'fecha_query': fecha_query,
    }
    
    return render(request, 'auditoria/lista.html', context)