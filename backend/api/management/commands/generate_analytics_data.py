from django.core.management.base import BaseCommand
import random
from datetime import date, timedelta
from django.utils import timezone
from api.models import Professor, Aluno, Turma, Matricula, Presenca
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Gera dados de teste para análises estatísticas'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Gerando dados para análises...'))
        
        # Limpar dados existentes (opcional)
        # Presenca.objects.all().delete()
        # Matricula.objects.all().delete()
        # Turma.objects.all().delete()
        # Aluno.objects.all().delete()
        # Professor.objects.all().delete()
        
        # Criar mais professores
        departamentos = ['Matemática', 'Computação', 'Estatística', 'Física', 'Química']
        for i in range(5):
            Professor.objects.get_or_create(
                nome=f'Professor {i+1}',
                email=f'professor{i+1}@ifb.edu',
                departamento=random.choice(departamentos),
                ativo=True
            )
        
        # Criar mais alunos
        cursos = [
            'Engenharia de Software',
            'Ciência da Computação',
            'Matemática',
            'Estatística',
            'Física',
            'Química'
        ]
        
        for i in range(50):
            Aluno.objects.get_or_create(
                nome=f'Aluno {i+1}',
                matricula=f'2024{i+1:04d}',
                email=f'aluno{i+1}@ifb.edu',
                curso=random.choice(cursos),
                data_nascimento=date(1998 + (i % 5), (i % 12) + 1, (i % 28) + 1),
                genero=random.choice(['M', 'F'])
            )
        
        self.stdout.write(self.style.SUCCESS('Professores e alunos criados.'))
        
        # Criar mais turmas
        professores = Professor.objects.all()
        disciplinas = [
            ('Cálculo I', 'Introdução ao cálculo'),
            ('Programação Python', 'Fundamentos de Python'),
            ('Banco de Dados', 'Modelagem de dados'),
            ('Estatística', 'Estatística básica'),
            ('Física I', 'Mecânica clássica'),
            ('Química Geral', 'Conceitos fundamentais'),
            ('Álgebra Linear', 'Vetores e matrizes'),
            ('Estrutura de Dados', 'Algoritmos e estruturas'),
            ('Redes de Computadores', 'Fundamentos de redes'),
            ('Inteligência Artificial', 'IA básica')
        ]
        
        for i, (nome, desc) in enumerate(disciplinas):
            Turma.objects.get_or_create(
                nome=nome,
                descricao=desc,
                professor=random.choice(professores),
                data_inicio=date.today() - timedelta(days=random.randint(0, 60)),
                data_fim=date.today() + timedelta(days=random.randint(30, 120)),
                status=random.choice(['Ativa', 'Ativa', 'Ativa', 'Concluída'])  # 75% ativas
            )
        
        self.stdout.write(self.style.SUCCESS('Turmas criadas.'))
        
        # Matricular alunos em turmas
        turmas = Turma.objects.all()
        alunos = Aluno.objects.all()
        
        for turma in turmas:
            # Matricular 10-20 alunos em cada turma
            alunos_turma = random.sample(list(alunos), random.randint(10, 20))
            for aluno in alunos_turma:
                Matricula.objects.get_or_create(turma=turma, aluno=aluno)
        
        self.stdout.write(self.style.SUCCESS('Matrículas criadas.'))
        
        # Criar presenças realistas
        matriculas = Matricula.objects.all()
        hoje = timezone.now().date()
        
        for matricula in matriculas:
            # Criar presenças para os últimos 60 dias (dias de semana)
            for dias_atras in range(60):
                data_aula = hoje - timedelta(days=dias_atras)
                
                # Apenas dias de semana (segunda a sexta)
                if data_aula.weekday() < 5:
                    # Taxa de presença baseada no "perfil" do aluno
                    # Alguns alunos têm melhor frequência que outros
                    perfil_aluno = hash(str(matricula.aluno_id)) % 10
                    
                    if perfil_aluno < 7:  # 70% dos alunos têm boa frequência
                        chance_presenca = 0.85  # 85% de chance de estar presente
                    elif perfil_aluno < 9:  # 20% têm frequência média
                        chance_presenca = 0.70  # 70% de chance
                    else:  # 10% têm baixa frequência
                        chance_presenca = 0.40  # 40% de chance
                    
                    # Status baseado na chance
                    if random.random() < chance_presenca:
                        status_presenca = 'Presente'
                    else:
                        status_presenca = 'Ausente'
                    
                    # Pequena chance de justificativa
                    if status_presenca == 'Ausente' and random.random() < 0.2:
                        status_presenca = 'Justificado'
                    
                    Presenca.objects.get_or_create(
                        matricula=matricula,
                        data=data_aula,
                        defaults={'status': status_presenca}
                    )
        
        self.stdout.write(self.style.SUCCESS('Presenças criadas.'))
        
        # Estatísticas finais
        self.stdout.write(self.style.SUCCESS('\n📊 DADOS GERADOS:'))
        self.stdout.write(self.style.SUCCESS(f'  Professores: {Professor.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Alunos: {Aluno.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Turmas: {Turma.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Matrículas: {Matricula.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Presenças: {Presenca.objects.count()}'))
        
        # Calcular taxa de presença geral
        total_presencas = Presenca.objects.count()
        if total_presencas > 0:
            presentes = Presenca.objects.filter(status='Presente').count()
            taxa = (presentes / total_presencas) * 100
            self.stdout.write(self.style.SUCCESS(f'  Taxa de presença geral: {taxa:.2f}%'))