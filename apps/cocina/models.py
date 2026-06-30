from django.db import models
from apps.menu.models import GestionPlatillo

class Mesa(models.Model):
    # Django autogenera id, y usas 'numero' en tu modelo real
    numero = models.PositiveIntegerField(unique=True)
    capacidad = models.PositiveIntegerField()
    estado = models.CharField(max_length=15, default='libre')

    class Meta:
        db_table = 'mesas_mesa'
        managed = False


class GestionPedido(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    id_mesa = models.ForeignKey(Mesa, on_delete=models.RESTRICT, db_column='id_mesa_id')
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado_pedido = models.CharField(max_length=20, default='en_preparacion')
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'gestion_pedido'
        managed = False


class Comanda(models.Model):
    id_comanda = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey(GestionPedido, on_delete=models.CASCADE, db_column='id_pedido_id')
    fecha_emision = models.DateTimeField(auto_now_add=True)
    estado_comanda = models.CharField(max_length=20, default='pendiente')
    nota_cocina = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'pedidos_comanda'
        managed = False