from django.contrib import admin
from .models import Professor, Aluno, Turma, Matricula, Presenca

@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'departamento', 'email', 'ativo', 'data_cadastro')
    list_filter = ('ativo', 'departamento', 'data_cadastro')
    search_fields = ('nome', 'email', 'departamento')
    ordering = ('nome',)

@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'matricula', 'curso', 'email', 'data_nascimento', 'genero')
    list_filter = ('curso', 'genero', 'data_cadastro')
    search_fields = ('nome', 'matricula', 'email', 'curso')
    ordering = ('nome',)

@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'professor', 'data_inicio', 'data_fim', 'status', 'representante')
    list_filter = ('status', 'data_inicio', 'data_fim', 'professor__departamento')
    search_fields = ('nome', 'descricao', 'professor__nome')
    ordering = ('-data_inicio', 'nome')
    
    # Para exibir o representante na lista
    def representante_nome(self, obj):
        return obj.representante.nome if obj.representante else "-"
    representante_nome.short_description = "Representante"

@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'turma', 'data_matricula', 'presenca_acumulada')
    list_filter = ('turma', 'data_matricula')
    search_fields = ('aluno__nome', 'aluno__matricula', 'turma__nome')
    ordering = ('-data_matricula',)

@admin.register(Presenca)
class PresencaAdmin(admin.ModelAdmin):
    list_display = ('aluno_nome', 'turma_nome', 'data', 'status', 'observacao')
    list_filter = ('status', 'data', 'matricula__turma')
    search_fields = ('matricula__aluno__nome', 'matricula__aluno__matricula')
    ordering = ('-data', 'matricula__aluno__nome')
    
    # Métodos para exibir informações relacionadas
    def aluno_nome(self, obj):
        return obj.matricula.aluno.nome
    aluno_nome.short_description = "Aluno"
    
    def turma_nome(self, obj):
        return obj.matricula.turma.nome
    turma_nome.short_description = "Turma"