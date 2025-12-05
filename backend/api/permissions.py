"""
Permissões personalizadas para o Sistema de Chamada de Alunos.
Define regras de acesso baseadas nos perfis: Admin, Professor, Aluno.
"""

from rest_framework import permissions
from .models import Professor, Aluno, Turma, Matricula


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permissão padrão:
    - Leitura: Qualquer usuário (autenticado ou não)
    - Escrita: Apenas administradores (is_staff=True)
    """
    def has_permission(self, request, view):
        # Métodos seguros (GET, HEAD, OPTIONS) permitidos para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Métodos de escrita apenas para administradores
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsAdminUser(permissions.BasePermission):
    """
    Acesso total apenas para administradores
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsProfessor(permissions.BasePermission):
    """
    Verifica se o usuário é um Professor
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'professor')
        )


class IsAluno(permissions.BasePermission):
    """
    Verifica se o usuário é um Aluno
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'aluno')
        )


class IsProfessorOrAdmin(permissions.BasePermission):
    """
    Permissão para Professores OU Administradores
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or hasattr(request.user, 'professor'))
        )
    
    def has_object_permission(self, request, view, obj):
        # Administradores têm acesso total
        if request.user.is_staff:
            return True
        
        # Professores só podem acessar seus próprios dados
        if hasattr(request.user, 'professor'):
            # Se o objeto for um Professor
            if isinstance(obj, Professor):
                return obj == request.user.professor
            
            # Se o objeto tiver relação com Professor
            if hasattr(obj, 'professor'):
                return obj.professor == request.user.professor
            
            # Se o objeto for uma Turma
            if isinstance(obj, Turma):
                return obj.professor == request.user.professor
            
            # Se o objeto for Matricula (acesso à turma do professor)
            if isinstance(obj, Matricula):
                return obj.turma.professor == request.user.professor
        
        return False


class IsAlunoOrAdmin(permissions.BasePermission):
    """
    Permissão para Alunos OU Administradores
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or hasattr(request.user, 'aluno'))
        )
    
    def has_object_permission(self, request, view, obj):
        # Administradores têm acesso total
        if request.user.is_staff:
            return True
        
        # Alunos só podem acessar seus próprios dados
        if hasattr(request.user, 'aluno'):
            # Se o objeto for um Aluno
            if isinstance(obj, Aluno):
                return obj == request.user.aluno
            
            # Se o objeto tiver relação com Aluno
            if hasattr(obj, 'aluno'):
                return obj.aluno == request.user.aluno
            
            # Se o objeto for Matricula do aluno
            if isinstance(obj, Matricula):
                return obj.aluno == request.user.aluno
        
        return False


class CanMarcarPresenca(permissions.BasePermission):
    """
    Permissão para marcar presenças:
    - Administradores: Podem marcar em qualquer turma
    - Professores: Apenas em suas próprias turmas
    """
    def has_permission(self, request, view):
        # Apenas usuários autenticados podem marcar presenças
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Se for administrador ou professor
        return request.user.is_staff or hasattr(request.user, 'professor')
    
    def has_object_permission(self, request, view, obj):
        # Métodos de leitura permitidos para professores do curso
        if request.method in permissions.SAFE_METHODS:
            if request.user.is_staff:
                return True
            if hasattr(request.user, 'professor'):
                # Verificar se o professor é dono da turma relacionada
                if hasattr(obj, 'matricula') and hasattr(obj.matricula, 'turma'):
                    return obj.matricula.turma.professor == request.user.professor
        
        # Métodos de escrita
        if request.user.is_staff:
            return True
        
        # Professor só pode marcar presença em suas turmas
        if hasattr(request.user, 'professor'):
            if hasattr(obj, 'matricula') and hasattr(obj.matricula, 'turma'):
                return obj.matricula.turma.professor == request.user.professor
        
        return False


class CanGerenciarTurma(permissions.BasePermission):
    """
    Permissão para gerenciar turmas:
    - Administradores: Podem fazer tudo
    - Professores: Apenas suas próprias turmas (exceto criação)
    """
    def has_permission(self, request, view):
        # Apenas usuários autenticados
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Método POST (criar) apenas para administradores
        if request.method == 'POST':
            return request.user.is_staff
        
        # Outros métodos para admin ou professor
        return request.user.is_staff or hasattr(request.user, 'professor')
    
    def has_object_permission(self, request, view, obj):
        # Administradores têm acesso total
        if request.user.is_staff:
            return True
        
        # Professores só podem gerenciar suas próprias turmas
        if hasattr(request.user, 'professor'):
            return obj.professor == request.user.professor
        
        return False


