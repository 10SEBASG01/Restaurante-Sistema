#!/usr/bin/env bash
set -o errexit

echo "📦 Instalando dependencias..."
pip install -r requirements.txt

echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --no-input

echo "🗄️ Aplicando migraciones..."
python manage.py migrate

echo "👤 Creando superusuario..."
python manage.py createsuperuser_if_not_exists

echo "✅ Build finalizado."