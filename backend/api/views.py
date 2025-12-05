"""
Views para a API do Sistema de Chamada de Alunos.
"""

# ========== IMPORTS ==========
from rest_framework import viewsets, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import date

from .models import Professor, Aluno, Turma, Matricula, Presenca
from .serializers import (
    ProfessorSerializer, AlunoSerializer, TurmaSerializer,
    MatriculaSerializer, PresencaSerializer,
    ProfessorDetailSerializer, AlunoDetailSerializer, TurmaDetailSerializer,
    DashboardTurmaSerializer
)
from .permissions import (
    IsAdminOrReadOnly, IsProfessorOrAdmin, IsAlunoOrAdmin, 
    CanMarcarPresenca, CanGerenciarTurma, CanVisualizarTurma,
    PublicReadOnly, IsOwnerOrAdmin
)


# ========== VIEWSETS PADRÃO ==========

class ProfessorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o modelo Professor.
    
    Permissões:
    - GET: Acesso público para listar e visualizar
    - POST/PUT/DELETE: Apenas administradores
    """
    
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['departamento', 'ativo']
    search_fields = ['nome', 'email', 'departamento']
    ordering_fields = ['nome', 'data_cadastro']
    ordering = ['nome']
    
    def get_permissions(self):
        """
        Define permissões baseadas na ação.
        """
        if self.action in ['list', 'retrieve']:
            # Listar e detalhar: acesso público
            permission_classes = [AllowAny]
        else:
            # Criar, atualizar, deletar: apenas admin
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """
        Retorna serializer diferente para detail view.
        """
        if self.action == 'retrieve':
            return ProfessorDetailSerializer
        return ProfessorSerializer
    
    @action(detail=True, methods=['get'])
    def turmas(self, request, pk=None):
        """
        Lista turmas de um professor específico.
        Endpoint: GET /api/professores/{id}/turmas/
        """
        professor = self.get_object()
        turmas = professor.turmas.all()
        serializer = TurmaSerializer(turmas, many=True)
        return Response(serializer.data)


class AlunoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o modelo Aluno.
    
    Permissões:
    - GET: Acesso público para listar e visualizar (dados limitados)
    - POST/PUT/DELETE: Apenas administradores
    - Presenças: Aluno dono ou administrador
    """
    
    queryset = Aluno.objects.all()
    serializer_class = AlunoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['curso', 'genero']
    search_fields = ['nome', 'matricula', 'email', 'curso']
    ordering_fields = ['nome', 'matricula', 'data_cadastro']
    ordering = ['nome']
    
    def get_permissions(self):
        """
        Define permissões baseadas na ação.
        """
        if self.action in ['list', 'retrieve']:
            # Listar e detalhar: acesso público (dados limitados)
            permission_classes = [AllowAny]
        elif self.action == 'presencas':
            # Presenças: aluno dono ou admin
            permission_classes = [IsAlunoOrAdmin]
        else:
            # Criar, atualizar, deletar: apenas admin
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """
        Retorna serializer diferente para detail view.
        """
        if self.action == 'retrieve':
            return AlunoDetailSerializer
        return AlunoSerializer
    
    @action(detail=True, methods=['get'], permission_classes=[IsAlunoOrAdmin])
    def presencas(self, request, pk=None):
        """
        Lista presenças de um aluno específico.
        Endpoint: GET /api/alunos/{id}/presencas/
        """
        aluno = self.get_object()
        matriculas = aluno.matriculas.all()
        
        # Coletar todas as presenças do aluno
        presencas = Presenca.objects.filter(matricula__in=matriculas)
        serializer = PresencaSerializer(presencas, many=True)
        return Response(serializer.data)


class TurmaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o modelo Turma.
    
    Permissões:
    - GET: Acesso público para listar, visualizar, dashboard
    - Relacionamentos: Acesso autenticado
    - Ações específicas: Professor da turma ou admin
    - POST/PUT/DELETE: Apenas administradores
    """
    
    queryset = Turma.objects.all()
    serializer_class = TurmaSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'professor']
    search_fields = ['nome', 'descricao', 'professor__nome']
    ordering_fields = ['nome', 'data_inicio', 'data_fim']
    ordering = ['-data_inicio']
    
    def get_permissions(self):
        """
        Define permissões baseadas na ação.
        """
        if self.action in ['list', 'retrieve', 'dashboard']:
            # Acesso público para listagem, detalhes e dashboard
            permission_classes = [AllowAny]
        elif self.action in ['alunos', 'representante']:
            # Alunos e representante: autenticados
            permission_classes = [IsAuthenticated]
        elif self.action in ['definir_representante', 'matricular_aluno']:
            # Ações específicas: professor da turma ou admin
            permission_classes = [IsProfessorOrAdmin]
        else:
            # Criar, atualizar, deletar: apenas admin
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """
        Retorna serializer diferente para detail view.
        """
        if self.action == 'retrieve':
            return TurmaDetailSerializer
        return TurmaSerializer
    
    # ========== ROTAS DE RELACIONAMENTO ==========
    
    @action(detail=True, methods=['get'])
    def alunos(self, request, pk=None):
        """
        Lista alunos matriculados na turma.
        Endpoint: GET /api/turmas/{id}/alunos/
        """
        turma = self.get_object()
        matriculas = turma.matriculas.all()
        serializer = MatriculaSerializer(matriculas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsProfessorOrAdmin])
    def matricular_aluno(self, request, pk=None):
        """
        Matricula um aluno na turma.
        Endpoint: POST /api/turmas/{id}/matricular-aluno/
        """
        turma = self.get_object()
        aluno_id = request.data.get('aluno_id')
        
        if not aluno_id:
            return Response(
                {'error': 'O ID do aluno é obrigatório'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            aluno = Aluno.objects.get(id=aluno_id)
        except Aluno.DoesNotExist:
            return Response(
                {'error': 'Aluno não encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar se já está matriculado
        if Matricula.objects.filter(turma=turma, aluno=aluno).exists():
            return Response(
                {'error': 'Aluno já matriculado nesta turma'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Criar matrícula
        matricula = Matricula.objects.create(turma=turma, aluno=aluno)
        serializer = MatriculaSerializer(matricula)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get', 'put'])
    def representante(self, request, pk=None):
        """
        Gerencia o aluno representante da turma.
        Endpoints: 
        - GET /api/turmas/{id}/representante/
        - PUT /api/turmas/{id}/representante/
        """
        turma = self.get_object()
        
        if request.method == 'GET':
            if turma.representante:
                serializer = AlunoSerializer(turma.representante)
                return Response(serializer.data)
            return Response({'message': 'Nenhum representante definido'})
        
        elif request.method == 'PUT':
            aluno_id = request.data.get('aluno_id')
            
            if not aluno_id:
                return Response(
                    {'error': 'O ID do aluno é obrigatório'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                aluno = Aluno.objects.get(id=aluno_id)
            except Aluno.DoesNotExist:
                return Response(
                    {'error': 'Aluno não encontrado'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verificar se o aluno está matriculado na turma
            if not Matricula.objects.filter(turma=turma, aluno=aluno).exists():
                return Response(
                    {'error': 'Aluno não está matriculado nesta turma'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Definir como representante
            turma.representante = aluno
            turma.save()
            
            serializer = AlunoSerializer(aluno)
            return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """
        Retorna dashboard completo da turma.
        Endpoint: GET /api/turmas/{id}/dashboard/
        """
        turma = self.get_object()
        
        # Dados da turma
        turma_serializer = TurmaSerializer(turma)
        
        # Dados do professor
        professor_serializer = ProfessorSerializer(turma.professor)
        
        # Alunos matriculados
        matriculas = turma.matriculas.all()
        alunos_serializer = MatriculaSerializer(matriculas, many=True)
        
        # Estatísticas
        total_alunos = matriculas.count()
        
        # Calcular presenças desta turma
        presencas_turma = Presenca.objects.filter(matricula__turma=turma)
        total_presencas = presencas_turma.count()
        
        if total_presencas > 0:
            presentes = presencas_turma.filter(status='Presente').count()
            taxa_presente = (presentes / total_presencas) * 100
            ausentes = presencas_turma.filter(status='Ausente').count()
            taxa_ausente = (ausentes / total_presencas) * 100
            justificados = presencas_turma.filter(status='Justificado').count()
            taxa_justificado = (justificados / total_presencas) * 100
        else:
            taxa_presente = 0
            taxa_ausente = 0
            taxa_justificado = 0
        
        estatisticas = {
            'turma_id': turma.id,
            'turma_nome': turma.nome,
            'total_alunos': total_alunos,
            'presenca_media': round(taxa_presente, 2),
            'taxa_presente': round(taxa_presente, 2),
            'taxa_ausente': round(taxa_ausente, 2),
            'taxa_justificado': round(taxa_justificado, 2),
        }
        
        data = {
            'turma': turma_serializer.data,
            'professor': professor_serializer.data,
            'alunos': alunos_serializer.data,
            'estatisticas': estatisticas
        }
        
        return Response(data)


class MatriculaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o modelo Matricula.
    
    Permissões:
    - GET: Acesso autenticado
    - POST/PUT/DELETE: Apenas administradores
    """
    
    queryset = Matricula.objects.all()
    serializer_class = MatriculaSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['turma', 'aluno']
    ordering_fields = ['data_matricula']
    ordering = ['-data_matricula']
    
    def get_permissions(self):
        """
        Define permissões baseadas na ação.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class PresencaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o modelo Presenca.
    
    Permissões:
    - GET: Acesso autenticado
    - POST/PUT: Professor da turma ou administrador
    - DELETE: Apenas administradores
    """
    
    queryset = Presenca.objects.all()
    serializer_class = PresencaSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['matricula', 'data', 'status']
    ordering_fields = ['data', 'data_registro']
    ordering = ['-data']
    
    def get_permissions(self):
        """
        Define permissões baseadas na ação.
        """
        if self.action == 'marcar_presenca':
            # Marcar presença: professor da turma ou admin
            permission_classes = [CanMarcarPresenca]
        elif self.action in ['list', 'retrieve']:
            # Listar e visualizar: autenticados
            permission_classes = [IsAuthenticated]
        elif self.action in ['create', 'update', 'partial_update']:
            # Criar/editar: professor da turma ou admin
            permission_classes = [CanMarcarPresenca]
        else:
            # Deletar: apenas admin
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['post'], permission_classes=[CanMarcarPresenca])
    def marcar_presenca(self, request):
        """
        Marca presença para múltiplos alunos de uma vez.
        Endpoint: POST /api/presencas/marcar-presenca/
        """
        turma_id = request.data.get('turma_id')
        data_aula = request.data.get('data', date.today().isoformat())
        registros = request.data.get('registros', [])
        
        if not turma_id or not registros:
            return Response(
                {'error': 'turma_id e registros são obrigatórios'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            turma = Turma.objects.get(id=turma_id)
        except Turma.DoesNotExist:
            return Response(
                {'error': 'Turma não encontrada'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar se o professor tem permissão (se não for admin)
        if not request.user.is_staff and hasattr(request.user, 'professor'):
            if turma.professor != request.user.professor:
                return Response(
                    {'error': 'Você não tem permissão para marcar presença nesta turma'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        resultados = []
        for registro in registros:
            aluno_id = registro.get('aluno_id')
            status_presenca = registro.get('status', 'Presente')
            observacao = registro.get('observacao', '')
            
            try:
                matricula = Matricula.objects.get(turma=turma, aluno_id=aluno_id)
                
                presenca, created = Presenca.objects.update_or_create(
                    matricula=matricula,
                    data=data_aula,
                    defaults={
                        'status': status_presenca,
                        'observacao': observacao
                    }
                )
                
                resultados.append({
                    'aluno_id': aluno_id,
                    'status': 'sucesso',
                    'presenca_id': presenca.id,
                    'criado': created
                })
                
            except Matricula.DoesNotExist:
                resultados.append({
                    'aluno_id': aluno_id,
                    'status': 'erro',
                    'mensagem': 'Aluno não matriculado nesta turma'
                })
            except Exception as e:
                resultados.append({
                    'aluno_id': aluno_id,
                    'status': 'erro',
                    'mensagem': str(e)
                })
        
        return Response({'resultados': resultados})


# ========== VIEWS PARA ROTAS PÚBLICAS ==========

class TurmasAtivasView(ListAPIView):
    """
    Lista apenas turmas ativas (acesso público).
    Endpoint: GET /api/turmas-ativas/
    """
    
    queryset = Turma.objects.filter(status='Ativa')
    serializer_class = TurmaSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome', 'descricao']


class ProfessoresPublicosView(ListAPIView):
    """
    Lista professores (apenas nome e departamento - acesso público).
    Endpoint: GET /api/professores-publicos/
    """
    
    queryset = Professor.objects.filter(ativo=True)
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        """
        Serializer limitado para dados públicos.
        """
        class ProfessorPublicoSerializer(serializers.ModelSerializer):
            class Meta:
                model = Professor
                fields = ['id', 'nome', 'departamento']
        
        return ProfessorPublicoSerializer


class EstatisticasView(APIView):
    """
    Retorna estatísticas gerais do sistema.
    Endpoint: GET /api/estatisticas/
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        total_professores = Professor.objects.filter(ativo=True).count()
        total_alunos = Aluno.objects.count()
        total_turmas = Turma.objects.filter(status='Ativa').count()
        
        # Calcular taxa média de presença
        total_presencas = Presenca.objects.count()
        if total_presencas > 0:
            presencas_presente = Presenca.objects.filter(status='Presente').count()
            taxa_presenca_geral = (presencas_presente / total_presencas) * 100
        else:
            taxa_presenca_geral = 0
        
        # Turma com maior presença
        turmas_com_presenca = Turma.objects.annotate(
            total_presencas=Count('matriculas__presencas'),
            presentes=Count('matriculas__presencas', filter=Q(matriculas__presencas__status='Presente'))
        ).filter(total_presencas__gt=0)
        
        if turmas_com_presenca.exists():
            melhor_turma = turmas_com_presenca.annotate(
                taxa=Avg('presentes') / Avg('total_presencas') * 100
            ).order_by('-taxa').first()
            melhor_turma_nome = melhor_turma.nome
            melhor_turma_taxa = round(melhor_turma.taxa, 2) if melhor_turma.taxa else 0
        else:
            melhor_turma_nome = "Nenhuma"
            melhor_turma_taxa = 0
        
        data = {
            'total_professores': total_professores,
            'total_alunos': total_alunos,
            'total_turmas_ativas': total_turmas,
            'taxa_presenca_geral': round(taxa_presenca_geral, 2),
            'melhor_turma': {
                'nome': melhor_turma_nome,
                'taxa_presenca': melhor_turma_taxa
            },
            'ultima_atualizacao': timezone.now()
        }
        
        return Response(data)