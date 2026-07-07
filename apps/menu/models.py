from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class CategoriasPlato(models.Model):
    # Definimos las 9 categorías oficiales de tu documentación en una tupla
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
    # CORRECCIÓN: Se quitó el choices para permitir categorías dinámicas
    nombre_categoria = models.CharField(
        max_length=100, 
        unique=True
    )

    class Meta:
        db_table = 'categorias_plato'
        verbose_name = 'Categoría de Plato'
        verbose_name_plural = 'Categorías de Platos'

    def __str__(self):
        # CORRECCIÓN: Como ya no usa choices, devolvemos el campo directo
        return self.nombre_categoria


class GestionPlatillo(models.Model):
    id_platillo = models.AutoField(primary_key=True)
    nombre_platillo = models.CharField(max_length=150, unique=False)
    descripcion = models.TextField(blank=True, null=True)
    
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    id_categoria = models.ForeignKey(
        CategoriasPlato, 
        on_delete=models.PROTECT, 
        db_column='id_categoria',
        related_name='platillos'
    )
    
    disponible = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)  # Campo para el borrado lógico
    imagen = models.ImageField(upload_to='menu/platillos/', blank=True, null=True)

    class Meta:
        db_table = 'gestion_platillo'
        verbose_name = 'Gestión de Platillo'
        verbose_name_plural = 'Gestión de Platillos'

    def __str__(self):
        return self.nombre_platillo