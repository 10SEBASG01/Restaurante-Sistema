from django.db import models
from django.core.validators import MinValueValidator
from apps.usuarios.models import Usuario

# =========================================================================
# --- ESTRUCTURA Y DINÁMICA DE ZONAS ---
# =========================================================================
class ZonaMesa(models.Model):
    """
    Modelo para la gestión e identificación de las áreas físicas del restaurante.
    """
    id_zona = models.AutoField(primary_key=True)
    nombre_zona = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Zona")

    class Meta:
        db_table = 'zonas_mesa'
        verbose_name = "Zona de Mesa"
        verbose_name_plural = "Zonas de Mesas"
        ordering = ['nombre_zona']

    def __str__(self):
        return self.nombre_zona


# =========================================================================
# --- ENTIDAD PRINCIPAL: CONTROL DE MESAS ---
# =========================================================================
class Mesa(models.Model):
    """
    Modelo operativo para el control de estados, asignaciones y consumo de clientes.
    """
    ESTADOS = (
        ('libre', 'Libre'),
        ('ocupada', 'Ocupada'),
        ('reservada', 'Reservada'),
    )

    # Validaciones numéricas para impedir valores cero o negativos
    numero = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="Número de Mesa")
    capacidad = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="Capacidad (Personas)")
    estado = models.CharField(max_length=15, choices=ESTADOS, default='libre')

    # LINEA IMPORTANTE: PROTECT impide borrar una zona si tiene mesas activas vinculadas
    ubicacion = models.ForeignKey(
        ZonaMesa,
        on_delete=models.PROTECT, 
        db_column='id_zona',
        related_name='mesas',
        null=True, 
        blank=True,
        verbose_name="Ubicación / Zona"
    )

    # --- BLOQUE: METADATOS COMPLEMENTARIOS DEL CLIENTE ---
    cliente_nombre = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cliente / Grupo")
    cliente_cedula = models.CharField(max_length=13, blank=True, null=True, verbose_name="Cédula del Cliente")
    cliente_correo = models.EmailField(blank=True, null=True, verbose_name="Correo del Cliente")
    cliente_direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección del Cliente")

    # LINEA IMPORTANTE: SET_NULL mantiene la mesa intacta si el mesero asignado es dado de baja
    mesero_assigned = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        limit_choices_to={'rol': 'mesero'},  # Filtro directo a nivel de base de datos
        verbose_name="Mesero Asignado"
    )

    # Interruptor crítico para el borrado lógico del sistema (Soft Delete)
    is_active = models.BooleanField(default=True, verbose_name="Mesa Activa")

    class Meta:
        ordering = ['numero']
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"
        
        # REGLA DE UNICIDAD CONDICIONAL (PostgreSQL):
        # Valida duplicados numéricos únicamente sobre los registros que sigan activos en el tablero.
        constraints = [
            models.UniqueConstraint(
                fields=['numero'],
                condition=models.Q(is_active=True),
                name='unique_numero_mesa_activa'
            )
        ]

    def __str__(self):
        estado_display = self.get_estado_display()
        return f"Mesa {self.numero} - ({estado_display})"