"""
Formularios para la gestión interna de Reservas.

Este módulo define la interfaz de entrada de datos y las validaciones de negocio 
para la creación y edición de reservas desde el panel administrativo del restaurante.
"""

from datetime import datetime, timedelta
from django import forms
from django.core.exceptions import ValidationError
from .models import Reserva
from apps.mesas.models import Mesa


class ReservaForm(forms.ModelForm):
    """
    Formulario principal para el modelo Reserva.
    
    Implementa widgets personalizados para mejorar la experiencia de usuario (UX) 
    y maneja la lógica compleja de disponibilidad de mesas y prevención de 
    solapamiento de horarios.
    """

    fecha = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={
                'type': 'date',
                'class': 'form-control'
            }
        )
    )

    hora = forms.TimeField(
        widget=forms.TimeInput(
            format='%H:%M',
            attrs={
                'type': 'time',
                'class': 'form-control'
            }
        )
    )

    mesa = forms.ChoiceField(
        # Las opciones se cargan dinámicamente en el constructor (__init__)
        choices=[],
        widget=forms.Select(
            attrs={
                'class': 'form-select'
            }
        )
    )

    class Meta:
        model = Reserva
        fields = [
            'nombres', 'apellidos', 'cedula', 'correo', 'telefono',
            'direccion', 'fecha', 'hora', 'personas', 'mesa', 'estado',
            'observaciones'
        ]
        # Configuración de atributos HTML y clases de Bootstrap para los campos
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres del cliente'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos del cliente'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
            'personas': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notas adicionales...'})
        }

    def __init__(self, *args, **kwargs):
        """
        Constructor del formulario.
        Configura dinámicamente las opciones del campo 'mesa' garantizando la 
        integridad referencial visual, incluso para registros históricos.
        """
        super().__init__(*args, **kwargs)
        
        # Filtra exclusivamente las mesas que están operativas actualmente en el sistema
        mesas_activas = Mesa.objects.filter(is_active=True).order_by('numero')
        
        # Genera las opciones. Estructura: (Valor_Guardado_En_BD, Etiqueta_Mostrada_Al_Usuario)
        # Se envía solo el número en la etiqueta para evitar redundancias visuales como "Mesa Mesa"
        opciones = [(f"Mesa {m.numero}", f"{m.numero}") for m in mesas_activas]

        # Lógica de compatibilidad histórica:
        # Si se está editando una reserva antigua y su mesa asociada fue desactivada o eliminada,
        # la agregamos temporalmente a las opciones solo para este registro, marcándola como "No disponible".
        if self.instance and self.instance.pk and self.instance.mesa:
            if not any(opt[0] == self.instance.mesa for opt in opciones):
                numero_solo = self.instance.mesa.replace('Mesa ', '')
                opciones.append((self.instance.mesa, f"{numero_solo} (No disponible)"))

        self.fields['mesa'].choices = opciones

    # 🔥 VALIDACIONES DEL FORMULARIO
    def clean(self):
        """
        Ejecuta las validaciones cruzadas y aplica las reglas de negocio estrictas.
        """
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora = cleaned_data.get('hora')
        mesa = cleaned_data.get('mesa')
        estado = cleaned_data.get('estado')
        cedula = cleaned_data.get('cedula')

        # Regla de negocio para IDs: 
        # El valor cero no está permitido; solo se aceptan números enteros positivos a partir de uno.
        if cedula and cedula.isdigit():
            if int(cedula) == 0:
                self.add_error(
                    'cedula', 
                    'La cédula no puede ser cero, ingrese un valor entero positivo a partir del uno.'
                )

        # Prevención de sobreventa (Overbooking)
        # Solo se valida si la reserva actual no está en estado CANCELADA
        if fecha and hora and mesa and estado != 'CANCELADA':
            tiempo_reserva = datetime.combine(fecha, hora)
            
            # Se establece un margen de bloqueo de 59 minutos antes y después de la hora solicitada
            rango_inicio = (tiempo_reserva - timedelta(minutes=59)).time()
            rango_fin = (tiempo_reserva + timedelta(minutes=59)).time()

            # Busca reservas activas que coincidan en mesa, fecha y rango horario
            choques = Reserva.objects.filter(
                mesa=mesa,
                fecha=fecha,
                hora__gte=rango_inicio,
                hora__lte=rango_fin
            ).exclude(estado='CANCELADA') 
            
            # Si se está editando, excluye la propia reserva de la validación
            if self.instance and self.instance.pk:
                choques = choques.exclude(pk=self.instance.pk)

            # Si existen registros, se levanta un error de validación
            if choques.exists():
                raise ValidationError(
                    "¡Choque de horarios! Esta mesa ya tiene una reserva activa en ese rango de tiempo."
                )

        return cleaned_data