from django.db import models
from django.conf import settings  # <-- Importamos los settings en lugar de User

class Auditoria(models.Model):
    # Opciones para darle el color al puntito en tu HTML
    OPCIONES_MODULO = [
        ('menu', 'Menú'),             # Para el punto amarillo
        ('pedidos', 'Pedidos'),       # Para el punto azul
        ('reservas', 'Reservas'),     # Para el punto verde
        ('usuarios', 'Usuarios'),     # Para el punto morado
        ('facturacion', 'Facturación')
    ]

    # <-- Apuntamos a settings.AUTH_USER_MODEL -->
    id_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # De qué módulo viene para pintar el color
    modulo = models.CharField(max_length=20, choices=OPCIONES_MODULO)
    
    # Qué hizo (Ej: "creado", "confirmada", "modificó precio")
    accion = models.CharField(max_length=255)
    
    # El dato exacto (Ej: "Mesa 7 - $45.50" o "Pizza Especial $12.50 -> $13.00")
    detalle = models.CharField(max_length=255)
    
    # Cuándo lo hizo (Django guarda fecha y hora automáticamente)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        # Ordenamos para que el más reciente salga arriba, justo como en tu diseño
        ordering = ['-fecha_hora'] 

    def __str__(self):
        usuario_nombre = self.id_usuario.username if self.id_usuario else 'Sistema'
        return f"{usuario_nombre} - {self.accion} - {self.fecha_hora.strftime('%H:%M')}"