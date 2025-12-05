#!/bin/bash

# Script de deploy para Render

echo "🚀 Iniciando deploy do Sistema de Chamada de Alunos..."

# Verificar se está no diretório correto
if [ ! -f "backend/manage.py" ]; then
    echo "❌ Erro: Execute este script da raiz do projeto!"
    exit 1
fi

echo "1. Verificando arquivos necessários..."
REQUIRED_FILES=("render.yaml" "backend/requirements_prod.txt" "backend/build.sh")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Arquivo $file não encontrado!"
        exit 1
    fi
done

echo "2. Atualizando requirements..."
cd backend
pip freeze > requirements.txt

echo "3. Fazendo commit das mudanças..."
cd ..
git add .
git commit -m "preparando para deploy" || true

echo "4. Enviando para GitHub..."
git push origin main

echo "✅ Pronto para deploy!"
echo ""
echo "📋 Para fazer deploy no Render:"
echo "1. Acesse: https://render.com"
echo "2. Crie uma conta (com GitHub)"
echo "3. Clique em 'New +' -> 'Web Service'"
echo "4. Conecte seu repositório GitHub"
echo "5. Render detectará automaticamente o render.yaml"
echo "6. Clique em 'Create Web Service'"
echo ""
echo "🌐 Seu app estará em: https://sistema-chamada-alunos.onrender.com"