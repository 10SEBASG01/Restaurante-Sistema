from django.db import models
from apps.usuarios.models import Usuario

# 🔥 NUEVO MODELO: Para manejar de forma dinámica las zonas desde tu base de datos
class ZonaMesa(models.Model):
    id_zona = models.AutoField(primary_key=True)
    nombre_zona = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="Nombre de la Zona"
    )

    class Meta:
        db_table = 'zonas_mesa'
        verbose_name = "Zona de Mesa"
        verbose_name_plural = "Zonas de Mesas"
        ordering = ['nombre_zona']

    def __str__(self):
        return self.nombre_zona


class Mesa(models.Model):
    ESTADOS = (
        ('libre', 'Libre'),
        ('ocupada', 'Ocupada'),
        ('reservada', 'Reservada'),
    )

    # ❌ SE ELIMINÓ LA TUPLA UBICACIONES ESTÁTICA

    numero = models.PositiveIntegerField(
        unique=True,
        verbose_name="Número de Mesa"
    )

    capacidad = models.PositiveIntegerField(
        verbose_name="Capacidad (Personas)"
    )

    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default='libre'
    )

    # 🔥 CORREGIDO: Ahora es una relación FK dinámica apuntando a la nueva tabla
    ubicacion = models.ForeignKey(
        ZonaMesa,
        on_delete=models.PROTECT, # No permite borrar una zona si contiene mesas asignadas
        db_column='id_zona',
        related_name='mesas',
        null=True, # Permite nulos temporalmente para migrar las mesas actuales sin errores
        blank=True,
        verbose_name="Ubicación / Zona"
    )

    # ==========================
    # INFORMACIÓN DEL CLIENTE
    # (USO INTERNO DEL SISTEMA)
    # ==========================

    cliente_nombre = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Cliente / Grupo"
    )

    cliente_cedula = models.CharField(
        max_length=13,
        blank=True,
        null=True,
        verbose_name="Cédula del Cliente"
    )

    cliente_correo = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo del Cliente"
    )

    cliente_direccion = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Dirección del Cliente"
    )

    mesero_assigned = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        limit_choices_to={'rol': 'mesero'},
        verbose_name="Mesero Asignado"
    )

    class Meta:
        ordering = ['numero']
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"

    def __str__(self):
        estado_display = self.get_estado_display()
        return f"Mesa {self.numero} - ({estado_display})"