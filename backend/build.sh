#!/usr/bin/env bash
# Script de build para Render

set -o errexit

echo "Instalando dependências..."
pip install -r requirements_prod.txt

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "Aplicando migrações..."
python manage.py migrate