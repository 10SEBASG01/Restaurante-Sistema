from django import forms
from .models import Mesa, ZonaMesa, Usuario

# --- 🔥 GESTIÓN DE ZONAS ---
class ZonaMesaForm(forms.ModelForm):
    class Meta:
        model = ZonaMesa
        fields = ['nombre_zona']
        labels = {
            'nombre_zona': 'Nombre de la Zona / Ubicación'
        }
        widgets = {
            'nombre_zona': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'width: 100%; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 15px;',
                'placeholder': 'Ej. Terraza, Salón VIP, Patio Exterior...'
            })
        }

# --- FORMULARIO 1: CREAR/EDITAR MESA ---
class MesaForm(forms.ModelForm):
    class Meta:
        model = Mesa
        fields = ('numero', 'capacidad', 'ubicacion', 'estado', 'cliente_nombre', 'mesero_assigned')
        labels = {
            'numero': 'Número de Mesa',
            'capacidad': 'Capacidad (Personas)',
            'ubicacion': 'Ubicación',
            'estado': 'Estado Inicial',
            'cliente_nombre': 'Cliente / Grupo (Opcional)',
            'mesero_assigned': 'Mesero Asignado',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mesero_assigned'].queryset = Usuario.objects.filter(rol='mesero', is_active=True)
        
        for field_name, field in self.fields.items():
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control',
                'style': 'width: 100%; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 15px;'
            })

    # 🔥 VALIDACIÓN DE CONTROL: Asegura limpieza visual si hay choques de números duplicados
    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        
        # Validamos si ya existe otra mesa activa con el mismo número
        queryset = Mesa.objects.filter(numero=numero, is_active=True)
        
        # Si estamos editando una mesa existente, excluimos su propio ID de la verificación
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
            
        if queryset.exists():
            raise forms.ValidationError("Ya existe una mesa activa registrada con este número.")
            
        return numero

# --- FORMULARIO 2: CAMBIAR ESTADO DESDE PANEL LATERAL ---
class CambiarEstadoMesaForm(forms.ModelForm):
    class Meta:
        model = Mesa
        fields = ['estado']
        labels = {'estado': 'Nuevo Estado de la Mesa'}
        widgets = {
            'estado': forms.Select(attrs={
                'class': 'form-control', 
                'style': 'width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; font-size: 15px;'
            })
        }

# --- FORMULARIO 3: ASIGNAR MESERO DESDE PANEL LATERAL ---
class AsignarMeseroForm(forms.ModelForm):
    class Meta:
        model = Mesa
        fields = ['cliente_nombre', 'mesero_assigned']
        labels = {
            'cliente_nombre': 'Nombre del Cliente / Grupo',
            'mesero_assigned': 'Mesero Asignado'
        }
        widgets = {
            'cliente_nombre': forms.TextInput(attrs={
                'class': 'form-control', 
                'style': 'width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; font-size: 15px;',
                'placeholder': 'Ej. Familia Vega (Opcional)'
            }),
            'mesero_assigned': forms.Select(attrs={
                'class': 'form-control', 
                'style': 'width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; font-size: 15px;'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mesero_assigned'].queryset = Usuario.objects.filter(rol='mesero', is_active=True)