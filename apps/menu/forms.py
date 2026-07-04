from django import forms
from .models import GestionPlatillo

class PlatilloForm(forms.ModelForm):
    class Meta:
        model = GestionPlatillo
        fields = ['nombre_platillo', 'descripcion', 'precio', 'id_categoria', 'disponible', 'imagen']
        widgets = {
            'nombre_platillo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Ceviche Premium'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ingredientes...'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'id_categoria': forms.Select(attrs={'class': 'form-control'}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None and precio <= 0:
            raise forms.ValidationError("El precio debe ser un valor mayor a cero.")
        return precio