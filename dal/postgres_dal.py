"""
PostgreSQL Data Access Layer (DAL) - Implementação específica para PostgreSQL.

Esta classe implementa a interface BaseDAL para PostgreSQL com suporte a
extensões vetoriais (pgvector) e funcionalidades específicas do Postgres.
"""

import psycopg2
import psycopg2.extras
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from core.config import config
from .base_dal import BaseDAL, DALException, SearchResult, ConnectionInfo, ConnectionStatus


class PostgresDAL(BaseDAL):
    """
    Implementação da DAL para PostgreSQL com suporte a busca vetorial.
    
    Características:
    - Suporte completo ao pgvector para busca por similaridade
    - Connection pooling e gerenciamento automático de conexões
    - Tratamento robusto de erros e reconexão automática
    - Logging detalhado para debugging
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Inicializa a DAL PostgreSQL.
        
        Args:
            connection_string: String de conexão. Se None, usa configuração padrão
        """
        connection_string = connection_string or config.database.main_url
        super().__init__(connection_string)
        self._connection = None
        self._cursor = None
        self.logger = config.get_logger("PostgresDAL")
        
    def connect(self) -> bool:
        """Estabelece conexão com PostgreSQL."""
        try:
            if self._connection and not self._connection.closed:
                return True
                
            self.logger.info("🔌 Estabelecendo conexão com PostgreSQL...")
            
            # Parse da URL de conexão para logging (sem senha)
            parsed_url = urlparse(self.connection_string)
            safe_url = f"{parsed_url.hostname}:{parsed_url.port}/{parsed_url.path.lstrip('/')}"
            self.logger.info(f"📡 Conectando em: {safe_url}")
            
            self._connection = psycopg2.connect(
                self.connection_string,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            
            # Configurações de performance e comportamento
            self._connection.autocommit = True
            self._cursor = self._connection.cursor()
            
            self.logger.info("✅ Conexão PostgreSQL estabelecida com sucesso")
            return True
            
        except psycopg2.Error as e:
            self.logger.error(f"❌ Erro ao conectar PostgreSQL: {e}")
            raise DALException(f"Falha na conexão PostgreSQL: {e}", e)
        except Exception as e:
            self.logger.error(f"❌ Erro inesperado na conexão: {e}")
            raise DALException(f"Erro inesperado: {e}", e)
    
    def disconnect(self) -> bool:
        """Encerra a conexão com PostgreSQL."""
        try:
            if self._cursor:
                self._cursor.close()
                self._cursor = None
                
            if self._connection and not self._connection.closed:
                self._connection.close()
                self._connection = None
                
            self.logger.info("🔌 Conexão PostgreSQL encerrada")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao desconectar: {e}")
            return False
    
    def test_connection(self) -> ConnectionInfo:
        """Testa a conexão e retorna informações detalhadas."""
        try:
            if not self._connection or self._connection.closed:
                if not self.connect():
                    return ConnectionInfo(
                        status=ConnectionStatus.ERROR,
                        error_message="Não foi possível estabelecer conexão"
                    )
            
            # Obter informações do banco
            self._cursor.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()")
            db_info = self._cursor.fetchone()
            
            # Verificar extensões instaladas
            self._cursor.execute("""
                SELECT extname FROM pg_extension 
                WHERE extname IN ('vector', 'pgvector', 'uuid-ossp', 'btree_gin')
                ORDER BY extname
            """)
            extensions = [row['extname'] for row in self._cursor.fetchall()]
            
            parsed_url = urlparse(self.connection_string)
            
            return ConnectionInfo(
                status=ConnectionStatus.CONNECTED,
                database_name=db_info['current_database'],
                host=db_info['inet_server_addr'] or parsed_url.hostname,
                port=db_info['inet_server_port'] or parsed_url.port,
                extensions=extensions
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erro no teste de conexão: {e}")
            return ConnectionInfo(
                status=ConnectionStatus.ERROR,
                error_message=str(e)
            )
    
    def search_vectors(
        self,
        table_name: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        similarity_threshold: Optional[float] = None
    ) -> SearchResult:
        """
        Realiza busca por similaridade vetorial usando pgvector.
        
        Args:
            table_name: Nome da tabela (será quoted automaticamente)
            query_vector: Vetor de consulta (embedding)
            limit: Número máximo de resultados
            filters: Filtros adicionais (WHERE clauses)
            similarity_threshold: Threshold mínimo de similaridade coseno
            
        Returns:
            SearchResult com documentos e metadados da busca
        """
        start_time = time.time()
        
        try:
            if not self._connection or self._connection.closed:
                self.connect()
            
            # Construir query com segurança (quoted table name)
            quoted_table = f'"{table_name}"'
            
            # Query base para busca por similaridade coseno
            query = f"""
                SELECT *,
                       conteudo_original AS conteudo,
                       1 - (vetor <=> %s::vector) as similarity_score
                FROM {quoted_table}
            """
            
            params = [query_vector]
            
            # Adicionar filtros se fornecidos
            where_clauses = []
            
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        placeholders = ','.join(['%s'] * len(value))
                        where_clauses.append(f"{key} IN ({placeholders})")
                        params.extend(value)
                    else:
                        where_clauses.append(f"{key} = %s")
                        params.append(value)
            
            # Adicionar threshold de similaridade se fornecido
            if similarity_threshold:
                where_clauses.append("(1 - (vetor <=> %s::vector)) >= %s")
                params.extend([query_vector, similarity_threshold])
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Ordenar por similaridade e limitar resultados
            query += " ORDER BY similarity_score DESC LIMIT %s"
            params.append(limit)
            
            self.logger.debug(f"🔍 Executando busca vetorial em {table_name} (limit={limit})")
            
            # Executar query
            self._cursor.execute(query, params)
            results = self._cursor.fetchall()
            
            # Converter para lista de dicionários
            documents = [dict(row) for row in results]
            similarity_scores = [doc.pop('similarity_score', 0.0) for doc in documents]
            
            execution_time = (time.time() - start_time) * 1000  # em ms
            
            self.logger.debug(f"✅ Busca concluída: {len(documents)} documentos em {execution_time:.1f}ms")
            
            return SearchResult(
                documents=documents,
                total_count=len(documents),
                execution_time_ms=execution_time,
                similarity_scores=similarity_scores,
                metadata={
                    'table_name': table_name,
                    'query_vector_dim': len(query_vector),
                    'filters_applied': filters or {},
                    'similarity_threshold': similarity_threshold
                }
            )
            
        except psycopg2.Error as e:
            self.logger.error(f"❌ Erro PostgreSQL na busca vetorial: {e}")
            raise DALException(f"Erro na busca vetorial: {e}", e)
        except Exception as e:
            self.logger.error(f"❌ Erro inesperado na busca: {e}")
            raise DALException(f"Erro inesperado na busca: {e}", e)
    
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Executa uma consulta SQL customizada."""
        try:
            if not self._connection or self._connection.closed:
                self.connect()
            
            self.logger.debug(f"🔍 Executando query customizada: {query[:100]}...")
            
            if parameters:
                self._cursor.execute(query, parameters)
            else:
                self._cursor.execute(query)
            
            # Tentar fazer fetch (pode não haver resultados para INSERT/UPDATE/DELETE)
            try:
                results = self._cursor.fetchall()
                return [dict(row) for row in results]
            except psycopg2.ProgrammingError:
                # Query não retorna resultados (INSERT, UPDATE, DELETE, etc.)
                return []
                
        except psycopg2.Error as e:
            self.logger.error(f"❌ Erro PostgreSQL na query: {e}")
            raise DALException(f"Erro na execução da query: {e}", e)
        except Exception as e:
            self.logger.error(f"❌ Erro inesperado na query: {e}")
            raise DALException(f"Erro inesperado na query: {e}", e)
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Obtém informações detalhadas sobre uma tabela."""
        try:
            # Informações básicas da tabela
            table_query = """
                SELECT schemaname, tablename, tableowner, tablespace
                FROM pg_tables 
                WHERE tablename = %s
            """
            
            # Informações das colunas
            columns_query = """
                SELECT column_name, data_type, is_nullable, column_default,
                       character_maximum_length, numeric_precision, numeric_scale
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """
            
            # Informações dos índices
            indexes_query = """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = %s
            """
            
            self._cursor.execute(table_query, [table_name])
            table_info = self._cursor.fetchone()
            
            if not table_info:
                raise DALException(f"Tabela '{table_name}' não encontrada")
            
            self._cursor.execute(columns_query, [table_name])
            columns = [dict(row) for row in self._cursor.fetchall()]
            
            self._cursor.execute(indexes_query, [table_name])
            indexes = [dict(row) for row in self._cursor.fetchall()]
            
            return {
                'table_info': dict(table_info),
                'columns': columns,
                'indexes': indexes
            }
            
        except DALException:
            raise
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter informações da tabela {table_name}: {e}")
            raise DALException(f"Erro ao obter informações da tabela: {e}", e)
    
    def list_tables(self) -> List[str]:
        """Lista todas as tabelas do banco atual."""
        try:
            query = """
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """
            
            self._cursor.execute(query)
            results = self._cursor.fetchall()
            
            return [row['tablename'] for row in results]
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao listar tabelas: {e}")
            raise DALException(f"Erro ao listar tabelas: {e}", e)
    
    def similarity_search(self, table_name: str, embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Método de compatibilidade com a interface anterior.
        
        Este método mantém compatibilidade com o código existente que usa
        o postgres_vector_store.py original.
        """
        result = self.search_vectors(table_name, embedding, limit)
        
        # Adicionar similarity_score de volta aos documentos para compatibilidade
        for i, doc in enumerate(result.documents):
            if i < len(result.similarity_scores):
                doc['similarity_score'] = result.similarity_scores[i]
        
        return result.documents