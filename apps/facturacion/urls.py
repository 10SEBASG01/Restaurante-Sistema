# apps/facturacion/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # =========================================================================
    # BLOQUE 1: PROCESAMIENTO Y FLUJOS DE FACTURACIÓN (Caja en Vivo)
    # =========================================================================
    
    # LINEA IMPORTANTE: Panel principal de caja; lista las mesas y comandas listas por liquidar
    path('', views.listar_pedidos_por_facturar, name='listar_pedidos_por_facturar'),
    
    # LINEA IMPORTANTE: Captura el ID del pedido para arrastrar automáticamente los platillos consumidos al formulario
    path('nueva/<int:id_pedido>/', views.crear_factura, name='crear_factura'),
    
    # Permite levantar un formulario de facturación manual desde cero (sin pedido enlazado)
    path('nueva/', views.crear_factura, name='crear_factura_vacia'),
    
    # =========================================================================
    # BLOQUE 2: CONSULTAS HISTÓRICAS, PARÁMETROS FISCALES Y REPORTES
    # =========================================================================
    
    # LINEA IMPORTANTE: Renderiza el comprobante final de la venta para visualización en pantalla o impresión física
    path('ver/<int:id_factura>/', views.ver_detalle_factura, name='ver_detalle_factura'),

    # Registro general de auditoría de transacciones emitidas anteriormente
    path('historial/', views.historial_facturas, name='historial_facturas'),
    
    # Panel de administración para alterar el porcentaje de IVA, datos de la empresa o RUC
    path('configuracion/', views.configuracion_facturacion, name='configuracion_facturacion'),
]