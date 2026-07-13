from datetime import datetime, timedelta
from django import forms
from django.core.exceptions import ValidationError
from .models import Reserva
from apps.mesas.models import Mesa


class ReservaForm(forms.ModelForm):

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
            'nombres',
            'apellidos',
            'cedula',
            'correo',
            'telefono',
            'direccion',
            'fecha',
            'hora',
            'personas',
            'mesa',
            'estado',
            'observaciones'
        ]
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
        super().__init__(*args, **kwargs)
        
        # 🎯 SOLUCIÓN 1: Volvemos a filtrar por is_active=True para que las eliminadas (1 y 2) desaparezcan.
        mesas_activas = Mesa.objects.filter(is_active=True).order_by('numero')
        
        # 🎯 SOLUCIÓN 2: La tupla es (Valor_Para_Backend, Etiqueta_Para_Frontend). 
        # Enviamos el número limpio en la etiqueta para que tu diseño no diga "Mesa Mesa".
        opciones = [(f"Mesa {m.numero}", f"{m.numero}") for m in mesas_activas]

        # Control de borde para editar reservas antiguas con mesas que ya no existen
        if self.instance and self.instance.pk and self.instance.mesa:
            if not any(opt[0] == self.instance.mesa for opt in opciones):
                numero_solo = self.instance.mesa.replace('Mesa ', '')
                opciones.append((self.instance.mesa, f"{numero_solo} (No disponible)"))

        self.fields['mesa'].choices = opciones

    # 🔥 VALIDACIONES DEL FORMULARIO
    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora = cleaned_data.get('hora')
        mesa = cleaned_data.get('mesa')
        estado = cleaned_data.get('estado')
        cedula = cleaned_data.get('cedula')

        # Validación de cédula 
        if cedula and cedula.isdigit():
            if int(cedula) == 0:
                self.add_error('cedula', 'La cédula no puede ser cero, ingrese un valor entero positivo a partir del uno.')

        # Validación de choque de horarios
        if fecha and hora and mesa and estado != 'CANCELADA':
            tiempo_reserva = datetime.combine(fecha, hora)
            
            rango_inicio = (tiempo_reserva - timedelta(minutes=59)).time()
            rango_fin = (tiempo_reserva + timedelta(minutes=59)).time()

            choques = Reserva.objects.filter(
                mesa=mesa,
                fecha=fecha,
                hora__gte=rango_inicio,
                hora__lte=rango_fin
            ).exclude(estado='CANCELADA') 
            
            if self.instance and self.instance.pk:
                choques = choques.exclude(pk=self.instance.pk)

            if choques.exists():
                raise ValidationError(
                    "¡Choque de horarios! Esta mesa ya tiene una reserva activa en ese rango de tiempo."
                )

        return cleaned_data