import os
from dotenv import load_dotenv

load_dotenv()

print("Variáveis de ambiente carregadas:")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')}")
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_PORT: {os.getenv('DB_PORT')}")

# Teste a conexão
import psycopg2

try:
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    print("\n✅ Conexão com PostgreSQL bem-sucedida!")
    
    # Verifique as databases existentes
    cursor = conn.cursor()
    cursor.execute("SELECT datname FROM pg_database;")
    databases = cursor.fetchall()
    print("\n📊 Databases disponíveis:")
    for db in databases:
        print(f"  - {db[0]}")
    
    conn.close()
    
except Exception as e:
    print(f"\n❌ Erro na conexão: {e}")
    print("\n📌 Soluções possíveis:")
    print("1. PostgreSQL está rodando? (services.msc)")
    print("2. Senha está correta? (Você definiu como 'admin')")
    print("3. Banco 'sistema_chamada' existe?")
    print("4. Usuário 'postgres' tem permissão?")