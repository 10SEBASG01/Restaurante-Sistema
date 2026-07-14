"""
Módulo de modelos para la gestión de Mesas y Pedidos.

Este archivo define la estructura de datos ORM que interactúa con las tablas 
preexistentes en la base de datos relacional del restaurante. 
Se utiliza 'managed = False' en las clases Meta para indicar que la creación 
y modificación del esquema de estas tablas se gestiona directamente en el 
motor de base de datos (ej. PostgreSQL), protegiendo la integridad estructural.
"""

from django.db import models
from apps.menu.models import GestionPlatillo

class Mesa(models.Model):
    """
    Representa las mesas físicas disponibles en el salón del restaurante.
    
    Permite controlar la capacidad máxima de comensales y monitorear el 
    flujo de ocupación en tiempo real (estado).
    """
    # Identificador visual de la mesa (solo enteros positivos a partir de 1, no permite 0)
    numero = models.PositiveIntegerField(unique=True)
    # Cantidad máxima de personas que pueden ocupar esta mesa
    capacidad = models.PositiveIntegerField()
    # Ciclo de vida de la mesa (ej. 'libre', 'ocupada', 'reservada')
    estado = models.CharField(max_length=15, default='libre')

    class Meta:
        db_table = 'mesas_mesa'
        # Django no creará ni alterará esta tabla mediante migraciones.
        managed = False  


class GestionPedido(models.Model):
    """
    Cabecera principal de una solicitud de consumo (Pedido Global).
    
    Agrupa toda la actividad transaccional de una mesa específica durante su 
    estadía, enlazando al cliente (mediante la mesa) con los detalles de su orden.
    """
    # Clave primaria autoincremental (inicia en 1)
    id_pedido = models.AutoField(primary_key=True)
    
    # Relación restrictiva: No se puede eliminar una mesa si tiene pedidos históricos asociados
    id_mesa = models.ForeignKey(Mesa, on_delete=models.RESTRICT, db_column='id_mesa_id')
    
    # Registro automático del momento exacto de la solicitud para métricas de tiempo
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    
    # Control del flujo general del pedido (ej. 'en_preparacion', 'servido', 'pagado')
    estado_pedido = models.CharField(max_length=20, default='en_preparacion')
    
    # Anotaciones generales del cliente (ej. alergias o solicitudes especiales)
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'gestion_pedido'
        managed = False


class Comanda(models.Model):
    """
    Documento de trabajo interno para el área de producción (Cocina).
    
    Se deriva de un 'GestionPedido'. Un pedido global puede generar múltiples 
    comandas si los clientes piden platos en diferentes momentos (ej. entradas primero, postres después).
    """
    # Clave primaria autoincremental (inicia en 1)
    id_comanda = models.AutoField(primary_key=True)
    
    # Relación en cascada: Si se cancela o elimina el pedido global por error humano, 
    # se eliminan sus comandas asociadas automáticamente en la base de datos
    id_pedido = models.ForeignKey(GestionPedido, on_delete=models.CASCADE, db_column='id_pedido_id')
    
    # Tiempo exacto en que la orden se imprime o aparece en la pantalla de la cocina
    fecha_emision = models.DateTimeField(auto_now_add=True)
    
    # Estado de preparación de esta orden específica (ej. 'pendiente', 'cocinando', 'lista')
    estado_comanda = models.CharField(max_length=20, default='pendiente')
    
    # Instrucciones directas para el chef relacionadas con este bloque de platos
    nota_cocina = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'pedidos_comanda'
        managed = False