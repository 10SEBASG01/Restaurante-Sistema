import json
from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

# 🛡️ Importamos el guardián de permisos desde la aplicación de usuarios
from apps.usuarios.views import requiere_permiso

# 📦 Modelos del sistema
from apps.pedidos.models import GestionPedido, DetallePedido, Comanda
from apps.menu.models import GestionPlatillo, CategoriasPlato
from apps.mesas.models import Mesa

@login_required
@requiere_permiso('modulo_pedidos')  # 🛡️ ESCUDO ACTIVADO
def pedido_pantalla(request):
    """
    Renderiza la interfaz de toma de pedidos cargando los datos reales.
    Calcula dinámicamente la cantidad de platos disponibles por categoría.
    """
    # 🔥 AQUÍ ATRAPAMOS AL FANTASMA: Añadimos activo=True a la consulta
    platillos = GestionPlatillo.objects.filter(disponible=True, activo=True)
    
    # 🔥 Y TAMBIÉN AQUÍ: Actualizamos el contador para que las burbujas amarillas de las categorías no cuenten platillos borrados
    categorias = CategoriasPlato.objects.annotate(
        total_productos=Count('platillos', filter=Q(platillos__disponible=True, platillos__activo=True))
    )
    
    # Muestra las mesas listas para ordenar
    mesas = Mesa.objects.filter(estado='ocupada')
    
    context = {
        'platillos': platillos,
        'categorias': categorias,
        'mesas': mesas,
    }
    return render(request, 'pedidos/crear_pedido.html', context)


@login_required
@requiere_permiso('modulo_pedidos')  # 🛡️ ESCUDO ACTIVADO
@transaction.atomic
def guardar_pedido_api(request):
    """
    Endpoint que recibe el JSON del pedido actual, guarda la cabecera,
    los detalles correspondientes y dispara la comanda para la cocina.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            id_mesa = data.get('id_mesa')
            observaciones = data.get('observaciones', '')
            items = data.get('items', [])  # [{id_platillo: 1, qty: 2}, ...]
            
            if not id_mesa or not items:
                return JsonResponse({'success': False, 'error': 'Datos incompletos.'}, status=400)
                
            # 1. Obtener la mesa y el empleado
            mesa = Mesa.objects.get(pk=id_mesa)
            empleado = request.user
            
            # 2. Crear la cabecera del pedido (CORREGIDO: Ahora inicia como 'pendiente')
            pedido = GestionPedido.objects.create(
                id_empleado=empleado,
                id_mesa=mesa,
                observaciones=observaciones,
                estado_pedido='pendiente'  # <-- CAMBIO AQUÍ: Nace en pendiente para pintar ROJO en caja
            )
            
            # 3. Registrar los detalles del pedido
            for item in items:
                platillo_id = item.get('id_platillo') or item.get('id') or item.get('id_producto')
                
                if not platillo_id:
                    return JsonResponse({
                        'success': False, 
                        'error': f'No se encontró la clave del platillo en el item: {item}'
                    }, status=400)

                # Nos aseguramos de buscar el platillo
                platillo = GestionPlatillo.objects.get(pk=platillo_id)
                amount = item.get('qty') or item.get('cantidad') or 1

                DetallePedido.objects.create(
                    id_pedido=pedido,
                    id_platillo=platillo,
                    cantidad=int(amount), 
                    precio_unitario=platillo.precio 
                )
            
            # 4. Generar automáticamente la comanda de cocina vinculada
            Comanda.objects.create(
                id_pedido=pedido,
                estado_comanda='pendiente',
                nota_cocina=observaciones
            )
            
            return JsonResponse({'success': True, 'message': '¡Pedido enviado a cocina con éxito!', 'id_pedido': pedido.id_pedido})
            
        except Mesa.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'La mesa seleccionada no existe.'}, status=404)
        except GestionPlatillo.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Uno de los platillos enviados no existe en la base de datos.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
            
    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)