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

    1.1 git clone https://github.com/Melizzano/sistema-chamada-alunos.git

    1.2 cd sistema-chamada-alunos

2. **Criar ambiente virtual:**

    2.1 python -m venv venv

    2.2 venv\Scripts\activate  # Windows

3. **Instalar dependências:**

    3.1 cd backend

    3.2 pip install -r requirements.txt

    3.3 pip install -r requirements_prod.tx

4. **Configurar banco de dados:**

    4.1 python manage.py migrate

    4.2 python manage.py createsuperuser

5. **Executar servidor:**

    5.1 python manage.py runserver
