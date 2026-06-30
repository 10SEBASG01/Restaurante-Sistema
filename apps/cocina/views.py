import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from django.contrib.auth.decorators import login_required

# Importamos los modelos de pedidos
from apps.pedidos.models import Comanda

# --- LÓGICA DE ACCESO ---
def acceso_cocina(request):
    usuario = request.user

    if usuario.is_superuser:
        return True

    if hasattr(usuario, 'rol') and usuario.rol in [
        'administrador',
        'cocinero' 
    ]:
        return True

    tiene_permiso = usuario.user_permissions.filter(
        codename='modulo_cocina'
    ).exists()

    return tiene_permiso
# ------------------------


@login_required
def tablero_cocina(request):
    if not acceso_cocina(request):
        return render(
            request,
            'errors/acceso_denegado.html',
            status=403
        )
    return render(request, 'cocina/tablero_cocina.html')


@login_required
def api_comandas_activas(request):
    if not acceso_cocina(request):
        return JsonResponse({"error": "Acceso denegado"}, status=403)

    try:
        comandas = Comanda.objects.filter(
            estado_comanda__in=['pendiente', 'en_preparacion', 'lista']
        ).select_related('id_pedido__id_mesa').order_by('fecha_emision')

        comandas_dict = {}

        for comanda in comandas:
            raw_id = comanda.id_comanda
            id_comanda = f"#{raw_id:03d}"
            
            pedido = comanda.id_pedido
            numero_mesa = pedido.id_mesa.numero if (pedido and pedido.id_mesa) else "N/A"
            texto_mesa = f"Mesa {numero_mesa}"
            estado_db = comanda.estado_comanda
            
            # Capturamos la nota o comentario general de la comanda
            nota_general = comanda.nota_cocina or ""
            
            if comanda.fecha_emision:
                try:
                    created_at = int(comanda.fecha_emision.timestamp() * 1000)
                except AttributeError:
                    created_at = int(timezone.now().timestamp() * 1000)
            else:
                created_at = int(timezone.now().timestamp() * 1000)

            estado_frontend = 'pendiente'
            if estado_db == 'en_preparacion' or estado_db == 'preparing':
                estado_frontend = 'en_preparacion'
            elif estado_db == 'lista' or estado_db == 'ready':
                estado_frontend = 'lista'

            if raw_id not in comandas_dict:
                comandas_dict[raw_id] = {
                    "id": id_comanda,
                    "id_comanda": raw_id,
                    "raw_id": raw_id,
                    "id_pedido": f"#{pedido.id_pedido}" if pedido else "N/A",
                    "table": texto_mesa,
                    "mesa": texto_mesa,
                    "numero_mesa": numero_mesa,
                    "status": estado_frontend,  
                    "estado": estado_db,
                    "createdAt": created_at,
                    "fecha_emision": created_at,
                    # Dejamos la observación limpia a nivel de cabecera de la orden
                    "observaciones": nota_general.strip(),
                    "items": []
                }

            if pedido:
                detalles = pedido.detalles.all().select_related('id_platillo')
                for detalle in detalles:
                    if detalle.id_platillo:
                        nombre_plato = detalle.id_platillo.nombre_platillo
                        
                        comandas_dict[raw_id]["items"].append({
                            "name": nombre_plato,
                            "nombre": nombre_plato,
                            "qty": detalle.cantidad,
                            "cantidad": detalle.cantidad
                        })

        return JsonResponse(list(comandas_dict.values()), safe=False)
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@ensure_csrf_cookie
@require_POST
@login_required
def api_avanzar_comanda(request):
    if not acceso_cocina(request):
        return JsonResponse({"error": "Acceso denegado"}, status=403)

    try:
        data = json.loads(request.body)
        comanda_id = data.get('id') or data.get('id_comanda')
        
        comanda = Comanda.objects.select_related('id_pedido').get(id_comanda=comanda_id)
        estado_actual = comanda.estado_comanda
        nuevo_estado = None
        
        if estado_actual == 'pendiente':
            nuevo_estado = 'en_preparacion'
        elif estado_actual == 'en_preparacion':
            nuevo_estado = 'lista'
        elif estado_actual == 'lista':
            nuevo_estado = 'entregado' 
            
        if nuevo_estado:
            comanda.estado_comanda = nuevo_estado
            comanda.save()
            
            if comanda.id_pedido:
                pedido = comanda.id_pedido
                if nuevo_estado == 'en_preparacion':
                    pedido.estado_pedido = 'en_preparacion'
                elif nuevo_estado == 'lista':
                    pedido.estado_pedido = 'listo'
                elif nuevo_estado == 'entregado':
                    pedido.estado_pedido = 'entregado'
                pedido.save()
            
        return JsonResponse({"success": True, "nuevo_estado": nuevo_estado})
        
    except Comanda.DoesNotExist:
        return JsonResponse({"error": "Comanda no encontrada"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)