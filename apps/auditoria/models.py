from django.db import models
from django.conf import settings 

class Auditoria(models.Model):
    # Opciones para clasificar el módulo y asignar estilos visuales en el HTML
    OPCIONES_MODULO = [
        ('menu', 'Menú'),             
        ('pedidos', 'Pedidos'),       
        ('reservas', 'Reservas'),     
        ('usuarios', 'Usuarios'),     
        ('facturacion', 'Facturación'),
        ('mesas', 'Mesas')            # 🎯 Módulo de mesas registrado
    ]

    # Relación con el usuario que realiza la acción (se vuelve NULL si el usuario se elimina)
    id_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Atributos del registro de auditoría
    modulo = models.CharField(max_length=20, choices=OPCIONES_MODULO)
    accion = models.CharField(max_length=255)  
    detalle = models.CharField(max_length=255) 
    fecha_hora = models.DateTimeField(auto_now_add=True) 

    class Meta:
        db_table = 'auditoria'
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        ordering = ['-fecha_hora']

    def __str__(self):
        usuario = self.id_usuario.username if self.id_usuario else "Usuario Eliminado"
        return f"{usuario} - {self.modulo} - {self.accion} ({self.fecha_hora})"