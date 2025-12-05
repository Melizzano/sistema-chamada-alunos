from rest_framework import serializers
from .models import Professor, Aluno, Turma, Matricula, Presenca
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    """Serializer para o modelo User do Django"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
        read_only_fields = ['id', 'is_staff', 'date_joined']

class ProfessorSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Professor"""
    usuario = UserSerializer(read_only=True)
    total_turmas = serializers.IntegerField(source='turmas.count', read_only=True)
    
    class Meta:
        model = Professor
        fields = [
            'id', 'nome', 'email', 'departamento', 'ativo', 
            'data_cadastro', 'usuario', 'total_turmas'
        ]
        read_only_fields = ['id', 'data_cadastro']

class AlunoSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Aluno"""
    usuario = UserSerializer(read_only=True)
    idade = serializers.IntegerField(read_only=True)
    total_turmas = serializers.IntegerField(source='matriculas.count', read_only=True)
    
    class Meta:
        model = Aluno
        fields = [
            'id', 'nome', 'matricula', 'email', 'curso', 
            'data_nascimento', 'genero', 'data_cadastro', 
            'usuario', 'idade', 'total_turmas'
        ]
        read_only_fields = ['id', 'data_cadastro', 'idade']

class TurmaSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Turma"""
    professor_nome = serializers.CharField(source='professor.nome', read_only=True)
    professor_email = serializers.CharField(source='professor.email', read_only=True)
    representante_nome = serializers.CharField(source='representante.nome', read_only=True)
    total_alunos = serializers.IntegerField(source='matriculas.count', read_only=True)
    
    class Meta:
        model = Turma
        fields = [
            'id', 'nome', 'descricao', 'professor', 'professor_nome', 'professor_email',
            'data_inicio', 'data_fim', 'status', 'representante', 'representante_nome',
            'data_cadastro', 'total_alunos', 'esta_ativa'
        ]
        read_only_fields = ['id', 'data_cadastro', 'esta_ativa']

class MatriculaSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Matricula"""
    aluno_nome = serializers.CharField(source='aluno.nome', read_only=True)
    aluno_matricula = serializers.CharField(source='aluno.matricula', read_only=True)
    turma_nome = serializers.CharField(source='turma.nome', read_only=True)
    taxa_presenca = serializers.SerializerMethodField()
    
    class Meta:
        model = Matricula
        fields = [
            'id', 'turma', 'turma_nome', 'aluno', 'aluno_nome', 'aluno_matricula',
            'data_matricula', 'presenca_acumulada', 'taxa_presenca'
        ]
        read_only_fields = ['id', 'data_matricula']
    
    def get_taxa_presenca(self, obj):
        """Calcula a taxa de presença do aluno"""
        total_presencas = obj.presencas.count()
        if total_presencas > 0:
            return (obj.presenca_acumulada / total_presencas) * 100
        return 0

class PresencaSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Presenca"""
    aluno_nome = serializers.CharField(source='matricula.aluno.nome', read_only=True)
    aluno_matricula = serializers.CharField(source='matricula.aluno.matricula', read_only=True)
    turma_nome = serializers.CharField(source='matricula.turma.nome', read_only=True)
    
    class Meta:
        model = Presenca
        fields = [
            'id', 'matricula', 'aluno_nome', 'aluno_matricula', 'turma_nome',
            'data', 'status', 'observacao', 'data_registro'
        ]
        read_only_fields = ['id', 'data_registro']

# Serializers para relações aninhadas
class TurmaDetailSerializer(TurmaSerializer):
    """Serializer detalhado para Turma com alunos matriculados"""
    matriculas = MatriculaSerializer(many=True, read_only=True)
    professor = ProfessorSerializer(read_only=True)
    
    class Meta(TurmaSerializer.Meta):
        fields = TurmaSerializer.Meta.fields + ['matriculas', 'professor']

class ProfessorDetailSerializer(ProfessorSerializer):
    """Serializer detalhado para Professor com suas turmas"""
    turmas = TurmaSerializer(many=True, read_only=True)
    
    class Meta(ProfessorSerializer.Meta):
        fields = ProfessorSerializer.Meta.fields + ['turmas']

class AlunoDetailSerializer(AlunoSerializer):
    """Serializer detalhado para Aluno com suas matrículas"""
    matriculas = MatriculaSerializer(many=True, read_only=True)
    
    class Meta(AlunoSerializer.Meta):
        fields = AlunoSerializer.Meta.fields + ['matriculas']

# Serializers para estatísticas
class EstatisticaTurmaSerializer(serializers.Serializer):
    """Serializer para estatísticas de turma"""
    turma_id = serializers.IntegerField()
    turma_nome = serializers.CharField()
    total_alunos = serializers.IntegerField()
    presenca_media = serializers.FloatField()
    taxa_presente = serializers.FloatField()
    taxa_ausente = serializers.FloatField()
    taxa_justificado = serializers.FloatField()

class DashboardTurmaSerializer(serializers.Serializer):
    """Serializer para dashboard de turma"""
    turma = TurmaSerializer()
    professor = ProfessorSerializer()
    alunos = MatriculaSerializer(many=True)
    estatisticas = EstatisticaTurmaSerializer()

# ========== SERIALIZERS PARA AUTENTICAÇÃO ==========
# (Adicione estas classes no FINAL do arquivo)

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para registro de novos usuários"""
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, data):
        # Verificar se as senhas coincidem
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        
        # Verificar se o email já existe
        if User.objects.filter(email=data.get('email', '')).exists():
            raise serializers.ValidationError({"email": "Este email já está em uso."})
        
        # Verificar se o username já existe
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "Este nome de usuário já está em uso."})
        
        return data
    
    def create(self, validated_data):
        # Remover password2 dos dados validados
        validated_data.pop('password2')
        
        # Criar usuário
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

class LoginSerializer(serializers.Serializer):
    """Serializer para login de usuários"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            raise serializers.ValidationError("Usuário e senha são obrigatórios.")
        
        return data

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para alteração de senha"""
    old_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, required=True, min_length=8, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, min_length=8, style={'input_type': 'password'})
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"new_password": "As novas senhas não coincidem."})
        
        if data['old_password'] == data['new_password']:
            raise serializers.ValidationError({"new_password": "A nova senha deve ser diferente da senha atual."})
        
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para perfil do usuário"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("Este email já está em uso.")
        return value
    
    def validate_username(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("Este nome de usuário já está em uso.")
        return value