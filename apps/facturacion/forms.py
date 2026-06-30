from django import forms
from django.core.exceptions import ValidationError
from .models import Factura

class FacturaForm(forms.ModelForm):
    # Definimos los campos opcionales explícitamente
    cliente_correo = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'ejemplo@correo.com (Opcional)'
        })
    )
    
    cliente_direccion = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Ej. Av. de los Granados (Opcional)'
        })
    )

    descuento = forms.IntegerField(
        initial=0,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1',
            'min': '0',
            'max': '100',
            'style': 'width: 110px; text-align: right;',
            'onkeypress': 'return event.charCode >= 48 && event.charCode <= 57;'
        }),
        label="Descuento (%)"
    )

    class Meta:
        model = Factura
        fields = [
            'cliente_nombre', 
            'cliente_identificacion', 
            'cliente_correo', 
            'cliente_direccion',
            'forma_pago',   
            'descuento'     
        ]
        widgets = {
            'cliente_nombre': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej. Juan Pérez o Consumidor Final'
            }),
            'cliente_identificacion': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Cédula (10 dígitos) o RUC (13 dígitos)'
            }),
            'forma_pago': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def clean_cliente_identificacion(self):
        identificacion = self.cleaned_data.get('cliente_identificacion', '').strip()
        
        if identificacion in ["9999999999", "9999999999999"]:
            return identificacion

        if len(identificacion) not in [10, 13]:
            raise ValidationError("La identificación debe tener 10 dígitos (Cédula) o 13 dígitos (RUC).")
            
        if not identificacion.isdigit():
            raise ValidationError("La identificación debe contener únicamente caracteres numéricos.")
            
        return identificacion

    def clean(self):
        cleaned_data = super().clean()
        nombre = cleaned_data.get('cliente_nombre')
        identificacion = cleaned_data.get('cliente_identificacion')
        direccion = cleaned_data.get('cliente_direccion')
        correo = cleaned_data.get('cliente_correo')

        # Coherencia automática para Consumidor Final
        if identificacion in ["9999999999", "9999999999999"]:
            if not nombre or nombre.lower() in ["", "consumidor final"]:
                cleaned_data['cliente_nombre'] = "Consumidor Final"
            
            # Si no hay dirección, asignamos un valor por defecto
            if not direccion:
                cleaned_data['cliente_direccion'] = "N/A"
            
            # Si no hay correo, lo dejamos como None para evitar errores de validación de EmailField
            if not correo:
                cleaned_data['cliente_correo'] = None 
        
        return cleaned_data