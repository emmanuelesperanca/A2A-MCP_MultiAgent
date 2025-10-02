"""Script para verificar a estrutura das tabelas no banco"""

import psycopg2
from core.config import config

def check_table_structure():
    """Verifica a estrutura da tabela knowledge_TECH"""
    try:
        # Conectar ao banco
        conn = psycopg2.connect(config.database.main_url)
        cursor = conn.cursor()
        
        print("📊 Verificando colunas da tabela knowledge_TECH:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'knowledge_TECH'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        if columns:
            for column_name, data_type, is_nullable in columns:
                print(f"  - {column_name}: {data_type} ({'NULL' if is_nullable == 'YES' else 'NOT NULL'})")
        else:
            print("  ❌ Tabela não encontrada")
        
        # Verificar se existe coluna com nome similar a 'embedding'
        print("\n🔍 Procurando colunas com nomes similares a 'embedding':")
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'knowledge_TECH'
            AND (column_name ILIKE '%embed%' OR column_name ILIKE '%vector%')
        """)
        
        embed_cols = cursor.fetchall()
        if embed_cols:
            for col_name, col_type in embed_cols:
                print(f"  ✅ {col_name}: {col_type}")
        else:
            print("  ❌ Nenhuma coluna de embedding encontrada")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("🔍 === VERIFICAÇÃO DE ESTRUTURA DA TABELA ===\n")
    check_table_structure()
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