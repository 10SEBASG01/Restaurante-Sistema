from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q

# 🔥 AGREGADO: Importamos los escudos de seguridad
from django.contrib.auth.decorators import login_required
from apps.usuarios.views import requiere_permiso 

from .models import GestionPlatillo, CategoriasPlato
from .forms import PlatilloForm


# 🔥 AGREGADO: Escudos de seguridad para Menú
@login_required
@requiere_permiso('modulo_menu')
def menu_gestion(request):
    # AUTOMATIZACIÓN: Si la tabla de categorías está vacía, la poblamos con las 9 oficiales
    if not CategoriasPlato.objects.exists():
        for codigo, nombre in CategoriasPlato.CATEGORIAS_CHOICES:
            CategoriasPlato.objects.get_or_create(nombre_categoria=codigo)

    # 1. Obtener todas las categorías para pintar las pestañas superiores
    categorias = CategoriasPlato.objects.all()
    
    # 2. Capturar los filtros enviados por la URL (Request GET)
    # Por defecto arranca en 'Todos' a la izquierda
    categoria_activa = request.GET.get('categoria', 'Todos')
    busqueda = request.GET.get('search', '').strip()
    filtro_disponibilidad = request.GET.get('disponible', 'Todos')

    # 3. Construir la consulta base
    # 🔥 CORREGIDO: Filtramos para que siempre traiga solo los que tienen activo=True
    if categoria_activa == 'Todos' or busqueda:
        platillos_queryset = GestionPlatillo.objects.filter(activo=True)
    else:
        platillos_queryset = GestionPlatillo.objects.filter(
            id_categoria__nombre_categoria=categoria_activa,
            activo=True
        )

    # 4. Aplicar el filtro de la barra de búsqueda (si el usuario escribió algo)
    if busqueda:
        platillos_queryset = platillos_queryset.filter(
            Q(nombre_platillo__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )

    # 5. Aplicar el filtro del selector de estado (Disponible / No disponible)
    if filtro_disponibilidad == 'Disponible':
        platillos_queryset = platillos_queryset.filter(disponible=True)
    elif filtro_disponibilidad == 'No disponible':
        platillos_queryset = platillos_queryset.filter(disponible=False)

    # 6. Contadores globales para las estadísticas del Header
    # 🔥 CORREGIDO: Contamos solo los activos para que las métricas cuadren
    total_platillos = GestionPlatillo.objects.filter(activo=True).count()
    disponibles_count = GestionPlatillo.objects.filter(disponible=True, activo=True).count()

    context = {
        'platillos': platillos_queryset,
        'categorias': categorias,
        'categoria_activa': categoria_activa,
        'search': busqueda,
        'filtro_disponibilidad': filtro_disponibilidad,
        'total_platillos': total_platillos,
        'disponibles_count': disponibles_count,
    }
    
    return render(request, 'menu/menu_gestion.html', context)


# Función para crear el platillo en pantalla completa
# 🔥 AGREGADO: Escudos de seguridad para Menú
@login_required
@requiere_permiso('modulo_menu')
def crear_platillo(request):
    if not CategoriasPlato.objects.exists():
        for codigo, nombre in CategoriasPlato.CATEGORIAS_CHOICES:
            CategoriasPlato.objects.get_or_create(nombre_categoria=codigo)

    if request.method == 'POST':
        form = PlatilloForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('menu:menu_gestion')
    else:
        form = PlatilloForm()
    
    return render(request, 'menu/agregar_platillo.html', {'form': form, 'editando': False})


# Función para editar un platillo existente
# 🔥 AGREGADO: Escudos de seguridad para Menú
@login_required
@requiere_permiso('modulo_menu')
def editar_platillo(request, id_platillo):
    platillo = get_object_or_404(GestionPlatillo, pk=id_platillo)
    
    if request.method == 'POST':
        form = PlatilloForm(request.POST, request.FILES, instance=platillo)
        if form.is_valid():
            form.save()
            return redirect('menu:menu_gestion')
    else:
        form = PlatilloForm(instance=platillo)
    
    context = {
        'form': form,
        'editando': True,
        'platillo': platillo
    }
    return render(request, 'menu/agregar_platillo.html', context)


# Función para eliminar un platillo de inmediato
# 🔥 AGREGADO: Escudos de seguridad para Menú
@login_required
@requiere_permiso('modulo_menu')
def eliminar_platillo(request, id_platillo):
    # Buscamos el platillo que tenga esa Primary Key
    platillo = get_object_or_404(GestionPlatillo, pk=id_platillo)
    
    # SI EL USUARIO HACE POST (Dio clic en "Sí, Eliminar" en la pantalla roja)
    if request.method == 'POST':
        # 🔥 CORREGIDO: Aplicamos el borrado lógico de forma segura
        platillo.activo = False
        platillo.save()
        return redirect('menu:menu_gestion')
        
    # SI EL USUARIO HACE GET (Viene de dar clic a la basura en el menú principal)
    # Simplemente pintamos la plantilla de confirmación pasándole el objeto 'platillo'
    return render(request, 'menu/eliminar_platillo.html', {'platillo': platillo})