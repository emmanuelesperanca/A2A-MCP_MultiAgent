"""
PostgreSQL Data Access Layer - VERSÃO ASSÍNCRONA
Implementação assíncrona usando asyncpg para operações não-bloqueantes
"""

import asyncpg
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from core.config import config
from dal.base_dal import DALException, SearchResult, ConnectionInfo, ConnectionStatus


class PostgresDALAsync:
    """
    Implementação assíncrona da DAL para PostgreSQL com suporte a busca vetorial.
    
    Características:
    - Totalmente assíncrono usando asyncpg
    - Suporte completo ao pgvector para busca por similaridade
    - Connection pooling automático
    - Operações não-bloqueantes para máxima performance
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Inicializa a DAL PostgreSQL assíncrona.
        
        Args:
            connection_string: String de conexão. Se None, usa configuração padrão
        """
        self.connection_string = connection_string or config.database.main_url
        self._connection = None
        self._pool = None
        self.logger = config.get_logger("PostgresDALAsync")
        
    async def connect(self) -> bool:
        """Estabelece conexão assíncrona com PostgreSQL."""
        try:
            if self._connection and not self._connection.is_closed():
                return True
                
            self.logger.info("🔌 Estabelecendo conexão assíncrona com PostgreSQL...")
            
            # Parse da URL de conexão para logging (sem senha)
            parsed_url = urlparse(self.connection_string)
            safe_url = f"{parsed_url.hostname}:{parsed_url.port}/{parsed_url.path.lstrip('/')}"
            self.logger.info(f"📡 Conectando em (ASYNC): {safe_url}")
            
            # Criar conexão assíncrona com timeout de 10 segundos
            import asyncio
            self._connection = await asyncio.wait_for(
                asyncpg.connect(self.connection_string),
                timeout=10.0
            )
            
            self.logger.info("✅ Conexão PostgreSQL assíncrona estabelecida com sucesso")
            return True
            
        except asyncio.TimeoutError:
            self.logger.error(f"❌ Timeout ao conectar PostgreSQL (>10s) - Verifique conectividade de rede")
            raise DALException("Timeout na conexão com banco de dados (>10s). Verifique VPN/rede.", None)
        except asyncpg.PostgresError as e:
            self.logger.error(f"❌ Erro ao conectar PostgreSQL (ASYNC): {e}")
            raise DALException(f"Falha na conexão PostgreSQL: {e}", e)
        except Exception as e:
            self.logger.error(f"❌ Erro inesperado na conexão (ASYNC): {e}")
            raise DALException(f"Erro inesperado: {e}", e)
    
    async def disconnect(self) -> bool:
        """Encerra a conexão assíncrona com PostgreSQL."""
        try:
            if self._connection and not self._connection.is_closed():
                await self._connection.close()
                self._connection = None
                
            if self._pool:
                await self._pool.close()
                self._pool = None
                
            self.logger.info("🔌 Conexão PostgreSQL assíncrona encerrada")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao desconectar (ASYNC): {e}")
            return False
    
    async def test_connection(self) -> ConnectionInfo:
        """Testa a conexão de forma assíncrona e retorna informações detalhadas."""
        try:
            if not self._connection or self._connection.is_closed():
                if not await self.connect():
                    return ConnectionInfo(
                        status=ConnectionStatus.ERROR,
                        error_message="Não foi possível estabelecer conexão"
                    )
            
            # Obter informações do banco
            db_info = await self._connection.fetchrow(
                "SELECT current_database(), current_user, inet_server_addr(), inet_server_port()"
            )
            
            # Verificar extensões instaladas
            extensions = await self._connection.fetch("""
                SELECT extname FROM pg_extension 
                WHERE extname IN ('vector', 'pgvector', 'uuid-ossp', 'btree_gin')
                ORDER BY extname
            """)
            
            parsed_url = urlparse(self.connection_string)
            
            return ConnectionInfo(
                status=ConnectionStatus.CONNECTED,
                database_name=db_info['current_database'],
                host=db_info['inet_server_addr'] or parsed_url.hostname,
                port=db_info['inet_server_port'] or parsed_url.port,
                extensions=[ext['extname'] for ext in extensions]
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erro no teste de conexão (ASYNC): {e}")
            return ConnectionInfo(
                status=ConnectionStatus.ERROR,
                error_message=str(e)
            )
    
    async def search_vectors_async(
        self,
        table_name: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        similarity_threshold: Optional[float] = None
    ) -> SearchResult:
        """
        Realiza busca por similaridade vetorial de forma ASSÍNCRONA usando pgvector.
        
        Args:
            table_name: Nome da tabela
            query_vector: Vetor de consulta (embedding)
            limit: Número máximo de resultados
            filters: Filtros adicionais (WHERE clauses)
            similarity_threshold: Threshold mínimo de similaridade coseno
            
        Returns:
            SearchResult com documentos e metadados da busca
        """
        start_time = time.time()
        
        try:
            if not self._connection or self._connection.is_closed():
                await self.connect()
            
            # Construir query com segurança
            quoted_table = f'"{table_name}"'
            
            # Converter o vetor para string no formato correto do pgvector
            vector_str = '[' + ','.join(map(str, query_vector)) + ']'
            
            # Query base para busca por similaridade coseno
            query = f"""
                SELECT *,
                       conteudo_original AS conteudo,
                       1 - (vetor <=> $1::vector) as similarity_score
                FROM {quoted_table}
            """
            
            params = [vector_str]  # Passar como string
            param_index = 2
            
            # Adicionar filtros se fornecidos
            where_clauses = []
            
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        placeholders = ','.join([f'${i}' for i in range(param_index, param_index + len(value))])
                        where_clauses.append(f"{key} IN ({placeholders})")
                        params.extend(value)
                        param_index += len(value)
                    else:
                        where_clauses.append(f"{key} = ${param_index}")
                        params.append(value)
                        param_index += 1
            
            # Adicionar threshold de similaridade se fornecido
            if similarity_threshold:
                where_clauses.append(f"(1 - (vetor <=> $1::vector)) >= ${param_index}")
                params.append(similarity_threshold)
                param_index += 1
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Ordenar por similaridade e limitar resultados
            query += f" ORDER BY similarity_score DESC LIMIT ${param_index}"
            params.append(limit)
            
            self.logger.debug(f"🔍 Executando busca vetorial assíncrona em {table_name} (limit={limit})")
            
            # Executar query de forma assíncrona
            results = await self._connection.fetch(query, *params)
            
            # Converter para lista de dicionários
            documents = [dict(row) for row in results]
            similarity_scores = [doc.pop('similarity_score', 0.0) for doc in documents]
            
            execution_time = (time.time() - start_time) * 1000  # em ms
            
            self.logger.debug(f"✅ Busca assíncrona concluída: {len(documents)} documentos em {execution_time:.1f}ms")
            
            return SearchResult(
                documents=documents,
                total_count=len(documents),
                execution_time_ms=execution_time,
                similarity_scores=similarity_scores,
                metadata={
                    'table_name': table_name,
                    'query_vector_dim': len(query_vector),
                    'filters_applied': filters or {},
                    'similarity_threshold': similarity_threshold,
                    'async': True
                }
            )
            
        except asyncpg.PostgresError as e:
            self.logger.error(f"❌ Erro PostgreSQL na busca vetorial assíncrona: {e}")
            raise DALException(f"Erro na busca vetorial: {e}", e)
        except Exception as e:
            self.logger.error(f"❌ Erro inesperado na busca assíncrona: {e}")
            raise DALException(f"Erro inesperado na busca: {e}", e)
    
    async def execute_query_async(
        self,
        query: str,
        parameters: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """Executa uma consulta SQL customizada de forma ASSÍNCRONA."""
        try:
            if not self._connection or self._connection.is_closed():
                await self.connect()
            
            self.logger.debug(f"🔍 Executando query assíncrona: {query[:100]}...")
            
            if parameters:
                results = await self._connection.fetch(query, *parameters)
            else:
                results = await self._connection.fetch(query)
            
            return [dict(row) for row in results]
                
        except asyncpg.PostgresError as e:
            self.logger.error(f"❌ Erro PostgreSQL na query assíncrona: {e}")
            raise DALException(f"Erro na execução da query: {e}", e)
        except Exception as e:
            self.logger.error(f"❌ Erro inesperado na query assíncrona: {e}")
            raise DALException(f"Erro inesperado na query: {e}", e)
    
    async def get_table_info_async(self, table_name: str) -> Dict[str, Any]:
        """Obtém informações detalhadas sobre uma tabela de forma ASSÍNCRONA."""
        try:
            # Informações básicas da tabela
            table_query = """
                SELECT schemaname, tablename, tableowner, tablespace
                FROM pg_tables 
                WHERE tablename = $1
            """
            
            # Informações das colunas
            columns_query = """
                SELECT column_name, data_type, is_nullable, column_default,
                       character_maximum_length, numeric_precision, numeric_scale
                FROM information_schema.columns
                WHERE table_name = $1
                ORDER BY ordinal_position
            """
            
            # Informações dos índices
            indexes_query = """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = $1
            """
            
            table_info = await self._connection.fetchrow(table_query, table_name)
            
            if not table_info:
                raise DALException(f"Tabela '{table_name}' não encontrada")
            
            columns = await self._connection.fetch(columns_query, table_name)
            indexes = await self._connection.fetch(indexes_query, table_name)
            
            return {
                'table_info': dict(table_info),
                'columns': [dict(col) for col in columns],
                'indexes': [dict(idx) for idx in indexes]
            }
            
        except DALException:
            raise
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter informações da tabela {table_name} (ASYNC): {e}")
            raise DALException(f"Erro ao obter informações da tabela: {e}", e)
    
    async def list_tables_async(self) -> List[str]:
        """Lista todas as tabelas do banco atual de forma ASSÍNCRONA."""
        try:
            query = """
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """
            
            results = await self._connection.fetch(query)
            
            return [row['tablename'] for row in results]
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao listar tabelas (ASYNC): {e}")
            raise DALException(f"Erro ao listar tabelas: {e}", e)
    
    async def similarity_search_async(
        self, 
        table_name: str, 
        embedding: List[float], 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Método de compatibilidade com a interface anterior (ASSÍNCRONO).
        """
        result = await self.search_vectors_async(table_name, embedding, limit)
        
        # Adicionar similarity_score de volta aos documentos para compatibilidade
        for i, doc in enumerate(result.documents):
            if i < len(result.similarity_scores):
                doc['similarity_score'] = result.similarity_scores[i]
        
        return result.documents


# Testes
if __name__ == "__main__":
    import asyncio
    
    async def test_dal_async():
        """Teste da DAL assíncrona"""
        print("🧪 Testando PostgresDALAsync...")
        
        dal = PostgresDALAsync()
        
        try:
            # Testar conexão
            print("\n1️⃣ Testando conexão...")
            await dal.connect()
            print("✅ Conexão estabelecida")
            
            # Testar informações de conexão
            print("\n2️⃣ Obtendo informações de conexão...")
            conn_info = await dal.test_connection()
            print(f"✅ Banco: {conn_info.database_name}")
            print(f"✅ Host: {conn_info.host}:{conn_info.port}")
            print(f"✅ Extensões: {conn_info.extensions}")
            
            # Listar tabelas
            print("\n3️⃣ Listando tabelas...")
            tables = await dal.list_tables_async()
            print(f"✅ Tabelas encontradas: {tables}")
            
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
        
        finally:
            await dal.disconnect()
            print("\n👋 Teste concluído")
    
    asyncio.run(test_dal_async())
