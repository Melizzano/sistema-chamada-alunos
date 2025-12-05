"""
Testes para as views de análises.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

from .models import Professor, Aluno, Turma, Matricula, Presenca


class AnalyticsTestCase(APITestCase):
    """Testes para endpoints de análises."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Criar usuários
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        
        self.professor_user = User.objects.create_user(
            username='professor',
            email='professor@test.com',
            password='prof123'
        )
        
        self.aluno_user = User.objects.create_user(
            username='aluno',
            email='aluno@test.com',
            password='aluno123'
        )
        
        # Criar professor
        self.professor = Professor.objects.create(
            nome='Professor Teste',
            email='professor@test.com',
            departamento='Computação',
            ativo=True,
            usuario=self.professor_user
        )
        
        # Criar aluno
        self.aluno = Aluno.objects.create(
            nome='Aluno Teste',
            matricula='20240001',
            email='aluno@test.com',
            curso='Engenharia de Software',
            data_nascimento=date(2000, 1, 1),
            genero='M',
            usuario=self.aluno_user
        )
        
        # Criar turma
        self.turma = Turma.objects.create(
            nome='Python Avançado',
            descricao='Curso de Python',
            professor=self.professor,
            data_inicio=date.today() - timedelta(days=30),
            data_fim=date.today() + timedelta(days=30),
            status='Ativa'
        )
        
        # Matricular aluno
        self.matricula = Matricula.objects.create(
            turma=self.turma,
            aluno=self.aluno
        )
        
        # Criar algumas presenças
        for i in range(10):
            Presenca.objects.create(
                matricula=self.matricula,
                data=date.today() - timedelta(days=i),
                status='Presente' if i < 8 else 'Ausente'  # 80% de presença
            )
    
    def test_dashboard_professor_autenticado(self):
        """Testa dashboard do professor autenticado."""
        self.client.force_authenticate(user=self.professor_user)
        response = self.client.get(reverse('dashboard-professor'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('estatisticas_gerais', response.data)
        self.assertIn('turmas', response.data)
    
    def test_dashboard_aluno_autenticado(self):
        """Testa dashboard do aluno autenticado."""
        self.client.force_authenticate(user=self.aluno_user)
        response = self.client.get(reverse('dashboard-aluno'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('estatisticas_gerais', response.data)
        self.assertIn('desempenho_por_turma', response.data)
    
    def test_analytics_geral_admin(self):
        """Testa analytics geral apenas para admin."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('analytics-geral'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('estatisticas_gerais', response.data)
        self.assertIn('alertas', response.data)
    
    def test_analytics_geral_nao_admin(self):
        """Testa que não-admin não pode acessar analytics geral."""
        self.client.force_authenticate(user=self.professor_user)
        response = self.client.get(reverse('analytics-geral'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_relatorio_presenca_admin(self):
        """Testa geração de relatório por admin."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'data_inicio': (date.today() - timedelta(days=30)).isoformat(),
            'data_fim': date.today().isoformat(),
            'turma_id': self.turma.id
        }
        response = self.client.post(reverse('relatorio-presenca'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('totais', response.data)
        self.assertIn('detalhes_por_turma', response.data)
    
    def test_dashboard_professor_por_id(self):
        """Testa dashboard do professor por ID."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(
            reverse('dashboard-professor-id', kwargs={'professor_id': self.professor.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['professor']['id'], self.professor.id)
    
    def test_dashboard_aluno_por_id(self):
        """Testa dashboard do aluno por ID."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(
            reverse('dashboard-aluno-id', kwargs={'aluno_id': self.aluno.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['aluno']['id'], self.aluno.id)
    
    def test_dashboard_aluno_outro_aluno(self):
        """Testa que aluno não pode ver dashboard de outro aluno."""
        outro_aluno_user = User.objects.create_user(
            username='outroaluno',
            password='outro123'
        )
        outro_aluno = Aluno.objects.create(
            nome='Outro Aluno',
            matricula='20240002',
            email='outro@test.com',
            curso='Matemática',
            data_nascimento=date(2001, 1, 1),
            genero='F',
            usuario=outro_aluno_user
        )
        
        self.client.force_authenticate(user=self.aluno_user)
        response = self.client.get(
            reverse('dashboard-aluno-id', kwargs={'aluno_id': outro_aluno.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)