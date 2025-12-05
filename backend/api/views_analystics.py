"""
Views para análises estatísticas e dashboards.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework import status
from django.db.models import Count, Avg, Q, F, Sum, Case, When, Value, FloatField
from django.db.models.functions import TruncMonth, TruncWeek, ExtractWeekDay
from django.utils import timezone
from datetime import datetime, timedelta, date
import statistics

from .models import Professor, Aluno, Turma, Matricula, Presenca
from .serializers import (
    ProfessorSerializer, AlunoSerializer, TurmaSerializer,
    MatriculaSerializer, PresencaSerializer
)


class DashboardProfessorView(APIView):
    """
    Dashboard específico para professor.
    Endpoint: GET /api/analytics/professor/{id}/dashboard/
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, professor_id=None):
        try:
            if professor_id:
                professor = Professor.objects.get(id=professor_id)
            elif hasattr(request.user, 'professor'):
                professor = request.user.professor
            else:
                return Response(
                    {'error': 'Professor não encontrado ou usuário não é professor'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verificar permissão (admin ou professor dono)
            if not request.user.is_staff and not hasattr(request.user, 'professor'):
                return Response(
                    {'error': 'Permissão negada'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if hasattr(request.user, 'professor') and request.user.professor != professor:
                return Response(
                    {'error': 'Você só pode acessar seu próprio dashboard'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Turmas do professor
            turmas = professor.turmas.all()
            
            # Estatísticas gerais
            total_turmas = turmas.count()
            turmas_ativas = turmas.filter(status='Ativa').count()
            turmas_concluidas = turmas.filter(status='Concluída').count()
            
            # Total de alunos em todas as turmas
            total_alunos = Matricula.objects.filter(turma__in=turmas).count()
            
            # Calcular presenças nas turmas do professor
            presencas_turmas = Presenca.objects.filter(matricula__turma__in=turmas)
            total_presencas = presencas_turmas.count()
            
            if total_presencas > 0:
                presentes = presencas_turmas.filter(status='Presente').count()
                taxa_presenca_geral = (presentes / total_presencas) * 100
            else:
                taxa_presenca_geral = 0
            
            # Turmas com melhor/maior presença
            turmas_com_estatisticas = []
            for turma in turmas:
                matriculas_turma = turma.matriculas.all()
                presencas_turma = Presenca.objects.filter(matricula__turma=turma)
                total_presencas_turma = presencas_turma.count()
                
                if total_presencas_turma > 0:
                    presentes_turma = presencas_turma.filter(status='Presente').count()
                    taxa_presenca_turma = (presentes_turma / total_presencas_turma) * 100
                else:
                    taxa_presenca_turma = 0
                
                turmas_com_estatisticas.append({
                    'id': turma.id,
                    'nome': turma.nome,
                    'status': turma.status,
                    'total_alunos': matriculas_turma.count(),
                    'taxa_presenca': round(taxa_presenca_turma, 2),
                    'data_inicio': turma.data_inicio,
                    'data_fim': turma.data_fim
                })
            
            # Ordenar turmas por taxa de presença (decrescente)
            turmas_com_estatisticas.sort(key=lambda x: x['taxa_presenca'], reverse=True)
            
            # Presenças por dia da semana (últimos 30 dias)
            data_30_dias_atras = timezone.now().date() - timedelta(days=30)
            presencas_30_dias = Presenca.objects.filter(
                matricula__turma__in=turmas,
                data__gte=data_30_dias_atras
            ).annotate(
                dia_semana=ExtractWeekDay('data')
            ).values('dia_semana').annotate(
                total=Count('id'),
                presentes=Count('id', filter=Q(status='Presente'))
            ).order_by('dia_semana')
            
            dias_semana_map = {
                1: 'Domingo',
                2: 'Segunda',
                3: 'Terça',
                4: 'Quarta',
                5: 'Quinta',
                6: 'Sexta',
                7: 'Sábado'
            }
            
            presencas_por_dia = []
            for item in presencas_30_dias:
                if item['total'] > 0:
                    taxa = (item['presentes'] / item['total']) * 100
                else:
                    taxa = 0
                
                presencas_por_dia.append({
                    'dia': dias_semana_map.get(item['dia_semana'], 'Desconhecido'),
                    'total_aulas': item['total'],
                    'taxa_presenca': round(taxa, 2)
                })
            
            # Alunos com maior número de faltas
            alunos_com_faltas = []
            matriculas_professor = Matricula.objects.filter(turma__in=turmas)
            
            for matricula in matriculas_professor[:10]:  # Top 10
                presencas_aluno = Presenca.objects.filter(matricula=matricula)
                total_presencas_aluno = presencas_aluno.count()
                
                if total_presencas_aluno > 0:
                    ausentes = presencas_aluno.filter(status='Ausente').count()
                    taxa_ausencia = (ausentes / total_presencas_aluno) * 100
                else:
                    taxa_ausencia = 0
                
                alunos_com_faltas.append({
                    'aluno_id': matricula.aluno.id,
                    'aluno_nome': matricula.aluno.nome,
                    'turma': matricula.turma.nome,
                    'total_aulas': total_presencas_aluno,
                    'faltas': ausentes if 'ausentes' in locals() else 0,
                    'taxa_ausencia': round(taxa_ausencia, 2)
                })
            
            # Ordenar por taxa de ausência (decrescente)
            alunos_com_faltas.sort(key=lambda x: x['taxa_ausencia'], reverse=True)
            
            data = {
                'professor': {
                    'id': professor.id,
                    'nome': professor.nome,
                    'departamento': professor.departamento,
                    'email': professor.email
                },
                'estatisticas_gerais': {
                    'total_turmas': total_turmas,
                    'turmas_ativas': turmas_ativas,
                    'turmas_concluidas': turmas_concluidas,
                    'total_alunos': total_alunos,
                    'taxa_presenca_geral': round(taxa_presenca_geral, 2)
                },
                'turmas': turmas_com_estatisticas[:5],  # Top 5 turmas
                'presencas_por_dia_semana': presencas_por_dia,
                'alunos_com_mais_faltas': alunos_com_faltas[:5],  # Top 5 alunos
                'periodo_analise': {
                    'inicio': data_30_dias_atras.isoformat(),
                    'fim': timezone.now().date().isoformat()
                }
            }
            
            return Response(data)
            
        except Professor.DoesNotExist:
            return Response(
                {'error': 'Professor não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )


class DashboardAlunoView(APIView):
    """
    Dashboard específico para aluno.
    Endpoint: GET /api/analytics/aluno/{id}/dashboard/
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, aluno_id=None):
        try:
            if aluno_id:
                aluno = Aluno.objects.get(id=aluno_id)
            elif hasattr(request.user, 'aluno'):
                aluno = request.user.aluno
            else:
                return Response(
                    {'error': 'Aluno não encontrado ou usuário não é aluno'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verificar permissão (admin ou aluno dono)
            if not request.user.is_staff and not hasattr(request.user, 'aluno'):
                return Response(
                    {'error': 'Permissão negada'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if hasattr(request.user, 'aluno') and request.user.aluno != aluno:
                return Response(
                    {'error': 'Você só pode acessar seu próprio dashboard'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Matrículas do aluno
            matriculas = aluno.matriculas.all()
            turmas_ids = matriculas.values_list('turma_id', flat=True)
            
            # Estatísticas gerais
            total_turmas = matriculas.count()
            turmas_ativas = Turma.objects.filter(
                id__in=turmas_ids,
                status='Ativa'
            ).count()
            
            # Calcular presenças do aluno
            presencas_aluno = Presenca.objects.filter(matricula__aluno=aluno)
            total_presencas = presencas_aluno.count()
            
            if total_presencas > 0:
                presentes = presencas_aluno.filter(status='Presente').count()
                ausentes = presencas_aluno.filter(status='Ausente').count()
                justificados = presencas_aluno.filter(status='Justificado').count()
                
                taxa_presenca = (presentes / total_presencas) * 100
                taxa_ausencia = (ausentes / total_presencas) * 100
                taxa_justificados = (justificados / total_presencas) * 100
            else:
                taxa_presenca = 0
                taxa_ausencia = 0
                taxa_justificados = 0
            
            # Desempenho por turma
            desempenho_por_turma = []
            for matricula in matriculas:
                turma = matricula.turma
                presencas_turma = Presenca.objects.filter(matricula=matricula)
                total_presencas_turma = presencas_turma.count()
                
                if total_presencas_turma > 0:
                    presentes_turma = presencas_turma.filter(status='Presente').count()
                    taxa_presenca_turma = (presentes_turma / total_presencas_turma) * 100
                else:
                    taxa_presenca_turma = 0
                
                # Comparar com média da turma
                todas_matriculas_turma = turma.matriculas.all()
                taxa_presenca_turma_geral = 0
                if todas_matriculas_turma.count() > 0:
                    total_presencas_geral = Presenca.objects.filter(
                        matricula__turma=turma
                    ).count()
                    
                    if total_presencas_geral > 0:
                        presentes_geral = Presenca.objects.filter(
                            matricula__turma=turma,
                            status='Presente'
                        ).count()
                        taxa_presenca_turma_geral = (presentes_geral / total_presencas_geral) * 100
                
                desempenho_por_turma.append({
                    'turma_id': turma.id,
                    'turma_nome': turma.nome,
                    'professor': turma.professor.nome,
                    'status': turma.status,
                    'minha_presenca': round(taxa_presenca_turma, 2),
                    'media_turma': round(taxa_presenca_turma_geral, 2),
                    'diferenca': round(taxa_presenca_turma - taxa_presenca_turma_geral, 2),
                    'presenca_acumulada': matricula.presenca_acumulada
                })
            
            # Presenças por mês (últimos 6 meses)
            data_6_meses_atras = timezone.now().date() - timedelta(days=180)
            presencas_6_meses = Presenca.objects.filter(
                matricula__aluno=aluno,
                data__gte=data_6_meses_atras
            ).annotate(
                mes=TruncMonth('data')
            ).values('mes').annotate(
                total=Count('id'),
                presentes=Count('id', filter=Q(status='Presente'))
            ).order_by('mes')
            
            presencas_por_mes = []
            for item in presencas_6_meses:
                if item['total'] > 0:
                    taxa = (item['presentes'] / item['total']) * 100
                else:
                    taxa = 0
                
                presencas_por_mes.append({
                    'mes': item['mes'].strftime('%Y-%m'),
                    'total_aulas': item['total'],
                    'presencas': item['presentes'],
                    'taxa_presenca': round(taxa, 2)
                })
            
            # Próximas aulas (próximos 7 dias)
            hoje = timezone.now().date()
            proxima_semana = hoje + timedelta(days=7)
            
            turmas_ativas_aluno = Turma.objects.filter(
                id__in=turmas_ids,
                status='Ativa',
                data_fim__gte=hoje
            )
            
            # Dias da semana com aula (simulação - na prática viria de um modelo de horário)
            # Aqui estamos assumindo que há aulas de segunda a sexta
            dias_com_aula = []
            for i in range(7):
                data_aula = hoje + timedelta(days=i)
                # Simulação: aulas apenas de segunda a sexta
                if data_aula.weekday() < 5:  # 0=segunda, 4=sexta
                    for turma in turmas_ativas_aluno:
                        dias_com_aula.append({
                            'data': data_aula.isoformat(),
                            'dia_semana': ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][data_aula.weekday()],
                            'turma': turma.nome,
                            'professor': turma.professor.nome
                        })
            
            data = {
                'aluno': {
                    'id': aluno.id,
                    'nome': aluno.nome,
                    'matricula': aluno.matricula,
                    'curso': aluno.curso,
                    'idade': aluno.idade()
                },
                'estatisticas_gerais': {
                    'total_turmas': total_turmas,
                    'turmas_ativas': turmas_ativas,
                    'total_aulas': total_presencas,
                    'presencas': presentes if 'presentes' in locals() else 0,
                    'ausencias': ausentes if 'ausentes' in locals() else 0,
                    'justificados': justificados if 'justificados' in locals() else 0,
                    'taxa_presenca': round(taxa_presenca, 2),
                    'taxa_ausencia': round(taxa_ausencia, 2),
                    'taxa_justificados': round(taxa_justificados, 2)
                },
                'desempenho_por_turma': desempenho_por_turma,
                'evolucao_mensal': presencas_por_mes,
                'proximas_aulas': dias_com_aula[:5],  # Próximas 5 aulas
                'recomendacoes': self.gerar_recomendacoes(taxa_presenca, desempenho_por_turma)
            }
            
            return Response(data)
            
        except Aluno.DoesNotExist:
            return Response(
                {'error': 'Aluno não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def gerar_recomendacoes(self, taxa_presenca, desempenho_por_turma):
        """Gera recomendações personalizadas para o aluno."""
        recomendacoes = []
        
        if taxa_presenca < 75:
            recomendacoes.append({
                'tipo': 'alta_prioridade',
                'mensagem': 'Sua taxa de presença está abaixo de 75%. É importante melhorar sua frequência.',
                'acao': 'Tente não faltar às próximas aulas.'
            })
        
        for turma in desempenho_por_turma:
            if turma['diferenca'] < -10:
                recomendacoes.append({
                    'tipo': 'media_prioridade',
                    'mensagem': f'Sua presença em {turma["turma_nome"]} está {abs(turma["diferenca"]):.1f}% abaixo da média da turma.',
                    'acao': f'Converse com o professor {turma["professor"]} sobre como melhorar.'
                })
        
        if not recomendacoes:
            recomendacoes.append({
                'tipo': 'baixa_prioridade',
                'mensagem': 'Seu desempenho está bom! Continue assim.',
                'acao': 'Mantenha a frequência e o bom trabalho.'
            })
        
        return recomendacoes


class AnalyticsGeralView(APIView):
    """
    Análises gerais para administradores.
    Endpoint: GET /api/analytics/geral/
    """
    
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Período para análise (último mês)
        data_30_dias_atras = timezone.now().date() - timedelta(days=30)
        
        # Estatísticas básicas
        total_professores = Professor.objects.filter(ativo=True).count()
        total_alunos = Aluno.objects.count()
        total_turmas = Turma.objects.filter(status='Ativa').count()
        total_matriculas = Matricula.objects.count()
        
        # Taxa de presença geral
        total_presencas = Presenca.objects.count()
        if total_presencas > 0:
            presentes = Presenca.objects.filter(status='Presente').count()
            taxa_presenca_geral = (presentes / total_presencas) * 100
        else:
            taxa_presenca_geral = 0
        
        # Evolução de matrículas (últimos 6 meses)
        data_6_meses_atras = timezone.now().date() - timedelta(days=180)
        matriculas_por_mes = Matricula.objects.filter(
            data_matricula__gte=data_6_meses_atras
        ).annotate(
            mes=TruncMonth('data_matricula')
        ).values('mes').annotate(
            total=Count('id')
        ).order_by('mes')
        
        # Presenças por departamento
        presencas_por_departamento = Professor.objects.values('departamento').annotate(
            total_turmas=Count('turmas'),
            total_alunos=Count('turmas__matriculas'),
            total_presencas=Count('turmas__matriculas__presencas'),
            presentes=Count('turmas__matriculas__presencas', filter=Q(turmas__matriculas__presencas__status='Presente'))
        )
        
        departamentos_com_taxa = []
        for depto in presencas_por_departamento:
            if depto['total_presencas'] > 0:
                taxa = (depto['presentes'] / depto['total_presencas']) * 100
            else:
                taxa = 0
            
            departamentos_com_taxa.append({
                'departamento': depto['departamento'],
                'total_turmas': depto['total_turmas'],
                'total_alunos': depto['total_alunos'],
                'taxa_presenca': round(taxa, 2)
            })
        
        # Turmas com maior evasão (taxa de presença < 70%)
        turmas_com_baixa_presenca = []
        for turma in Turma.objects.filter(status='Ativa'):
            presencas_turma = Presenca.objects.filter(matricula__turma=turma)
            total_presencas_turma = presencas_turma.count()
            
            if total_presencas_turma > 0:
                presentes_turma = presencas_turma.filter(status='Presente').count()
                taxa_presenca_turma = (presentes_turma / total_presencas_turma) * 100
                
                if taxa_presenca_turma < 70:
                    turmas_com_baixa_presenca.append({
                        'turma_id': turma.id,
                        'turma_nome': turma.nome,
                        'professor': turma.professor.nome,
                        'total_alunos': turma.matriculas.count(),
                        'taxa_presenca': round(taxa_presenca_turma, 2)
                    })
        
        # Ordenar por taxa de presença (crescente)
        turmas_com_baixa_presenca.sort(key=lambda x: x['taxa_presenca'])
        
        # Alunos com maior número de faltas
        alunos_com_faltas = []
        for aluno in Aluno.objects.all()[:20]:  # Analisar os 20 primeiros
            presencas_aluno = Presenca.objects.filter(matricula__aluno=aluno)
            total_presencas_aluno = presencas_aluno.count()
            
            if total_presencas_aluno > 0:
                ausentes = presencas_aluno.filter(status='Ausente').count()
                taxa_ausencia = (ausentes / total_presencas_aluno) * 100
                
                if taxa_ausencia > 30:  # Mais de 30% de faltas
                    alunos_com_faltas.append({
                        'aluno_id': aluno.id,
                        'aluno_nome': aluno.nome,
                        'matricula': aluno.matricula,
                        'curso': aluno.curso,
                        'total_aulas': total_presencas_aluno,
                        'faltas': ausentes,
                        'taxa_ausencia': round(taxa_ausencia, 2)
                    })
        
        # Ordenar por taxa de ausência (decrescente)
        alunos_com_faltas.sort(key=lambda x: x['taxa_ausencia'], reverse=True)
        
        data = {
            'estatisticas_gerais': {
                'total_professores': total_professores,
                'total_alunos': total_alunos,
                'total_turmas_ativas': total_turmas,
                'total_matriculas': total_matriculas,
                'taxa_presenca_geral': round(taxa_presenca_geral, 2),
                'periodo_analise': {
                    'inicio': data_30_dias_atras.isoformat(),
                    'fim': timezone.now().date().isoformat()
                }
            },
            'evolucao_matriculas': [
                {
                    'mes': item['mes'].strftime('%Y-%m'),
                    'total': item['total']
                }
                for item in matriculas_por_mes
            ],
            'desempenho_por_departamento': departamentos_com_taxa,
            'alertas': {
                'turmas_baixa_presenca': turmas_com_baixa_presenca[:5],  # Top 5
                'alunos_muitas_faltas': alunos_com_faltas[:10]  # Top 10
            },
            'recomendacoes_administrativas': self.gerar_recomendacoes_administrativas(
                taxa_presenca_geral, 
                turmas_com_baixa_presenca,
                alunos_com_faltas
            )
        }
        
        return Response(data)
    
    def gerar_recomendacoes_administrativas(self, taxa_presenca_geral, turmas_com_baixa_presenca, alunos_com_faltas):
        """Gera recomendações para a administração."""
        recomendacoes = []
        
        if taxa_presenca_geral < 80:
            recomendacoes.append({
                'prioridade': 'alta',
                'titulo': 'Taxa de presença geral baixa',
                'descricao': f'A taxa de presença geral está em {taxa_presenca_geral:.1f}%, abaixo dos 80% recomendados.',
                'acao': 'Implementar campanha de conscientização sobre frequência.'
            })
        
        if turmas_com_baixa_presenca:
            recomendacoes.append({
                'prioridade': 'alta',
                'titulo': 'Turmas com baixa presença',
                'descricao': f'Existem {len(turmas_com_baixa_presenca)} turmas com taxa de presença abaixo de 70%.',
                'acao': 'Reunir-se com os professores dessas turmas para identificar problemas.'
            })
        
        if alunos_com_faltas:
            recomendacoes.append({
                'prioridade': 'media',
                'titulo': 'Alunos com muitas faltas',
                'descricao': f'Existem {len(alunos_com_faltas)} alunos com mais de 30% de faltas.',
                'acao': 'Entrar em contato com esses alunos e seus coordenadores de curso.'
            })
        
        if taxa_presenca_geral > 90 and len(turmas_com_baixa_presenca) == 0:
            recomendacoes.append({
                'prioridade': 'baixa',
                'titulo': 'Desempenho excelente',
                'descricao': 'O sistema está com ótimos índices de presença.',
                'acao': 'Manter as políticas atuais e reconhecer os professores com melhor desempenho.'
            })
        
        return recomendacoes


class RelatorioPresencaView(APIView):
    """
    Gera relatório detalhado de presenças.
    Endpoint: POST /api/analytics/relatorio-presenca/
    """
    
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        # Parâmetros do relatório
        data_inicio = request.data.get('data_inicio')
        data_fim = request.data.get('data_fim')
        turma_id = request.data.get('turma_id')
        formato = request.data.get('formato', 'json')  # json, csv
        
        try:
            # Converter datas
            if data_inicio:
                data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            else:
                data_inicio = timezone.now().date() - timedelta(days=30)
            
            if data_fim:
                data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            else:
                data_fim = timezone.now().date()
            
            # Filtrar presenças
            filtros = Q(data__gte=data_inicio, data__lte=data_fim)
            
            if turma_id:
                filtros &= Q(matricula__turma_id=turma_id)
                turma = Turma.objects.get(id=turma_id)
                titulo_relatorio = f"Relatório de Presenças - {turma.nome}"
            else:
                titulo_relatorio = "Relatório Geral de Presenças"
            
            presencas = Presenca.objects.filter(filtros)
            
            # Agrupar por turma
            presencas_por_turma = presencas.values(
                'matricula__turma__id',
                'matricula__turma__nome',
                'matricula__turma__professor__nome'
            ).annotate(
                total=Count('id'),
                presentes=Count('id', filter=Q(status='Presente')),
                ausentes=Count('id', filter=Q(status='Ausente')),
                justificados=Count('id', filter=Q(status='Justificado'))
            ).order_by('matricula__turma__nome')
            
            # Calcular totais
            totais = {
                'total': presencas.count(),
                'presentes': presencas.filter(status='Presente').count(),
                'ausentes': presencas.filter(status='Ausente').count(),
                'justificados': presencas.filter(status='Justificado').count()
            }
            
            if totais['total'] > 0:
                totais['taxa_presenca'] = (totais['presentes'] / totais['total']) * 100
                totais['taxa_ausencia'] = (totais['ausentes'] / totais['total']) * 100
                totais['taxa_justificados'] = (totais['justificados'] / totais['total']) * 100
            else:
                totais['taxa_presenca'] = 0
                totais['taxa_ausencia'] = 0
                totais['taxa_justificados'] = 0
            
            # Formatar dados
            relatorio = {
                'titulo': titulo_relatorio,
                'periodo': {
                    'inicio': data_inicio.isoformat(),
                    'fim': data_fim.isoformat()
                },
                'parametros': {
                    'turma_id': turma_id,
                    'formato': formato
                },
                'totais': totais,
                'detalhes_por_turma': [
                    {
                        'turma_id': item['matricula__turma__id'],
                        'turma_nome': item['matricula__turma__nome'],
                        'professor': item['matricula__turma__professor__nome'],
                        'total': item['total'],
                        'presentes': item['presentes'],
                        'ausentes': item['ausentes'],
                        'justificados': item['justificados'],
                        'taxa_presenca': round((item['presentes'] / item['total'] * 100), 2) if item['total'] > 0 else 0
                    }
                    for item in presencas_por_turma
                ],
                'gerado_em': timezone.now().isoformat(),
                'gerado_por': request.user.username if request.user else 'Sistema'
            }
            
            return Response(relatorio)
            
        except Exception as e:
            return Response(
                {'error': f'Erro ao gerar relatório: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )