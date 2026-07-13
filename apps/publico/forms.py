from datetime import datetime, timedelta
from django import forms
from django.core.exceptions import ValidationError
from apps.reservas.models import Reserva
from apps.mesas.models import Mesa

class ReservaPublicaForm(forms.ModelForm):

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

    mesa = forms.ModelChoiceField(
        queryset=Mesa.objects.none(),  
        widget=forms.Select(
            attrs={
                'class': 'form-select'
            }
        ),
        empty_label="Seleccione una mesa"
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
            'observaciones'
        ]

        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Juan Carlos'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Pérez Mendoza'}),
            
            'cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '10',
                'pattern': r'\d{10}',
                'title': 'Ingrese exactamente 10 dígitos'
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@correo.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '10',
                'pattern': r'\d{10}',
                'title': 'Ingrese exactamente 10 dígitos'
            }),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'personas': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True,
                'style': 'background:#f3f4f6;'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 🎯 LA SOLUCIÓN: Solo cargar las mesas que siguen activas
        self.fields['mesa'].queryset = Mesa.objects.filter(is_active=True).order_by('numero')

    def clean_mesa(self):
        mesa_obj = self.cleaned_data.get('mesa')
        if mesa_obj:
            return f"Mesa {mesa_obj.numero}"
        return mesa_obj

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora = cleaned_data.get('hora')
        mesa = cleaned_data.get('mesa') 
        cedula = cleaned_data.get('cedula')

        # Control estricto de identificaciones (solo enteros positivos a partir de 1)
        if cedula and cedula.isdigit():
            if int(cedula) == 0:
                self.add_error('cedula', 'La cédula no puede ser cero, ingrese un valor entero positivo a partir del uno.')

        if fecha and hora and mesa:
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
                    "Lo sentimos, esta mesa ya fue reservada en este horario. Por favor, elige otra mesa o cambia la hora (nuestras reservas duran 1 hora)."
                )

        return cleaned_data