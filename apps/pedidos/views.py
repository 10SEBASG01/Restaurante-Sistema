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