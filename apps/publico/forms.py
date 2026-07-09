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

    # 🎯 CAMBIO: Se mantiene ModelChoiceField para aprovechar el HTML, 
    # pero el queryset se cargará con TODAS las mesas en el __init__
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
            'cliente',
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
            'cliente': forms.TextInput(attrs={'class': 'form-control'}),
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
        # 🎯 CORRECCIÓN: Cargamos TODAS las mesas. Una mesa ocupada HOY puede estar libre MAÑANA.
        self.fields['mesa'].queryset = Mesa.objects.all().order_by('numero')

    def clean_mesa(self):
        """
        🎯 CORRECCIÓN CLAVE: El módulo público envía un Objeto Mesa, pero la BD 
        espera un texto. Transformamos el objeto al formato "Mesa X" para que 
        coincida exactamente con la lógica del administrador.
        """
        mesa_obj = self.cleaned_data.get('mesa')
        if mesa_obj:
            # Asumiendo que tu modelo Mesa tiene un campo llamado 'numero'
            return f"Mesa {mesa_obj.numero}"
        return mesa_obj

    # 🔥 VALIDACIÓN PÚBLICA DE CHOQUE DE HORARIOS (1 Hora Exacta)
    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora = cleaned_data.get('hora')
        mesa = cleaned_data.get('mesa') # Aquí ya llega como "Mesa X" gracias a clean_mesa()

        if fecha and hora and mesa:
            tiempo_reserva = datetime.combine(fecha, hora)
            
            # Margen de 59 minutos antes y después para asegurar la hora exacta
            rango_inicio = (tiempo_reserva - timedelta(minutes=59)).time()
            rango_fin = (tiempo_reserva + timedelta(minutes=59)).time()

            # Buscar conflictos en la base de datos excluyendo las canceladas
            choques = Reserva.objects.filter(
                mesa=mesa,
                fecha=fecha,
                hora__gte=rango_inicio,
                hora__lte=rango_fin
            ).exclude(estado='CANCELADA') 
            
            # Si se está editando una reserva existente (por si acaso el cliente puede editar)
            if self.instance and self.instance.pk:
                choques = choques.exclude(pk=self.instance.pk)

            # Si existe un cruce, lanzamos un error amigable al cliente
            if choques.exists():
                raise ValidationError(
                    "Lo sentimos, esta mesa ya fue reservada en este horario. Por favor, elige otra mesa o cambia la hora (nuestras reservas duran 1 hora)."
                )

        return cleaned_data