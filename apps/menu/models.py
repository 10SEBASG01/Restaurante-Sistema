from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class CategoriasPlato(models.Model):
    """
    Representa el catálogo de clasificaciones o agrupaciones del menú del restaurante.
    Permite la escalabilidad al admitir que las categorías crezcan dinámicamente.
    """
    # Nota de diseño: Se conserva la tupla de referencia como histórico, 
    # pero el modelo permite registros libres y dinámicos en producción.
    CATEGORIAS_CHOICES = (
        ('Entradas', 'Entradas'),
        ('Sopas', 'Sopas'),
        ('Platos fuertes', 'Platos fuertes'),
        ('Parrilladas', 'Parrilladas'),
        ('Mariscos', 'Mariscos'),
        ('Postres', 'Postres'),
        ('Bebidas', 'Bebidas'),
        ('Cócteles', 'Cócteles'),
        ('Comida rápida', 'Comida rápida'),
    )

    id_categoria = models.AutoField(primary_key=True)
    
    # CRÍTICO: 'unique=True' impide la duplicidad de nombres de categorías en el sistema
    nombre_categoria = models.CharField(
        max_length=100, 
        unique=True
    )

    class Meta:
        db_table = 'categorias_plato'  # Fuerza el nombre exacto de la tabla en SQL
        verbose_name = 'Categoría de Plato'
        verbose_name_plural = 'Categorías de Platos'

    def __str__(self):
        return self.nombre_categoria


class GestionPlatillo(models.Model):
    """
    Almacena los datos individuales de cada comida o bebida disponible en el establecimiento.
    Controla precios mínimos, estados de disponibilidad, imágenes y su borrado lógico.
    """
    id_platillo = models.AutoField(primary_key=True)
    nombre_platillo = models.CharField(max_length=150, unique=False)
    descripcion = models.TextField(blank=True, null=True)
    
    # CRÍTICO: El validador MinValueValidator asegura a nivel de base de datos que 
    # el precio ingresado sea estrictamente mayor o igual a $0.01 centavos.
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # CRÍTICO: 'on_delete=models.PROTECT' evita que una categoría sea eliminada de la base 
    # de datos si todavía contiene platillos asociados, previniendo errores de datos huérfanos.
    id_categoria = models.ForeignKey(
        CategoriasPlato, 
        on_delete=models.PROTECT, 
        db_column='id_categoria',
        related_name='platillos'
    )
    
    disponible = models.BooleanField(default=True)  # Visibilidad para el mesero (si hay o no stock)
    
    # CRÍTICO: Campo implementado para 'Borrado Lógico'. En lugar de ejecutar un 'DELETE' real, 
    # se cambia a False para preservar el historial de comandas antiguas asociadas a este platillo.
    activo = models.BooleanField(default=True)  
    
    imagen = models.ImageField(upload_to='menu/platillos/', blank=True, null=True)

    class Meta:
        db_table = 'gestion_platillo'  # Mapeo explícito a la tabla física en PostgreSQL/MySQL
        verbose_name = 'Gestión de Platillo'
        verbose_name_plural = 'Gestión de Platillos'

    def __str__(self):
        return self.nombre_platillo