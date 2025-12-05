# 🎓 Sistema de Chamada de Alunos - Projeto Integrador

Sistema completo para gerenciamento de chamadas de alunos em instituições de ensino superior.

## 📋 Sobre o Projeto

Este projeto foi desenvolvido como trabalho final do curso de Python, implementando uma API RESTful para gerenciamento de presenças de alunos com dashboards analíticos.

### 🎯 Funcionalidades

- ✅ Gestão de Professores, Alunos e Turmas
- ✅ Sistema de chamada de presenças
- ✅ Dashboard analítico por turma
- ✅ Autenticação por token JWT
- ✅ Permissões por perfil (Admin, Professor, Aluno)
- ✅ API REST documentada com Swagger
- ✅ Estatísticas de frequência

### 🏗️ Arquitetura

- **Backend:** Django + Django REST Framework
- **Banco de Dados:** PostgreSQL / SQLite
- **Autenticação:** Token Authentication
- **Documentação:** drf-spectacular (Swagger/Redoc)

## 🚀 Instalação Local

1. **Clonar repositório:**

git clone https://github.com/Melizzano/sistema-chamada-alunos.git

cd sistema-chamada-alunos

2. **Criar ambiente virtual:**

python -m venv venv

venv\Scripts\activate  # Windows

3. **Instalar dependências:**

cd backend

pip install -r requirements.txt

pip install -r requirements_prod.tx

4. **Configurar banco de dados:**

python manage.py migrate

python manage.py createsuperuser

5. **Executar servidor:**

python manage.py runserver
