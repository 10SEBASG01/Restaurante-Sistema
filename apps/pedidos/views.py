import json
from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

# 🛡️ Importamos el guardián de permisos desde la aplicación de usuarios
from apps.usuarios.views import requiere_permiso

# 🎯 IMPORTAMOS AUDITORÍA
from apps.auditoria.models import Auditoria

# 📦 Modelos del sistema
from apps.pedidos.models import GestionPedido, DetallePedido, Comanda
from apps.menu.models import GestionPlatillo, CategoriasPlato
from apps.mesas.models import Mesa

@login_required
@requiere_permiso('modulo_pedidos')
def pedido_pantalla(request):
    """
    Renderiza la interfaz de toma de pedidos cargando los datos reales.
    Calcula dinámicamente la cantidad de platos disponibles por categoría.
    """
    platillos = GestionPlatillo.objects.filter(disponible=True, activo=True)
    
    categorias = CategoriasPlato.objects.annotate(
        total_productos=Count('platillos', filter=Q(platillos__disponible=True, platillos__activo=True))
    )
    
    mesas = Mesa.objects.filter(estado='ocupada')
    
    context = {
        'platillos': platillos,
        'categorias': categorias,
        'mesas': mesas,
    }
    return render(request, 'pedidos/crear_pedido.html', context)


@login_required
@requiere_permiso('modulo_pedidos')
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
            items = data.get('items', [])
            
            if not id_mesa or not items:
                return JsonResponse({'success': False, 'error': 'Datos incompletos.'}, status=400)
                
            # 1. Obtener la mesa y el empleado
            mesa = Mesa.objects.get(pk=id_mesa)
            empleado = request.user
            
            # 2. Crear la cabecera del pedido (Inicia como 'pendiente' para Caja)
            pedido = GestionPedido.objects.create(
                id_empleado=empleado,
                id_mesa=mesa,
                observaciones=observaciones,
                estado_pedido='pendiente'
            )
            
            # 3. Registrar los detalles del pedido
            total_items = 0
            for item in items:
                platillo_id = item.get('id_platillo') or item.get('id') or item.get('id_producto')
                
                if not platillo_id:
                    return JsonResponse({'success': False, 'error': f'Clave del platillo no encontrada: {item}'}, status=400)

                platillo = GestionPlatillo.objects.get(pk=platillo_id)
                amount = int(item.get('qty') or item.get('cantidad') or 1)
                total_items += amount

                DetallePedido.objects.create(
                    id_pedido=pedido,
                    id_platillo=platillo,
                    cantidad=amount, 
                    precio_unitario=platillo.precio 
                )
            
            # 4. Generar automáticamente la comanda de cocina vinculada
            Comanda.objects.create(
                id_pedido=pedido,
                estado_comanda='pendiente',
                nota_cocina=observaciones
            )
            
            # 🎯 5. CONEXIÓN A AUDITORÍA: Registrar la toma del pedido exitosamente
            Auditoria.objects.create(
                id_usuario=empleado,
                modulo='pedidos',
                accion='Pedido Creado',
                detalle=f"Generó pedido #{pedido.id_pedido} para Mesa {mesa.numero} ({total_items} platillos)."
            )
            
            return JsonResponse({'success': True, 'message': '¡Pedido enviado a cocina con éxito!', 'id_pedido': pedido.id_pedido})
            
        except Mesa.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'La mesa seleccionada no existe.'}, status=404)
        except GestionPlatillo.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Un platillo enviado no existe en la base de datos.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
            
    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

@login_required
@requiere_permiso('modulo_pedidos')
def mis_pedidos_mesero(request):
    """
    Subcaso 7.7: Consultar Estado del Pedido
    Muestra al mesero sus comandas activas y oculta automáticamente 
    aquellas que ya han sido entregadas a la mesa.
    """
    # 1. Traemos los pedidos del mesero actual
    pedidos_mesero = GestionPedido.objects.filter(
        id_empleado=request.user
    ).select_related('id_mesa').order_by('-id_pedido')
    
    pedidos_activos = []
    
    # 2. Vinculamos con su comanda y filtramos las que ya terminaron su ciclo
    for pedido in pedidos_mesero:
        comanda = Comanda.objects.filter(id_pedido=pedido).first()
        estado = comanda.estado_comanda if comanda else 'pendiente'
        
        # 🌟 FILTRO CRÍTICO: Si el estado ya es 'entregado', se ignora y no se añade a la lista
        if estado != 'entregado':
            pedido.estado_cocina = estado
            pedidos_activos.append(pedido)

    context = {
        'pedidos': pedidos_activos,  # Enviamos únicamente las comandas vivas o en proceso
    }
    
    return render(request, 'pedidos/mis_pedidos_mesero.html', context)

@login_required
@requiere_permiso('modulo_pedidos')
@transaction.atomic
def eliminar_pedido_api(request, id_pedido):
    """
    Permite al mesero cancelar un pedido de su lista SI Y SOLO SI
    su comanda asociada sigue con estado 'pendiente' en la cocina.
    """
    if request.method == 'POST':
        try:
            # 1. Buscar el pedido y su comanda asociada
            pedido = GestionPedido.objects.get(pk=id_pedido, id_empleado=request.user)
            comanda = Comanda.objects.filter(id_pedido=pedido).first()
            
            if not comanda:
                return JsonResponse({'success': False, 'error': 'No se encontró la comanda vinculada.'}, status=44)
            
            # 2. Validar que siga pendiente antes de borrar
            if comanda.estado_comanda != 'pendiente':
                return JsonResponse({
                    'success': False, 
                    'error': f'No puedes eliminar este pedido porque ya se encuentra {comanda.estado_comanda}.'
                }, status=400)
            
            # 3. Registrar acción en auditoría antes de limpiar
            Auditoria.objects.create(
                id_usuario=request.user,
                modulo='pedidos',
                accion='Pedido Cancelado/Eliminado',
                detalle=f"Canceló el pedido #{pedido.id_pedido} (Mesa {pedido.id_mesa.numero}) cuando estaba pendiente."
            )
            
            # 4. Eliminar el pedido de la base de datos (por cascada borrará sus detalles y comanda)
            pedido.delete()
            
            return JsonResponse({'success': True, 'message': 'El pedido fue cancelado y eliminado correctamente.'})
            
        except GestionPedido.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'El pedido no existe o no tienes permisos sobre él.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
            
    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)