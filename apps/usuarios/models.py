from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

# =====================================================================
# 🧠 MANAGER: EL CEREBRO DE LA CREACIÓN DE USUARIOS
# =====================================================================
class UsuarioManager(BaseUserManager):
    """
    Gestiona la creación de usuarios y superusuarios en la base de datos, 
    sobrescribiendo el comportamiento por defecto de Django para exigir 
    el correo electrónico y asignar roles automáticamente desde la consola.
    """
    
    def create_user(self, username, email, password=None, **extra_fields):
        """
        Crea y guarda un usuario regular con su nombre, correo y contraseña.
        Aplica validaciones de seguridad básicas.
        """
        if not email:
            raise ValueError('El usuario debe tener un correo electrónico')
        
        # Estandariza el formato del correo (minúsculas en el dominio, etc.)
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        
        # Encripta la contraseña antes de guardarla en la BD
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Crea y guarda un Superusuario (Ej: al usar 'python manage.py createsuperuser').
        Garantiza que nazca con todos los permisos del sistema y el rol correcto.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        # Forzamos a que si nace por consola, nazca con el rol de máxima jerarquía
        extra_fields.setdefault('rol', 'administrador')

        # Validaciones de seguridad para evitar superusuarios defectuosos
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El Superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El Superusuario debe tener is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


# =====================================================================
# 👤 MODELO PRINCIPAL DE IDENTIDAD Y ACCESO (IAM)
# =====================================================================
class Usuario(AbstractUser):
    """
    🎯 MODELO DE USUARIO PERSONALIZADO
    
    Sustituye al modelo de usuario tradicional de Django. Centraliza la 
    información del personal del restaurante, definiendo sus roles operativos 
    y los permisos modulares de acceso al ERP.
    """

    # ==========================================
    # 📌 CONFIGURACIONES Y ROLES DE SISTEMA
    # ==========================================
    ROLES = (
        ('administrador', 'Administrador'),
        ('secretario', 'Secretario'),
        ('mesero', 'Mesero'),
        ('cajero', 'Cajero'),
        ('jefe_cocina', 'Jefe de Cocina'),
    )
    
    # ==========================================
    # 📝 ATRIBUTOS / CAMPOS DE LA BASE DE DATOS
    # ==========================================
    
    # Obligamos a que el correo sea único para evitar cuentas duplicadas
    email = models.EmailField(unique=True, verbose_name='Correo Electrónico')
    
    # Define la jerarquía del empleado (Por defecto 'cliente' si se registran externamente)
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    
    # 🔥 CAMPO DE SEGURIDAD HISTÓRICA: 
    # Permite ocultar visualmente al usuario (ej. si renuncia) sin destruir 
    # sus relaciones en la BD (para no romper auditorías, pedidos o facturas).
    es_anonimo = models.BooleanField(default=False, verbose_name='¿Está anonimizado?')

    # Conectamos este modelo con nuestro Manager personalizado
    objects = UsuarioManager()

    # ==========================================
    # ⚙️ METADATOS Y PERMISOS MODULARES
    # ==========================================
    class Meta:
        # Estos permisos se inyectan en la BD y permiten bloquear o habilitar 
        # las vistas y menús laterales dependiendo del rol del trabajador.
        permissions = [
            ("modulo_usuarios", "Acceso al módulo de Usuarios"),
            ("modulo_dashboard", "Acceso al módulo de Dashboard"),
            ("modulo_menu", "Acceso al módulo de Menú"),
            ("modulo_mesas", "Acceso al módulo de Mesas"),
            ("modulo_reservas", "Acceso al módulo de Reservas"),
            ("modulo_pedidos", "Acceso al módulo de Pedidos"),
            ("modulo_cocina", "Acceso al módulo de Cocina"),
            ("modulo_facturacion", "Acceso al módulo de Facturación"),
            ("modulo_reportes", "Acceso al módulo de Reportes"),
            ("modulo_panel_principal", "Puede ver el Panel Principal"),
        ]

    # ==========================================
    # 🔄 MÉTODOS DE REPRESENTACIÓN
    # ==========================================
    def __str__(self):
        """
        Formato de lectura rápida en el panel de administración o selects HTML.
        Ejemplo: "alan123 - Administrador"
        """
        return f"{self.username} - {self.get_rol_display()}"