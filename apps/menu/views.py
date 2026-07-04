from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from apps.usuarios.views import requiere_permiso 
from apps.auditoria.models import Auditoria  # 🔥 Importamos el modelo de Auditoría

from .models import GestionPlatillo, CategoriasPlato
from .forms import PlatilloForm

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
    categoria_activa = request.GET.get('categoria', 'Todos')
    busqueda = request.GET.get('search', '').strip()
    filtro_disponibilidad = request.GET.get('disponible', 'Todos')

    # 3. Construir la consulta base
    if categoria_activa == 'Todos' or busqueda:
        platillos_queryset = GestionPlatillo.objects.filter(activo=True)
    else:
        platillos_queryset = GestionPlatillo.objects.filter(
            id_categoria__nombre_categoria=categoria_activa,
            activo=True
        )

    # 4. Aplicar el filtro de la barra de búsqueda
    if busqueda:
        platillos_queryset = platillos_queryset.filter(
            Q(nombre_platillo__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )

    # 5. Aplicar el filtro del selector de estado
    if filtro_disponibilidad == 'Disponible':
        platillos_queryset = platillos_queryset.filter(disponible=True)
    elif filtro_disponibilidad == 'No disponible':
        platillos_queryset = platillos_queryset.filter(disponible=False)

    # 6. Contadores globales para las estadísticas del Header
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


@login_required
@requiere_permiso('modulo_menu')
def crear_platillo(request):
    if not CategoriasPlato.objects.exists():
        for codigo, nombre in CategoriasPlato.CATEGORIAS_CHOICES:
            CategoriasPlato.objects.get_or_create(nombre_categoria=codigo)

    if request.method == 'POST':
        form = PlatilloForm(request.POST, request.FILES)
        if form.is_valid():
            platillo = form.save()
            
            # 🎯 Auditoría: Creación de platillo
            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='menu',
                accion='Platillo Creado',
                detalle=f"Añadió al menú: {platillo.nombre_platillo} (${platillo.precio})"
            )
            
            return redirect('menu:menu_gestion')
    else:
        form = PlatilloForm()
    
    return render(request, 'menu/agregar_platillo.html', {'form': form, 'editando': False})


@login_required
@requiere_permiso('modulo_menu')
def editar_platillo(request, id_platillo):
    platillo = get_object_or_404(GestionPlatillo, pk=id_platillo)
    precio_viejo = platillo.precio  # Guardamos el precio original antes de editar
    
    if request.method == 'POST':
        form = PlatilloForm(request.POST, request.FILES, instance=platillo)
        if form.is_valid():
            platillo_guardado = form.save()
            
            # 🎯 Auditoría: Edición de platillo
            detalle_audit = f"Actualizó datos de: {platillo_guardado.nombre_platillo}"
            
            if precio_viejo != platillo_guardado.precio:
                detalle_audit += f" (Precio cambió de ${precio_viejo} a ${platillo_guardado.precio})"
                
            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='menu',
                accion='Platillo Editado',
                detalle=detalle_audit
            )
            
            return redirect('menu:menu_gestion')
    else:
        form = PlatilloForm(instance=platillo)
    
    context = {
        'form': form,
        'editando': True,
        'platillo': platillo
    }
    return render(request, 'menu/agregar_platillo.html', context)


@login_required
@requiere_permiso('modulo_menu')
def eliminar_platillo(request, id_platillo):
    platillo = get_object_or_404(GestionPlatillo, pk=id_platillo)
    
    if request.method == 'POST':
        platillo.activo = False
        platillo.save()
        
        # 🎯 Auditoría: Borrado lógico de platillo
        Auditoria.objects.create(
            id_usuario=request.user,
            modulo='menu',
            accion='Platillo Eliminado',
            detalle=f"Dio de baja el platillo: {platillo.nombre_platillo}"
        )
        
        return redirect('menu:menu_gestion')
        
    return render(request, 'menu/eliminar_platillo.html', {'platillo': platillo})