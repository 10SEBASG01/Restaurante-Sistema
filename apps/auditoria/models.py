from django.db import models
from django.conf import settings 

class Auditoria(models.Model):
    """
    🎯 MODELO DE AUDITORÍA CENTRALIZADA
    
    Permite registrar de manera cronológica e histórica todas las acciones 
    críticas realizadas por los usuarios dentro del ERP "Sabor & Arte".
    Sirve como bitácora de seguridad para el rastreo y control de cambios.
    """

    # ==========================================
    # 📌 CONFIGURACIONES Y LLAVES DE ENUMERACIÓN
    # ==========================================
    
    # Opciones para clasificar el módulo y asignar estilos visuales o etiquetas en el HTML
    OPCIONES_MODULO = [
        ('menu', 'Menú'),             
        ('pedidos', 'Pedidos'),       
        ('reservas', 'Reservas'),     
        ('usuarios', 'Usuarios'),     
        ('facturacion', 'Facturación'),
        ('mesas', 'Mesas')            # 🎯 Módulo de mesas registrado
    ]

    # ==========================================
    # 📝 ATRIBUTOS / CAMPOS DE LA BASE DE DATOS
    # ==========================================

    # Relación con el usuario que realiza la acción. 
    # Usamos SET_NULL para que si un empleado es eliminado, el registro de auditoría persista por seguridad.
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Usuario Ejecutor"
    )
    
    # Identifica a qué sección o módulo del sistema pertenece la acción ejecutada
    modulo = models.CharField(
        max_length=20, 
        choices=OPCIONES_MODULO,
        verbose_name="Módulo Afectado"
    )
    
    # Título corto o categoría de la acción (Ej: "Mesa Eliminada", "Pedido Creado")
    accion = models.CharField(
        max_length=255,
        verbose_name="Acción Realizada"
    )  
    
    # Explicación detallada y dinámica del evento (Ej: "Eliminó permanentemente la Mesa 5.")
    detalle = models.CharField(
        max_length=255,
        verbose_name="Detalles del Evento"
    ) 
    
    # Fecha y hora exacta de la transacción. Se genera automáticamente al insertar en la BD.
    fecha_hora = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y Hora"
    ) 

    # ==========================================
    # ⚙️ METADATOS DEL MODELO
    # ==========================================

    class Meta:
        db_table = 'auditoria'
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        # Ordena por defecto desde el registro más nuevo al más antiguo
        ordering = ['-fecha_hora']

    # ==========================================
    # 🔄 MÉTODOS DE REPRESENTACIÓN
    # ==========================================

    def __str__(self):
        """
        Devuelve una cadena legible que identifica de forma rápida el registro.
        Previene fallos controlando si el usuario original ya no existe en el sistema.
        """
        usuario = self.id_usuario.username if self.id_usuario else "Usuario Eliminado"
        return f"{usuario} - {self.modulo} - {self.accion} ({self.fecha_hora})"