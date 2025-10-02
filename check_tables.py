import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    
    # Buscar todas as tabelas que começam com 'knowledge_'
    cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE 'knowledge_%'
    ORDER BY table_name;
    """)
    
    tables = cur.fetchall()
    print('Tabelas knowledge_ encontradas:')
    for table in tables:
        print(f'  "{table[0]}"')
    
    conn.close()
    
except Exception as e:
    print(f"Erro: {e}")