from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

# --- EL CEREBRO DE LA CONSOLA (MANAGER) ---
class UsuarioManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El usuario debe tener un correo electrónico')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        # Forzamos a que si nace por consola, nazca como administrador
        extra_fields.setdefault('rol', 'administrador')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El Superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El Superusuario debe tener is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

# --- TU MODELO DE USUARIO ---
class Usuario(AbstractUser):
    ROLES = (
        ('administrador', 'Administrador'),
        ('secretario', 'Secretario'),
        ('mesero', 'Mesero'),
        ('cajero', 'Cajero'),
        ('jefe_cocina', 'Jefe de Cocina'),
    )
    email = models.EmailField(unique=True, verbose_name='Correo Electrónico')
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    
    # 🔥 NUEVO CAMPO: Permite ocultar visualmente al usuario sin destruir sus relaciones en la BD
    es_anonimo = models.BooleanField(default=False, verbose_name='¿Está anonimizado?')

    objects = UsuarioManager()

    # PERMISOS DE MÓDULOS PERSONALIZADOS
    class Meta:
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

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"