from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.auditoria.models import Auditoria

class GestionPedido(models.Model):
    ESTADOS_PEDIDO = [
        ('en_preparacion', 'En Preparación'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    id_pedido = models.AutoField(primary_key=True)
    
    # id_cliente: Apunta al modelo de usuario central (puede ser NULL si es consumidor final)
    id_cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_cliente', related_name='pedidos_cliente')
    
    # id_empleado: ¡CORREGIDO! Apunta al modelo de Usuario centralizado (que contiene el rol mesero/cajero)
    id_empleado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, db_column='id_empleado', related_name='pedidos_atendidos')
    
    # Apunta a la app 'mesas'
    id_mesa = models.ForeignKey('mesas.Mesa', on_delete=models.RESTRICT, db_column='id_mesa')
    
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado_pedido = models.CharField(max_length=20, choices=ESTADOS_PEDIDO, default='en_preparacion')
    observaciones = models.TextField(null=True, blank=True, db_column='observaciones')

    class Meta:
        db_table = 'gestion_pedido'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        return f"Pedido #{self.id_pedido} - Mesa {self.id_mesa}"


class DetallePedido(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey(GestionPedido, on_delete=models.CASCADE, related_name='detalles', db_column='id_pedido')
    
    # Apunta a la app 'menu'
    id_platillo = models.ForeignKey('menu.GestionPlatillo', on_delete=models.RESTRICT, db_column='id_platillo')
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'detalle_pedido'
        verbose_name = 'Detaille de Pedido'
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
    
    # --- TRIGGER: AUDITAR CREACIÓN DE PEDIDO ---
@receiver(post_save, sender=GestionPedido)
def auditar_creacion_pedido(sender, instance, created, **kwargs):
    """
    Se dispara automáticamente DESPUÉS de guardar un pedido nuevo.
    """
    if created: # Si es un pedido recién creado
        Auditoria.objects.create(
            id_usuario=instance.id_empleado, # Usamos tu campo id_empleado
            modulo='pedidos',                # 'pedidos' activa el punto AZUL
            accion='Pedido creado',
            detalle=f"Pedido #{instance.id_pedido} · Mesa {instance.id_mesa.numero}"
        )