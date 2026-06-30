from django import forms
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

    # 🎯 CAMBIO MAESTRO: ModelChoiceField para validar correctamente los IDs numéricos enviados por JS
    mesa = forms.ModelChoiceField(
        queryset=Mesa.objects.none(),  # Se inicializa vacío y se llena en el __init__
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
        # 🎯 Cargamos las mesas libres para mapear correctamente sus IDs en la validación del POST
        self.fields['mesa'].queryset = Mesa.objects.filter(estado='libre').order_by('numero')