from django.db import models
from django.conf import settings
from apps.pedidos.models import GestionPedido

# =========================================================================
# BLOQUE 1: CONFIGURACIÓN GLOBAL DEL ESTABLECIMIENTO Y DATOS FISCALES
# =========================================================================
class ConfiguracionFacturacion(models.Model):
    """
    Maneja los parámetros globales del restaurante para la emisión de comprobantes.
    Almacena datos legales y comerciales obligatorios requeridos por las entidades fiscales.
    """

    # ATRIBUTOS / CAMPOS DE LA BASE DE DATOS
    id = models.AutoField(primary_key=True)
    nombre_comercial = models.CharField(max_length=255, default="Sabor y Arte")
    razon_social = models.CharField(max_length=255, blank=True, null=True, verbose_name="Razón Social")
    ruc = models.CharField(max_length=13, default="20456789012", verbose_name="RUC del Establecimiento")
    provincia = models.CharField(max_length=100, default="Manta, Manabí", verbose_name="Ciudad / Provincia")
    direccion = models.CharField(max_length=255, default="Av. Gastronomía 455, Miraflores", verbose_name="Dirección Matriz")
    telefono = models.CharField(max_length=10, blank=True, null=True, verbose_name="Teléfono Principal")
    
    # LÍNEA CRÍTICA: Almacena el IVA vigente que utilizará el sistema para los nuevos cálculos tributarios
    iva_porcentaje = models.IntegerField(default=12, verbose_name="Tasa de IVA Vigente (%)")
    logo_restaurante = models.ImageField(upload_to='logos_marca/', blank=True, null=True, verbose_name="Logo del Restaurante")

    # METADATOS DEL MODELO
    class Meta:
        db_table = 'configuracion_facturacion'
        verbose_name = 'Configuración de Facturación'
        verbose_name_plural = 'Configuraciones de Facturación'

    # MÉTODOS DE REPRESENTACIÓN
    def __str__(self):
        return f"Configuración Activa - IVA: {self.iva_porcentaje}%"


# =========================================================================
# BLOQUE 2: CABECERA DE LA FACTURA (COMPROBANTE FISCAL)
# =========================================================================
class Factura(models.Model):
    """
    Registra el encabezado legal de la transacción de cobro.
    Almacena tanto la información de los montos económicos como un snapshot 
    de los datos del emisor para mantener la inmutabilidad histórica.
    """

    # CONFIGURACIONES Y LLAVES DE ENUMERACIÓN
    FORMAS_PAGO = [
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA', 'Tarjeta de Crédito/Débito'),
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
    ]

    # ATRIBUTOS / CAMPOS DE LA BASE DE DATOS
    id_factura = models.AutoField(primary_key=True)
    secuencial = models.CharField(max_length=20, unique=True, verbose_name="Número de Factura")
    
    # LÍNEA CRÍTICA: SET_NULL evita que la eliminación accidental de un pedido borre el registro legal de la factura
    id_pedido = models.OneToOneField(
        GestionPedido, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        db_column='id_pedido',
        related_name='factura'
    )
    
    # LÍNEA CRÍTICA: RESTRICT bloquea la eliminación de un usuario cajero si este ya ha emitido facturas (Auditoría segura)
    id_cajero = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.RESTRICT, 
        db_column='id_cajero',
        related_name='facturas_emitidas'
    )
    
    # Datos específicos del cliente al momento de generar la venta
    cliente_nombre = models.CharField(max_length=150, default="Consumidor Final")
    cliente_identificacion = models.CharField(max_length=13, default="9999999999999", verbose_name="Cédula/RUC")
    cliente_correo = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    cliente_direccion = models.CharField(max_length=250, blank=True, null=True, default="S/N", verbose_name="Dirección")
    
    fecha_emision = models.DateTimeField(auto_now_add=True)
    forma_pago = models.CharField(max_length=20, choices=FORMAS_PAGO, default='EFECTIVO')
    
    # LÍNEA CRÍTICA: Copia de respaldo inmutable de los datos del establecimiento para auditorías retroactivas
    emisor_nombre_comercial = models.CharField(max_length=255, blank=True, null=True)
    emisor_razon_social = models.CharField(max_length=255, blank=True, null=True)
    emisor_ruc = models.CharField(max_length=13, blank=True, null=True)
    emisor_direccion = models.CharField(max_length=255, blank=True, null=True)
    emisor_provincia = models.CharField(max_length=100, blank=True, null=True)
    
    iva_porcentaje_aplicado = models.IntegerField(default=12, verbose_name="Porcentaje IVA Aplicado")

    # DESGLOSE MONETARIO DE CONTABILIDAD FISCAL
    subtotal_12 = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    subtotal_0 = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    descuento_porcentaje = models.IntegerField(default=0, verbose_name="Porcentaje de Descuento")
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Descuento")
    subtotal_neto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Subtotal Neto Afectado")
    
    iva_valor = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # METADATOS DEL MODELO
    class Meta:
        db_table = 'factura'
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-fecha_emision']

    # MÉTODOS DE REPRESENTACIÓN
    def __str__(self):
        return f"Factura {self.secuencial} - Total: ${self.total}"


# =========================================================================
# BLOQUE 3: DESGLOSE O DETALLE INDIVIDUAL DE LA FACTURA
# =========================================================================
class FacturaDetalle(models.Model):
    """
    Representa cada línea de producto dentro del comprobante de venta.
    Preserva datos históricos de manera independiente al estado actual del catálogo de menú.
    """

    # ATRIBUTOS / CAMPOS DE LA BASE DE DATOS
    id_factura_detalle = models.AutoField(primary_key=True)
    
    # LÍNEA CRÍTICA: CASCADE asegura que si se elimina la cabecera, se limpien todos sus renglones automáticamente
    id_factura = models.ForeignKey(
        Factura, 
        on_delete=models.CASCADE, 
        db_column='id_factura',
        related_name='detalles_factura'
    )
    
    # LÍNEA CRÍTICA: Si un platillo se borra del menú, la factura conserva su consistencia física intacta
    id_platillo = models.ForeignKey(
        'menu.GestionPlatillo', 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        db_column='id_platillo'
    )
    
    # LÍNEA CRÍTICA: Resguarda el nombre y precio original cobrado, evitando alteraciones por modificaciones en el menú
    nombre_historico = models.CharField(max_length=150)
    cantidad = models.PositiveIntegerField()
    precio_unitario_historico = models.DecimalField(max_digits=10, decimal_places=2)

    # METADATOS DEL MODELO
    class Meta:
        db_table = 'factura_detalle'
        verbose_name = 'Detail de Factura'
        verbose_name_plural = 'Detalles de Facturas'

    # PROPIEDADES CALCULADAS (EN MEMORIA)
    @property
    def subtotal_linea(self):
        """Calcula de forma dinámica el valor bruto acumulado en esta fila."""
        return self.cantidad * self.precio_unitario_historico

    # MÉTODOS DE REPRESENTACIÓN
    def __str__(self):
        return f"Detalle {self.id_factura_detalle} de Factura {self.id_factura.secuencial}"