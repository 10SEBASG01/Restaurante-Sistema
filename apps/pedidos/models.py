from django.db import models
from django.conf import settings

class GestionPedido(models.Model):
    ESTADOS_PEDIDO = [
        ('en_preparacion', 'En Preparación'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    id_pedido = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_cliente', related_name='pedidos_cliente')
    id_empleado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, db_column='id_empleado', related_name='pedidos_atendidos')
    
    # 🔥 SOLUCIÓN: Cambiamos RESTRICT por SET_NULL. Si se borra la mesa, este campo quedará vacío (null).
    id_mesa = models.ForeignKey(
        'mesas.Mesa', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        db_column='id_mesa'
    )
    
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado_pedido = models.CharField(max_length=20, choices=ESTADOS_PEDIDO, default='en_preparacion')
    observaciones = models.TextField(null=True, blank=True, db_column='observaciones')

    class Meta:
        db_table = 'gestion_pedido'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        # Manejamos el caso donde la mesa ya no exista
        mesa_str = f"Mesa {self.id_mesa.numero}" if self.id_mesa else "Mesa Eliminada"
        return f"Pedido #{self.id_pedido} - {mesa_str}"


class DetallePedido(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey(GestionPedido, on_delete=models.CASCADE, related_name='detalles', db_column='id_pedido')
    
    # Te recomiendo dejar el platillo en RESTRICT o SET_NULL, si borras un platillo, arruinas facturas pasadas. SET_NULL es más seguro si quieres permitir borrar platillos.
    id_platillo = models.ForeignKey('menu.GestionPlatillo', on_delete=models.SET_NULL, null=True, blank=True, db_column='id_platillo')
    
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'detalle_pedido'
        verbose_name = 'Detalle de Pedido'
        verbose_name_plural = 'Detalles de Pedidos'

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"Detalle {self.id_detalle} - Pedido #{self.id_pedido.id_pedido}"


class Comanda(models.Model):
    ESTADOS_COMANDA = [
        ('pendiente', 'Pendiente'),
        ('lista', 'Lista'),
    ]

    id_comanda = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey(GestionPedido, on_delete=models.CASCADE, db_column='id_pedido')
    fecha_emision = models.DateTimeField(auto_now_add=True)
    estado_comanda = models.CharField(max_length=20, choices=ESTADOS_COMANDA, default='pendiente')
    nota_cocina = models.TextField(null=True, blank=True, db_column='nota_cocina')

    class Meta:
        db_table = 'comanda'
        verbose_name = 'Comanda'
        verbose_name_plural = 'Comandas'

    def __str__(self):        
        return f"Comanda #{self.id_comanda} - Pedido #{self.id_pedido.id_pedido}"