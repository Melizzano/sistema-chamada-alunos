from django.http import JsonResponse
from django.views import View

class HomeView(View):
    """View para a página inicial da API"""
    
    def get(self, request):
        data = {
            'message': 'Bem-vindo à API do Sistema de Chamada de Alunos',
            'version': '1.0.0',
            'endpoints': {
                'admin': '/admin/',
                'api_root': '/api/',
                'documentation': {
                    'swagger': '/api/docs/',
                    'redoc': '/api/redoc/',
                    'schema': '/api/schema/'
                },
                'public_endpoints': {
                    'turmas_ativas': '/api/turmas-ativas/',
                    'professores_publicos': '/api/professores-publicos/',
                    'estatisticas': '/api/estatisticas/'
                }
            },
            'project': {
                'name': 'Sistema de Chamada de Alunos',
                'description': 'API para gerenciamento de chamadas de alunos - Projeto Integrador',
                'author': 'Melizzano',
                'github': 'https://github.com/Melizzano/sistema-chamada-alunos'
            }
        }
        return JsonResponse(data)