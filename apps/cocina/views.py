import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from django.contrib.auth.decorators import login_required

# Importación del modelo central de la cocina
from apps.pedidos.models import Comanda

# =========================================================================
# BLOQUE 1: CONTROL DE ACCESO Y SEGURIDAD
# =========================================================================
def acceso_cocina(request):
    """
    Centraliza las reglas de negocio para permitir la entrada al módulo.
    Evalúa jerárquicamente: Superusuario -> Roles explícitos -> Permiso específico.
    """
    usuario = request.user

    # 1. Los superusuarios se saltan cualquier restricción
    if usuario.is_superuser:
        return True

    # 2. Control por rol asignado en el perfil del usuario
    if hasattr(usuario, 'rol') and usuario.rol in ['administrador', 'cocinero']:
        return True

    # 3. Control granular por sistema de permisos nativo de Django
    tiene_permiso = usuario.user_permissions.filter(
        codename='modulo_cocina'
    ).exists()

    return tiene_permiso


# =========================================================================
# BLOQUE 2: RENDERIZADO DEL TABLERO (VISTA PRINCIPAL)
# =========================================================================
@login_required
def tablero_cocina(request):
    """
    Carga la interfaz gráfica base del tablero de cocina.
    Sirve como contenedor para que luego el JavaScript consuma la API.
    """
    if not acceso_cocina(request):
        return render(
            request,
            'errors/acceso_denegado.html',
            status=403
        )
    return render(request, 'cocina/tablero_cocina.html')


# =========================================================================
# BLOQUE 3: API - CONSULTA DE COMANDAS ACTIVAS (GET)
# =========================================================================
@login_required
def api_comandas_activas(request):
    """
    Endpoint que retorna las comandas en curso en formato JSON.
    Agrupa los platos dentro de sus respectivas cabeceras de comanda.
    """
    if not acceso_cocina(request):
        return JsonResponse({"error": "Acceso denegado"}, status=403)

    try:
        # OPTIMIZACIÓN: select_related evita consultas repetitivas al traer mesa y pedido de un solo golpe
        comandas = Comanda.objects.filter(
            estado_comanda__in=['pendiente', 'en_preparacion', 'lista']
        ).select_related('id_pedido__id_mesa').order_by('fecha_emision')

        comandas_dict = {}

        for comanda in comandas:
            raw_id = comanda.id_comanda
            id_comanda = f"#{raw_id:03d}" # Formatea el ID visualmente (Ej: #005)
            
            pedido = comanda.id_pedido
            numero_mesa = pedido.id_mesa.numero if (pedido and pedido.id_mesa) else "N/A"
            texto_mesa = f"Mesa {numero_mesa}"
            estado_db = comanda.estado_comanda
            nota_general = comanda.nota_cocina or ""
            
            # Conversión de fechas a milisegundos para compatibilidad nativa con JavaScript (new Date())
            if comanda.fecha_emision:
                try:
                    created_at = int(comanda.fecha_emision.timestamp() * 1000)
                except AttributeError:
                    created_at = int(timezone.now().timestamp() * 1000)
            else:
                created_at = int(timezone.now().timestamp() * 1000)

            # Homologación de estados con el CSS/Frontend
            estado_frontend = 'pendiente'
            if estado_db in ['en_preparacion', 'preparing']:
                estado_frontend = 'en_preparacion'
            elif estado_db in ['lista', 'ready']:
                estado_frontend = 'lista'

            # Estructuración del JSON de la comanda (Cabecera)
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
                    "observaciones": nota_general.strip(),
                    "items": [] # Lista donde se inyectarán los platos abajo
                }

            # Extracción y anexado de los platos (Detalle del Pedido)
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

        # safe=False permite enviar una lista directamente en lugar de un objeto JSON forzado
        return JsonResponse(list(comandas_dict.values()), safe=False)
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =========================================================================
# BLOQUE 4: API - MÁQUINA DE ESTADOS Y AVANCE DE COMANDA (POST)
# =========================================================================
@ensure_csrf_cookie # Asegura que el cliente reciba el token CSRF para peticiones seguras
@require_POST       # Restringe el endpoint para que solo acepte peticiones POST
@login_required
def api_avanzar_comanda(request):
    """
    Flujo secuencial de estados de la cocina. 
    Actualiza tanto la comanda de cocina como el estado global del pedido de la mesa.
    """
    if not acceso_cocina(request):
        return JsonResponse({"error": "Acceso denegado"}, status=403)

    try:
        data = json.loads(request.body)
        comanda_id = data.get('id') or data.get('id_comanda')
        
        comanda = Comanda.objects.select_related('id_pedido', 'id_pedido__id_mesa').get(id_comanda=comanda_id)
        estado_actual = comanda.estado_comanda
        nuevo_estado = None
        
        # MÁQUINA DE ESTADOS: Define estrictamente el siguiente paso del ciclo de vida
        if estado_actual == 'pendiente':
            nuevo_estado = 'en_preparacion'
        elif estado_actual == 'en_preparacion':
            nuevo_estado = 'lista'
        elif estado_actual == 'lista':
            nuevo_estado = 'entregado' 
            
        if nuevo_estado:
            # 1. Actualizar comanda de cocina
            comanda.estado_comanda = nuevo_estado
            comanda.save()
            
            # 2. Sincronizar el estado del pedido general para el mesero/caja
            if comanda.id_pedido:
                pedido = comanda.id_pedido
                if nuevo_estado == 'en_preparacion':
                    pedido.estado_pedido = 'en_preparacion'
                elif nuevo_estado == 'lista':
                    pedido.estado_pedido = 'listo'
                elif nuevo_estado == 'entregado':
                    pedido.estado_pedido = 'entregado'
                pedido.save()
            
            # 3. Registro en Auditoría: Solo se ejecuta al cerrar con éxito el ciclo ('entregado')
            if nuevo_estado == 'entregado':
                from apps.auditoria.models import Auditoria
                Auditoria.objects.create(
                    id_usuario=request.user,
                    modulo='pedidos',
                    accion='Pedido Entregado',
                    detalle=f"Despachó el pedido #{comanda.id_pedido.id_pedido} (Mesa {comanda.id_pedido.id_mesa.numero})."
                )
            
        return JsonResponse({"success": True, "nuevo_estado": nuevo_estado})
        
    except Comanda.DoesNotExist:
        return JsonResponse({"error": "Comanda no encontrada"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)