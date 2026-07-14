"""
Módulo de modelos de datos para la gestión de Reservas.

Define la estructura central para el almacenamiento de las reservas de mesas. 
Implementa reglas de negocio directamente en la capa de datos (Fat Models), 
como la generación automática de códigos serializados, validación estricta de 
identificaciones (cédulas) mediante expresiones regulares, y prevención de 
duplicidad de registros a nivel de base de datos.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone


class Reserva(models.Model):
    """
    Entidad principal que representa una reserva agendada en el sistema.
    
    Desacopla la información del cliente (nombres, apellidos, contacto) de 
    una tabla de usuarios externa para permitir reservas rápidas, mientras 
    mantiene controles estrictos sobre la disponibilidad de las mesas.
    """

    # Opciones predefinidas para el ciclo de vida de la reserva
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
    ]

    # Identificador alfanumérico único generado automáticamente (ej. R-0001)
    codigo = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    # 🎯 Datos personales del cliente (separados para mejor estructuración)
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)

    # Validación a nivel de base de datos y formulario para asegurar exactamente 10 dígitos
    cedula = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message='La cédula debe contener exactamente 10 dígitos numéricos.'
            )
        ]
    )

    correo = models.EmailField(
        max_length=254
    )

    direccion = models.CharField(
        max_length=255
    )

    # Validación de formato telefónico estándar de 10 dígitos
    telefono = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message='El teléfono debe contener exactamente 10 dígitos numéricos.'
            )
        ]
    )

    # Parámetros temporales y logísticos de la reserva
    fecha = models.DateField()
    hora = models.TimeField()
    personas = models.PositiveIntegerField()

    # Almacena el identificador descriptivo de la mesa (ej. "Mesa 5")
    mesa = models.CharField(
        max_length=50
    )

    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default='PENDIENTE'
    )

    observaciones = models.TextField(
        blank=True,
        null=True
    )

    # Auditoría básica: Timestamp de creación del registro
    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        """
        Metadatos del modelo: Define el ordenamiento por defecto y 
        las restricciones de integridad estructural (constraints).
        """
        # Ordena las consultas cronológicamente por defecto
        ordering = ['fecha', 'hora']

        # Restricción a nivel de motor de base de datos para evitar que 
        # exista más de un registro con la misma mesa, fecha y hora exacta.
        constraints = [
            models.UniqueConstraint(
                fields=['mesa', 'fecha', 'hora'],
                name='unique_reserva_mesa_fecha_hora'
            )
        ]

    def __str__(self):
        """
        Representación en cadena del objeto.
        Útil para la visualización rápida en el panel de administración y logs.
        """
        return f"{self.codigo} - {self.nombres} {self.apellidos}"

    def clean(self):
        """
        Método de validación personalizada del modelo.
        Se ejecuta antes de guardar para asegurar el cumplimiento de las reglas de negocio.
        """
        
        # ======================================
        # CONTROL ESTRICTO DE IDENTIFICACIONES
        # ======================================
        # Evita el almacenamiento del valor cero. Solo se permiten números enteros positivos a partir del uno.
        if self.cedula and self.cedula.isdigit():
            if int(self.cedula) == 0:
                raise ValidationError({
                    'cedula': 'La cédula no puede ser cero, ingrese un número válido entero y positivo.'
                })

        # 🔥 LÓGICA DE TIEMPO COMENTADA PARA DAR LIBERTAD DE REGISTRO
        # (Se mantiene comentado para permitir al administrador agendar reservas pasadas 
        # si es necesario para cuadrar el sistema).
        # hoy = timezone.localdate()
        # 
        # if self.fecha < hoy:
        #     raise ValidationError({
        #         'fecha': 'No se puede reservar una fecha pasada.'
        #     })
        # 
        # if self.fecha == hoy:
        #     hora_actual = timezone.localtime().time()
        # 
        #     if self.hora <= hora_actual:
        #         raise ValidationError({
        #             'hora': 'La hora debe ser posterior a la actual.'
        #         })

        # ======================================
        # PREVENCIÓN DE DUPLICIDAD EXACTA
        # ======================================
        # Asegura que no se guarde una reserva en la misma mesa, misma fecha y mismo segundo.
        # (El margen preventivo de 1 hora se gestiona en la capa de formularios).
        reserva_existente = Reserva.objects.filter(
            mesa=self.mesa,
            fecha=self.fecha,
            hora=self.hora
        )

        # Si estamos editando un registro existente (tiene Primary Key), lo excluimos del chequeo
        if self.pk:
            reserva_existente = reserva_existente.exclude(pk=self.pk)

        if reserva_existente.exists():
            raise ValidationError({
                'mesa': 'Esta mesa ya está reservada para esa fecha y hora exacta.'
            })

    def save(self, *args, **kwargs):
        """
        Sobreescritura del método de guardado.
        Fuerza la ejecución de las validaciones y genera el código secuencial 
        único para las nuevas reservas antes de realizar el INSERT en la base de datos.
        """
        # Fuerza las validaciones del método clean()
        self.full_clean()

        # Generación dinámica del código si es un nuevo registro
        if not self.codigo:
            ultimo = Reserva.objects.order_by('-id').first()

            if ultimo:
                # Extrae el número del último código, lo incrementa y lo formatea a 4 dígitos
                numero = int(ultimo.codigo.replace('R-', '')) + 1
            else:
                numero = 1

            self.codigo = f"R-{numero:04d}"

        # Llama al método save() original de la clase padre
        super().save(*args, **kwargs)