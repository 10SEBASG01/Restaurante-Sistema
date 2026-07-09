from django import forms
from .models import GestionPlatillo

class PlatilloForm(forms.ModelForm):
    """
    Formulario vinculado al modelo GestionPlatillo.
    Se encarga del mapeo automático de campos, la inyección de clases CSS 
    para Bootstrap y el control estricto de reglas de negocio en los datos.
    """
    
    class Meta:
        # Vinculación directa con el modelo de la Base de Datos
        model = GestionPlatillo
        
        # Campos explícitos que serán expuestos en la interfaz de usuario
        fields = ['nombre_platillo', 'descripcion', 'precio', 'id_categoria', 'disponible', 'imagen']
        
        # --- CONFIGURACIÓN DE WIDGETS ---
        # Personaliza el tipo de input HTML y les inyecta atributos/clases dinámicamente.
        widgets = {
            'nombre_platillo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Ceviche Premium'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ingredientes...'}),
            
            # CRÍTICO: 'step' y 'min' restringen a nivel de HTML5 el ingreso de números decimales y positivos
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            
            # Renderiza un menú desplegable (<select>) alimentado por las llaves foráneas de Categorías
            'id_categoria': forms.Select(attrs={'class': 'form-control'}),
            
            # Cambia la clase para que Bootstrap lo renderice como un switch/checkbox moderno
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # Maneja de manera segura la carga de archivos multimedia (imágenes del platillo)
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    # --- VALIDACIONES ESPECÍFICAS (CLEAN METHODS) ---
    def clean_precio(self):
        """
        Validación personalizada para el campo 'precio' a nivel de servidor.
        Garantiza que ningún platillo sea registrado con valor negativo o cero,
        actuando como segunda capa de seguridad si la validación HTML5 es vulnerada.
        """
        precio = self.cleaned_data.get('precio')
        
        # CRÍTICO: Detiene el flujo de guardado si el precio no cumple la regla de negocio
        if precio is not None and precio <= 0:
            raise forms.ValidationError("El precio debe ser un valor mayor a cero.")
            
        return precio