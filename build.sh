#!/usr/bin/env bash
# Le indica al sistema operativo que este archivo es un script y debe ejecutarse usando la terminal Bash.

# Hace que el script se detenga por completo si algún comando llega a fallar.
# Es una medida de seguridad vital para que no se despliegue una versión rota del sistema.
set -o errexit

echo "📦 Instalando dependencias..."
# Lee tu archivo requirements.txt e instala todas las librerías necesarias 
# para que el proyecto funcione (Django, los adaptadores de base de datos, etc.).
pip install -r requirements.txt

echo "📁 Recolectando archivos estáticos..."
# Agrupa todos los archivos CSS, JavaScript e imágenes de tu proyecto en una sola carpeta.
# Esto prepara los archivos para que sean servidos eficientemente.
# El flag '--no-input' es clave porque evita que la consola se detenga a pedirte que escribas "yes" para confirmar.
python manage.py collectstatic --no-input

echo "🗄️ Aplicando migraciones..."
# Traduce los modelos de Django a tablas y columnas reales en tu base de datos PostgreSQL.
# Asegura que la base de datos tenga la estructura correcta (ej. las tablas para cocina, facturación, etc.).
python manage.py migrate

echo "👤 Creando superusuario..."
# Ejecuta un comando personalizado de Django que asegura la existencia de un usuario administrador.
# Muy útil para no quedarte fuera del panel de administración (admin) en un despliegue nuevo.
python manage.py createsuperuser_if_not_exists

echo "✅ Build finalizado."