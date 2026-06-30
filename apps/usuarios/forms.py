from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario

# --- 1. FORMULARIO PARA CREAR EMPLEADOS (USADO POR EL ADMIN) ---
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ('username', 'email', 'first_name', 'last_name', 'rol', 'is_active')
        labels = {
            'username': 'Nombre de Usuario',
            'email': 'Correo Electrónico',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'rol': 'Rol asignado',
            'is_active': '¿Es un usuario activo?',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtramos roles (sin clientes)
        opciones_personal = [(clave, valor) for clave, valor in Usuario.ROLES if clave != 'cliente']
        self.fields['rol'].choices = opciones_personal
        self.fields['rol'].initial = 'mesero'

        # Limpieza de textos
        self.fields['username'].help_text = ''
        self.fields['is_active'].help_text = 'Desmarca para desactivar al empleado sin borrar su historial.'

        # Estilos automáticos (Diseño Moderno)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'style': 'width: 100%; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 15px;'
            })

# --- 2. FORMULARIO PARA EDITAR EMPLEADOS (USADO POR EL ADMIN) ---
class UsuarioEditForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ('username', 'email', 'first_name', 'last_name', 'rol', 'is_active')
        labels = {
            'username': 'Nombre de Usuario',
            'email': 'Correo Electrónico',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'rol': 'Rol asignado',
            'is_active': '¿Es un usuario activo?',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtramos roles
        opciones_personal = [(clave, valor) for clave, valor in Usuario.ROLES if clave != 'cliente']
        self.fields['rol'].choices = opciones_personal
        
        # Texto de ayuda
        self.fields['is_active'].help_text = 'Desmarca para desactivar al empleado sin borrar su historial.'
        
        # Estilos automáticos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'style': 'width: 100%; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 15px;'
            })