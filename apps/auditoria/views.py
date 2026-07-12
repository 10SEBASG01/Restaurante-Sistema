from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import datetime
from .models import Auditoria

@login_required(login_url='login')
def auditoria_lista(request):
    """
    🎯 VISTA DE LISTADO DE AUDITORÍA
    
    Renderiza la tabla del historial de acciones del ERP "Sabor & Arte".
    Incluye un motor de búsqueda integrado para filtrar los registros 
    por nombre de usuario o por una fecha específica.
    
    Args:
        request: Objeto HttpRequest que contiene los datos de la sesión y parámetros GET.
        
    Returns:
        HttpResponse con la plantilla 'auditoria/lista.html' renderizada y el contexto.
    """

    # ==========================================
    # 🚀 1. CONSULTA BASE Y OPTIMIZACIÓN
    # ==========================================
    
    # 🎯 OPTIMIZACIÓN CLAVE: Usamos 'select_related' para hacer un JOIN en la base de datos 
    # y traer los datos de los usuarios en una sola consulta. Esto evita el problema de 
    # "N+1 queries" cuando el HTML recorre los logs en un bucle 'for', mejorando el rendimiento.
    logs = Auditoria.objects.all().select_related('id_usuario').order_by('-fecha_hora')
    
    # ==========================================
    # 📥 2. CAPTURA DE PARÁMETROS DE BÚSQUEDA
    # ==========================================
    
    # Obtenemos los valores enviados por el formulario GET (barra de búsqueda y selectores).
    # Usamos '' como valor por defecto para evitar errores si el parámetro viene vacío o no existe.
    usuario_query = request.GET.get('usuario', '')
    fecha_query = request.GET.get('fecha', '')
    
    # ==========================================
    # 🔍 3. APLICACIÓN DE FILTROS DINÁMICOS
    # ==========================================
    
    # --- FILTRO POR USUARIO ---
    if usuario_query:
        # Usamos objetos 'Q' para hacer búsquedas condicionales múltiples (OR lógicos).
        # Revisa si el texto ingresado coincide con el username, el nombre o el apellido.
        logs = logs.filter(
            Q(id_usuario__username__icontains=usuario_query) |
            Q(id_usuario__first_name__icontains=usuario_query) |
            Q(id_usuario__last_name__icontains=usuario_query)
        )
        
    # --- FILTRO POR FECHA EXACTA ---
    if fecha_query:
        try:
            # Convierte el string del HTML ('YYYY-MM-DD') a un objeto de fecha (Date) de Python
            fecha_obj = datetime.strptime(fecha_query, '%Y-%m-%d').date()
            # Filtra ignorando la hora exacta, buscando solo coincidencias en ese día específico
            logs = logs.filter(fecha_hora__date=fecha_obj)
        except ValueError:
            # 🛡️ Sistema de seguridad: Si alguien manipula la URL e inyecta una fecha corrupta, 
            # simplemente ignoramos el filtro en lugar de tumbar el servidor con un Error 500.
            pass 
            
    # ==========================================
    # 📦 4. CONTEXTO Y RENDERIZADO
    # ==========================================
    
    # Empaquetamos los datos y los términos de búsqueda para enviarlos al frontend.
    # Pasar las variables '_query' de vuelta permite que los inputs del HTML mantengan 
    # escrito lo que el usuario acaba de buscar, mejorando la experiencia de usuario (UX).
    context = {
        'logs': logs,
        'usuario_query': usuario_query,
        'fecha_query': fecha_query,
    }
    
    return render(request, 'auditoria/lista.html', context)