from django import forms
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
            'cliente',
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

            'cliente': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'cedula': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'maxlength': '10',
                    'pattern': '\d{10}',
                    'title': 'Ingrese exactamente 10 dígitos'
                }
            ),

            'correo': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'ejemplo@correo.com'
                }
            ),

            'telefono': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'maxlength': '10',
                    'pattern': '\d{10}',
                    'title': 'Ingrese exactamente 10 dígitos'
                }
            ),

            'direccion': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'personas': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'readonly': True,
                    'style': 'background:#f3f4f6;'
                }
            ),

            'estado': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'observaciones': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4
                }
            )
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Mostrar TODAS las mesas
        mesas_disponibles = Mesa.objects.all().order_by('numero')

        opciones = [
            ('', 'Seleccione una mesa')
        ]

        self.mesas_capacidad = {}

        for mesa in mesas_disponibles:

            self.mesas_capacidad[
                f"Mesa {mesa.numero}"
            ] = mesa.capacidad

            opciones.append(
                (
                    f"Mesa {mesa.numero}",
                    f"Mesa {mesa.numero} - {mesa.capacidad} personas"
                )
            )

        # Si estamos editando una reserva
        if self.instance and self.instance.pk:

            mesa_actual = self.instance.mesa

            existe = any(
                opcion[0] == mesa_actual
                for opcion in opciones
            )

            if not existe:

                opciones.append(
                    (
                        mesa_actual,
                        f"{mesa_actual} (Actual)"
                    )
                )

        self.fields['mesa'].choices = opciones