from django.db import models
from django.conf import settings
from apps.pedidos.models import GestionPedido

class ConfiguracionFacturacion(models.Model):
    """
    🎯 Almacena de manera centralizada la información del establecimiento
    y los parámetros impositivos editables por el administrador.
    """
    id = models.AutoField(primary_key=True)
    nombre_comercial = models.CharField(max_length=255, default="Sabor y Arte")
    razon_social = models.CharField(max_length=255, blank=True, null=True, verbose_name="Razón Social")
    ruc = models.CharField(max_length=13, default="20456789012", verbose_name="RUC del Establecimiento")
    provincia = models.CharField(max_length=100, default="Manta, Manabí", verbose_name="Ciudad / Provincia")
    direccion = models.CharField(max_length=255, default="Av. Gastronomía 455, Miraflores", verbose_name="Dirección Matriz")
    iva_porcentaje = models.IntegerField(default=12, verbose_name="Tasa de IVA Vigente (%)")

    class Meta:
        db_table = 'configuracion_facturacion'
        verbose_name = 'Configuración de Facturación'
        verbose_name_plural = 'Configuraciones de Facturación'

    def __str__(self):
        return f"Configuración Activa - IVA: {self.iva_porcentaje}%"


class Factura(models.Model):
    FORMAS_PAGO = [
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA', 'Tarjeta de Crédito/Débito'),
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
    ]

    id_factura = models.AutoField(primary_key=True)
    secuencial = models.CharField(max_length=20, unique=True, verbose_name="Número de Factura")
    
    id_pedido = models.OneToOneField(
        GestionPedido, 
        on_delete=models.PROTECT, 
        db_column='id_pedido',
        related_name='factura'
    )
    
    id_cajero = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.RESTRICT, 
        db_column='id_cajero',
        related_name='facturas_emitidas'
    )
    
    # Datos del cliente al momento de facturar
    cliente_nombre = models.CharField(max_length=150, default="Consumidor Final")
    cliente_identificacion = models.CharField(max_length=13, default="9999999999999", verbose_name="Cédula/RUC")
    cliente_correo = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    cliente_direccion = models.CharField(max_length=250, blank=True, null=True, default="S/N", verbose_name="Dirección")
    
    fecha_emision = models.DateTimeField(auto_now_add=True)
    forma_pago = models.CharField(max_length=20, choices=FORMAS_PAGO, default='EFECTIVO')
    
    # 🎯 PERSISTENCIA FISCAL (Auditoría): Congela los datos de la cabecera del restaurante para el PDF
    emisor_nombre_comercial = models.CharField(max_length=255, blank=True, null=True)
    emisor_razon_social = models.CharField(max_length=255, blank=True, null=True)
    emisor_ruc = models.CharField(max_length=13, blank=True, null=True)
    emisor_direccion = models.CharField(max_length=255, blank=True, null=True)
    emisor_provincia = models.CharField(max_length=100, blank=True, null=True)
    
    # 🎯 TASA APLICADA: Registra si la factura se procesó al 12%, 14%, 15%, etc.
    iva_porcentaje_aplicado = models.IntegerField(default=12, verbose_name="Porcentaje IVA Aplicado")

    # Valores económicos persistidos estáticos
    subtotal_12 = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    subtotal_0 = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    iva_valor = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Descuento")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'factura'
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-fecha_emision']

    def __str__(self):
        return f"Factura {self.secuencial} - Total: ${self.total}"


class FacturaDetalle(models.Model):
    id_factura_detalle = models.AutoField(primary_key=True)
    id_factura = models.ForeignKey(
        Factura, 
        on_delete=models.CASCADE, 
        db_column='id_factura',
        related_name='detalles_factura'
    )
    id_platillo = models.ForeignKey(
        'menu.GestionPlatillo', 
        on_delete=models.RESTRICT, 
        db_column='id_platillo'
    )
    
    nombre_historico = models.CharField(max_length=150)
    cantidad = models.PositiveIntegerField()
    precio_unitario_historico = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'factura_detalle'
        verbose_name = 'Detalle de Factura'
        verbose_name_plural = 'Detalles de Facturas'

    @property
    def subtotal_linea(self):
        return self.cantidad * self.precio_unitario_historico

    def __str__(self):
        return f"Detalle {self.id_factura_detalle} de Factura {self.id_factura.secuencial}"