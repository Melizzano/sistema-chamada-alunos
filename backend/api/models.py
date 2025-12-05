from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Professor(models.Model):
    """
    Entidade A: Representa os docentes responsáveis por turmas.
    Relacionamento: 1:N com Turma (um professor pode ter várias turmas)
    """
    nome = models.CharField(max_length=200, verbose_name="Nome Completo")
    email = models.EmailField(unique=True, verbose_name="E-mail")
    departamento = models.CharField(max_length=100, verbose_name="Departamento")
    ativo = models.BooleanField(default=True, verbose_name="Em Exercício")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    
    # Relacionamento com usuário do sistema (para autenticação)
    usuario = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='professor'
    )
    
    class Meta:
        verbose_name = "Professor"
        verbose_name_plural = "Professores"
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} ({self.departamento})"

class Aluno(models.Model):
    """
    Entidade C: Representa os estudantes matriculados.
    Relacionamento: N:N com Turma (através da tabela Matricula)
    """
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
        ('N', 'Prefiro não informar'),
    ]
    
    nome = models.CharField(max_length=200, verbose_name="Nome Completo")
    matricula = models.CharField(max_length=20, unique=True, verbose_name="Matrícula")
    email = models.EmailField(unique=True, verbose_name="E-mail")
    curso = models.CharField(max_length=100, verbose_name="Curso")
    data_nascimento = models.DateField(verbose_name="Data de Nascimento")
    genero = models.CharField(
        max_length=1, 
        choices=GENERO_CHOICES, 
        verbose_name="Gênero"
    )
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    
    # Relacionamento com usuário do sistema (para autenticação)
    usuario = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='aluno'
    )
    
    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} - {self.matricula}"
    
    def idade(self):
        """Calcula a idade do aluno"""
        today = timezone.now().date()
        return today.year - self.data_nascimento.year - (
            (today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )

class Turma(models.Model):
    """
    Entidade B: Representa as classes ou disciplinas lecionadas.
    Relacionamentos: 
    - 1:N com Professor (uma turma tem um professor)
    - N:N com Aluno (através da tabela Matricula)
    - 1:1 com Aluno (representante)
    """
    STATUS_CHOICES = [
        ('Ativa', 'Ativa'),
        ('Concluída', 'Concluída'),
        ('Cancelada', 'Cancelada'),
    ]
    
    nome = models.CharField(max_length=200, verbose_name="Nome da Turma")
    descricao = models.TextField(verbose_name="Descrição", blank=True)
    professor = models.ForeignKey(
        Professor, 
        on_delete=models.PROTECT, 
        related_name='turmas',
        verbose_name="Professor Responsável"
    )
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(verbose_name="Data de Término")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='Ativa',
        verbose_name="Status"
    )
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    
    # Relacionamento 1:1 com Aluno (representante)
    representante = models.OneToOneField(
        Aluno,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turma_representante',
        verbose_name="Aluno Representante"
    )
    
    class Meta:
        verbose_name = "Turma"
        verbose_name_plural = "Turmas"
        ordering = ['-data_inicio', 'nome']
    
    def __str__(self):
        return f"{self.nome} - {self.professor.nome}"
    
    @property
    def esta_ativa(self):
        """Verifica se a turma está ativa"""
        hoje = timezone.now().date()
        return self.status == 'Ativa' and self.data_inicio <= hoje <= self.data_fim

class Matricula(models.Model):
    """
    Tabela de junção para o relacionamento N:N entre Turma e Aluno.
    Inclui dados adicionais específicos da matrícula.
    """
    turma = models.ForeignKey(
        Turma, 
        on_delete=models.CASCADE, 
        related_name='matriculas'
    )
    aluno = models.ForeignKey(
        Aluno, 
        on_delete=models.CASCADE, 
        related_name='matriculas'
    )
    data_matricula = models.DateTimeField(auto_now_add=True, verbose_name="Data da Matrícula")
    presenca_acumulada = models.IntegerField(
        default=0,
        verbose_name="Presenças Acumuladas",
        validators=[MinValueValidator(0)]
    )
    
    class Meta:
        verbose_name = "Matrícula"
        verbose_name_plural = "Matrículas"
        unique_together = ['turma', 'aluno']  # Um aluno não pode se matricular duas vezes na mesma turma
        ordering = ['-data_matricula']
    
    def __str__(self):
        return f"{self.aluno.nome} em {self.turma.nome}"
    
    def taxa_presenca(self, total_aulas):
        """Calcula a taxa de presença do aluno na turma"""
        if total_aulas > 0:
            return (self.presenca_acumulada / total_aulas) * 100
        return 0

class Presenca(models.Model):
    """
    Entidade auxiliar para registrar chamadas diárias.
    Permite cálculos estatísticos de frequência.
    """
    STATUS_CHOICES = [
        ('Presente', 'Presente'),
        ('Ausente', 'Ausente'),
        ('Justificado', 'Justificado'),
    ]
    
    matricula = models.ForeignKey(
        Matricula, 
        on_delete=models.CASCADE, 
        related_name='presencas'
    )
    data = models.DateField(verbose_name="Data da Aula", default=timezone.now)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='Ausente',
        verbose_name="Status"
    )
    observacao = models.TextField(blank=True, verbose_name="Observação")
    data_registro = models.DateTimeField(auto_now_add=True, verbose_name="Data do Registro")
    
    class Meta:
        verbose_name = "Presença"
        verbose_name_plural = "Presenças"
        unique_together = ['matricula', 'data']  # Um aluno só pode ter um registro por dia
        ordering = ['-data', 'matricula__aluno__nome']
    
    def __str__(self):
        return f"{self.matricula.aluno.nome} - {self.data} - {self.status}"
    
    def save(self, *args, **kwargs):
        """Atualiza presenca_acumulada quando status é alterado"""
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            old_presenca = Presenca.objects.get(pk=self.pk)
            old_status = old_presenca.status
        
        super().save(*args, **kwargs)
        
        # Atualiza contador acumulado
        if is_new or old_status != self.status:
            self.atualizar_presenca_acumulada()
    
    def atualizar_presenca_acumulada(self):
        """Atualiza o contador de presenças na matrícula"""
        matricula = self.matricula
        total_presente = matricula.presencas.filter(status='Presente').count()
        matricula.presenca_acumulada = total_presente
        matricula.save()