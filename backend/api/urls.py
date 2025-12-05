from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from . import views
from .views_auth import RegisterView, LoginView, LogoutView, ProfileView, ChangePasswordView

# Configurar router para viewsets
router = DefaultRouter()
router.register(r'professores', views.ProfessorViewSet)
router.register(r'alunos', views.AlunoViewSet)
router.register(r'turmas', views.TurmaViewSet)
router.register(r'matriculas', views.MatriculaViewSet)
router.register(r'presencas', views.PresencaViewSet)

urlpatterns = [
    # Rotas da API
    path('', include(router.urls)),
    
    # Autenticação
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/profile/', ProfileView.as_view(), name='profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Rotas públicas
    path('turmas-ativas/', views.TurmasAtivasView.as_view(), name='turmas-ativas'),
    path('professores-publicos/', views.ProfessoresPublicosView.as_view(), name='professores-publicos'),
    path('estatisticas/', views.EstatisticasView.as_view(), name='estatisticas'),
    
    # Documentação
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]