import os
import django
import random
from datetime import date, timedelta
from django.utils import timezone

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Professor, Aluno, Turma, Matricula, Presenca

def criar_professores():
    professores = [
        {'nome': 'Carlos Silva', 'email': 'carlos.silva@universidade.edu', 'departamento': 'Matemática'},
        {'nome': 'Ana Santos', 'email': 'ana.santos@universidade.edu', 'departamento': 'Computação'},
        {'nome': 'Roberto Alves', 'email': 'roberto.alves@universidade.edu', 'departamento': 'Estatística'},
    ]
    
    for prof in professores:
        Professor.objects.create(**prof)
    
    print(f"{len(professores)} professores criados.")

def criar_alunos():
    cursos = ['Engenharia de Software', 'Ciência da Computação', 'Matemática', 'Estatística']
    alunos_data = []
    
    for i in range(1, 21):  # Criar 20 alunos
        alunos_data.append({
            'nome': f'Aluno {i} Teste',
            'matricula': f'2024000{i:02d}',
            'email': f'aluno{i}@universidade.edu',
            'curso': random.choice(cursos),
            'data_nascimento': date(2000 + i % 5, (i % 12) + 1, (i % 28) + 1),
            'genero': random.choice(['M', 'F']),
        })
    
    for aluno in alunos_data:
        Aluno.objects.create(**aluno)
    
    print(f"{len(alunos_data)} alunos criados.")

def criar_turmas():
    professores = Professor.objects.all()
    turmas_data = [
        {'nome': 'Cálculo I', 'descricao': 'Introdução ao cálculo diferencial e integral'},
        {'nome': 'Programação Python', 'descricao': 'Fundamentos de programação em Python'},
        {'nome': 'Estatística Aplicada', 'descricao': 'Estatística para ciência de dados'},
        {'nome': 'Banco de Dados', 'descricao': 'Modelagem e implementação de bancos de dados'},
    ]
    
    hoje = date.today()
    for i, turma_info in enumerate(turmas_data):
        Turma.objects.create(
            nome=turma_info['nome'],
            descricao=turma_info['descricao'],
            professor=professores[i % len(professores)],
            data_inicio=hoje - timedelta(days=30),
            data_fim=hoje + timedelta(days=60),
            status='Ativa'
        )
    
    print(f"{len(turmas_data)} turmas criadas.")

def criar_matriculas():
    turmas = Turma.objects.all()
    alunos = Aluno.objects.all()
    
    for turma in turmas:
        # Matricular 5-10 alunos em cada turma
        alunos_turma = random.sample(list(alunos), random.randint(5, 10))
        for aluno in alunos_turma:
            Matricula.objects.get_or_create(turma=turma, aluno=aluno)
    
    print("Matrículas criadas.")

def definir_representantes():
    turmas = Turma.objects.all()
    for turma in turmas:
        if not turma.representante:
            # Escolher um aluno matriculado como representante
            matriculas = turma.matriculas.all()
            if matriculas.exists():
                turma.representante = matriculas.first().aluno
                turma.save()
    
    print("Representantes definidos.")

def criar_presencas():
    matriculas = Matricula.objects.all()
    hoje = timezone.now().date()
    
    for matricula in matriculas:
        # Criar presenças para os últimos 10 dias
        for dias_atras in range(10):
            data_aula = hoje - timedelta(days=dias_atras)
            
            # 80% de chance de estar presente
            status = 'Presente' if random.random() < 0.8 else 'Ausente'
            
            Presenca.objects.get_or_create(
                matricula=matricula,
                data=data_aula,
                defaults={'status': status}
            )
    
    print("Registros de presença criados.")

if __name__ == '__main__':
    print("Populando banco de dados com dados de teste...")
    
    # Limpar dados existentes (opcional - descomente se quiser recriar tudo)
    # Presenca.objects.all().delete()
    # Matricula.objects.all().delete()
    # Turma.objects.all().delete()
    # Aluno.objects.all().delete()
    # Professor.objects.all().delete()
    
    criar_professores()
    criar_alunos()
    criar_turmas()
    criar_matriculas()
    definir_representantes()
    criar_presencas()
    
    print("✅ Banco de dados populado com sucesso!")