class CanVisualizarTurma(permissions.BasePermission):
    """
    Permissão para visualizar turmas:
    - Público: Listagem básica (sem dados sensíveis)
    - Autenticados: Dados completos de turmas relacionadas
    - Admin/Professor: Todos os dados
    """
    def has_permission(self, request, view):
        # Métodos GET sempre permitidos (lista pública)
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Outros métodos requerem autenticação
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Métodos de leitura
        if request.method in permissions.SAFE_METHODS:
            # Se for acesso público (sem autenticação)
            if not request.user or not request.user.is_authenticated:
                # Apenas dados básicos da turma
                return True
            
            # Usuários autenticados podem ver detalhes
            # 1. Administradores veem tudo
            if request.user.is_staff:
                return True
            
            # 2. Professores veem suas turmas
            if hasattr(request.user, 'professor'):
                return obj.professor == request.user.professor
            
            # 3. Alunos veem turmas onde estão matriculados
            if hasattr(request.user, 'aluno'):
                return Matricula.objects.filter(
                    turma=obj, 
                    aluno=request.user.aluno
                ).exists()
            
            # 4. Outros usuários autenticados veem dados básicos
            return True
        
        # Métodos de escrita (update, delete)
        # Apenas admin ou professor dono da turma
        if request.user.is_staff:
            return True
        
        if hasattr(request.user, 'professor'):
            return obj.professor == request.user.professor
        
        return False


class CanAcessarDashboard(permissions.BasePermission):
    """
    Permissão para acessar dashboard de turma:
    - Público: Apenas estatísticas gerais
    - Admin/Professor: Dashboard completo da turma
    - Aluno: Seu próprio desempenho na turma
    """
    def has_permission(self, request, view):
        # Acesso ao dashboard sempre permitido (dados agregados)
        return True
    
    def has_object_permission(self, request, view, obj):
        # Todos podem ver o dashboard básico
        return True


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão genérica: Dono do objeto OU Administrador
    """
    def has_object_permission(self, request, view, obj):
        # Administradores têm acesso total
        if request.user.is_staff:
            return True
        
        # Verificar se o usuário é dono do objeto
        # 1. Objeto tem atributo 'usuario'
        if hasattr(obj, 'usuario') and obj.usuario == request.user:
            return True
        
        # 2. Objeto tem atributo 'user'
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # 3. Objeto é um Professor
        if isinstance(obj, Professor) and hasattr(request.user, 'professor'):
            return obj == request.user.professor
        
        # 4. Objeto é um Aluno
        if isinstance(obj, Aluno) and hasattr(request.user, 'aluno'):
            return obj == request.user.aluno
        
        return False


class PublicReadOnly(permissions.BasePermission):
    """
    Permissão para endpoints públicos (apenas leitura)
    """
    def has_permission(self, request, view):
        # Apenas métodos de leitura são permitidos
        return request.method in permissions.SAFE_METHODS


# Permissões compostas (para uso em viewsets)
class ProfessorPermission(permissions.BasePermission):
    """
    Permissão para ações de professor
    """
    def has_permission(self, request, view):
        # Ações de listagem permitidas para todos
        if view.action in ['list', 'retrieve']:
            return True
        
        # Outras ações apenas para admin
        return request.user and request.user.is_authenticated and request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        # Visualização permitida para todos
        if view.action in ['retrieve']:
            return True
        
        # Modificação apenas para admin
        return request.user and request.user.is_staff


class AlunoPermission(permissions.BasePermission):
    """
    Permissão para ações de aluno
    """
    def has_permission(self, request, view):
        # Ações de listagem permitidas para todos (dados públicos)
        if view.action in ['list', 'retrieve']:
            return True
        
        # Criação apenas para admin
        if view.action == 'create':
            return request.user and request.user.is_authenticated and request.user.is_staff
        
        # Outras ações para admin ou aluno dono
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Visualização permitida para todos (dados públicos)
        if view.action == 'retrieve':
            return True
        
        # Modificação apenas para admin ou aluno dono
        if request.user.is_staff:
            return True
        
        if hasattr(request.user, 'aluno'):
            return obj == request.user.aluno
        
        return False