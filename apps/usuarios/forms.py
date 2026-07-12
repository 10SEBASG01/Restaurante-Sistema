from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario

# =====================================================================
# 🎯 1. FORMULARIO PARA CREAR EMPLEADOS (USADO POR EL ADMIN)
# =====================================================================
class CustomUserCreationForm(UserCreationForm):
    """
    Formulario especializado para la creación de cuentas del personal operativo.
    Hereda de 'UserCreationForm' de Django para asegurar que las contraseñas 
    se procesen y se guarden encriptadas (hash) desde el primer momento, 
    cumpliendo con los estándares de seguridad.
    """

    # ==========================================
    # ⚙️ CONFIGURACIÓN DEL MODELO
    # ==========================================
    class Meta:
        model = Usuario
        # Campos explícitos que se pedirán al momento de crear un nuevo empleado
        fields = ('username', 'email', 'first_name', 'last_name', 'rol', 'is_active')
        labels = {
            'username': 'Nombre de Usuario',
            'email': 'Correo Electrónico',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'rol': 'Rol asignado',
            'is_active': '¿Es un usuario activo?',
        }

    # ==========================================
    # 🔧 INICIALIZACIÓN Y LÓGICA DINÁMICA
    # ==========================================
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtramos roles: El administrador solo puede crear personal de trabajo,
        # por lo que quitamos la opción de 'cliente' del menú desplegable.
        opciones_personal = [(clave, valor) for clave, valor in Usuario.ROLES if clave != 'cliente']
        self.fields['rol'].choices = opciones_personal
        self.fields['rol'].initial = 'mesero'

        # Limpieza de la interfaz: Quitamos el texto largo por defecto de Django en username
        self.fields['username'].help_text = ''
        
        # Explicación clara sobre el "borrado lógico" (Soft Delete)
        self.fields['is_active'].help_text = 'Desmarca para desactivar al empleado sin borrar su historial.'

        # 🎨 Estilos Automáticos: Inyectamos diseño moderno y consistente a todos los inputs
        # sin necesidad de sobrecargar el código HTML de los templates.
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'style': 'width: 100%; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 15px;'
            })


# =====================================================================
# ✏️ 2. FORMULARIO PARA EDITAR EMPLEADOS (USADO POR EL ADMIN)
# =====================================================================
class UsuarioEditForm(forms.ModelForm):
    """
    Formulario diseñado exclusivamente para actualizar la información de un empleado 
    existente (Nombres, correos, cambio de rol o desactivación de cuenta). 
    Al heredar de ModelForm, no manipula ni expone las contraseñas.
    """

    # ==========================================
    # ⚙️ CONFIGURACIÓN DEL MODELO
    # ==========================================
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

    # ==========================================
    # 🔧 INICIALIZACIÓN Y LÓGICA DINÁMICA
    # ==========================================
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtramos roles: Evita que accidentalmente se degrade a un empleado al rol de 'cliente'
        opciones_personal = [(clave, valor) for clave, valor in Usuario.ROLES if clave != 'cliente']
        self.fields['rol'].choices = opciones_personal
        
        # Mantenemos la explicación del borrado lógico por consistencia
        self.fields['is_active'].help_text = 'Desmarca para desactivar al empleado sin borrar su historial.'
        
        # 🎨 Estilos Automáticos: Mantienen el mismo diseño UI que el formulario de creación
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'style': 'width: 100%; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 15px;'
            })