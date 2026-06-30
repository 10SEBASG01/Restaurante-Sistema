# apps/facturacion/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 1. Consola principal de facturación
    path('', views.listar_pedidos_por_facturar, name='listar_pedidos_por_facturar'),
    
    # 2. Flujo directo: Cuando cobras un pedido específico desde la tabla
    path('nueva/<int:id_pedido>/', views.crear_factura, name='crear_factura'),
    
    # 3. Flujo global: Cuando entran a "Nueva Factura" vacía (sin ID)
    path('nueva/', views.crear_factura, name='crear_factura_vacia'),
    
    # 4. Plantilla de visualización o impresión de la factura emitida
    path('ver/<int:id_factura>/', views.ver_detalle_factura, name='ver_detalle_factura'),

    path('historial/', views.historial_facturas, name='historial_facturas'),
    path('configuracion/', views.configuracion_facturacion, name='configuracion_facturacion'),
]