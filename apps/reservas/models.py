from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone


class Reserva(models.Model):

    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
    ]

    codigo = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    # 🎯 CAMBIO AQUÍ: Separamos el cliente
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)

    # Validadores para exigir exactamente 10 números
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

    telefono = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message='El teléfono debe contener exactamente 10 dígitos numéricos.'
            )
        ]
    )

    fecha = models.DateField()

    hora = models.TimeField()

    personas = models.PositiveIntegerField()

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

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['fecha', 'hora']

        constraints = [
            models.UniqueConstraint(
                fields=['mesa', 'fecha', 'hora'],
                name='unique_reserva_mesa_fecha_hora'
            )
        ]

    def __str__(self):
        # 🎯 CAMBIO AQUÍ: Reflejar nombres y apellidos en el panel admin
        return f"{self.codigo} - {self.nombres} {self.apellidos}"

    def clean(self):

        # Evitar que la cédula sea cero
        if self.cedula and self.cedula.isdigit():
            if int(self.cedula) == 0:
                raise ValidationError({
                    'cedula': 'La cédula no puede ser cero, ingrese un número válido.'
                })

        # 🔥 LÓGICA DE TIEMPO COMENTADA PARA DAR LIBERTAD DE REGISTRO
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
        # NO PERMITIR DOS RESERVAS EXACTAMENTE IGUALES
        # (El margen de 1 hora ya lo maneja forms.py)
        # ======================================

        reserva_existente = Reserva.objects.filter(
            mesa=self.mesa,
            fecha=self.fecha,
            hora=self.hora
        )

        # Si se está editando, excluir la reserva actual
        if self.pk:
            reserva_existente = reserva_existente.exclude(pk=self.pk)

        if reserva_existente.exists():
            raise ValidationError({
                'mesa': 'Esta mesa ya está reservada para esa fecha y hora exacta.'
            })

    def save(self, *args, **kwargs):

        self.full_clean()

        if not self.codigo:
            ultimo = Reserva.objects.order_by('-id').first()

            if ultimo:
                numero = int(ultimo.codigo.replace('R-', '')) + 1
            else:
                numero = 1

            self.codigo = f"R-{numero:04d}"

        super().save(*args, **kwargs)