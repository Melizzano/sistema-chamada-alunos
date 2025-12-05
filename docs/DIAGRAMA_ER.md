# 📊 Diagrama Entidade-Relacionamento (ER)

## Modelo Lógico do Banco de Dados

```mermaid
erDiagram
    USER ||--o| PROFESSOR : "tem"
    USER ||--o| ALUNO : "tem"
    PROFESSOR ||--o{ TURMA : "leciona"
    TURMA }o--o{ ALUNO : "matriculado"
    TURMA ||--|| ALUNO : "representante"
    MATRICULA ||--|| PRESENCA : "registra"
    
    USER {
        int id PK
        string username
        string email
        string password
        boolean is_staff
        datetime date_joined
    }
    
    PROFESSOR {
        int id PK
        string nome
        string email UK
        string departamento
        boolean ativo
        datetime data_cadastro
        int usuario_id FK
    }
    
    ALUNO {
        int id PK
        string nome
        string matricula UK
        string email UK
        string curso
        date data_nascimento
        char genero
        datetime data_cadastro
        int usuario_id FK
    }
    
    TURMA {
        int id PK
        string nome
        text descricao
        date data_inicio
        date data_fim
        string status
        datetime data_cadastro
        int professor_id FK
        int representante_id FK
    }
    
    MATRICULA {
        int id PK
        datetime data_matricula
        int presenca_acumulada
        int turma_id FK
        int aluno_id FK
    }
    
    PRESENCA {
        int id PK
        date data
        string status
        text observacao
        datetime data_registro
        int matricula_id FK
    }