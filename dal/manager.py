"""
DAL Factory e Manager - Gerenciamento centralizado de conexões de banco.

Este módulo fornece um ponto único para criação e gerenciamento de instâncias
da DAL, implementando patterns como Factory e Singleton para conexões.
"""

from typing import Dict, Optional, Any
from enum import Enum

from core.config import config
from .postgres_dal import PostgresDAL
from .base_dal import BaseDAL, DALException


class DatabaseType(Enum):
    """Tipos de banco de dados suportados."""
    POSTGRESQL = "postgresql"


class DALFactory:
    """
    Factory para criação de instâncias DAL baseada no tipo de banco configurado.
    
    Permite facilmente trocar implementações de banco no futuro mantendo
    a mesma interface.
    """
    
    @staticmethod
    def create_dal(
        db_type: DatabaseType = DatabaseType.POSTGRESQL,
        connection_string: Optional[str] = None
    ) -> BaseDAL:
        """
        Cria uma instância DAL apropriada para o tipo de banco especificado.
        
        Args:
            db_type: Tipo do banco de dados
            connection_string: String de conexão customizada (opcional)
            
        Returns:
            Instância da DAL apropriada
            
        Raises:
            DALException: Se o tipo de banco não for suportado
        """
        if db_type == DatabaseType.POSTGRESQL:
            return PostgresDAL(connection_string)
        else:
            raise DALException(f"Tipo de banco não suportado: {db_type}")
    
    @staticmethod
    def create_main_dal() -> BaseDAL:
        """
        Cria a DAL principal usando configurações padrão.
        
        Returns:
            Instância DAL configurada para o banco principal
        """
        return PostgresDAL(config.database.main_url)
    
    @staticmethod
    def create_knowledge_dal(table_suffix: str) -> BaseDAL:
        """
        Cria DAL para tabelas de conhecimento específicas.
        
        Args:
            table_suffix: Sufixo da tabela de conhecimento (rh, ti, etc.)
            
        Returns:
            Instância DAL configurada para a base de conhecimento específica
        """
        # Mapear sufixos para URLs de configuração específicas
        knowledge_urls = {
            'rh': config.database.rh_url or config.database.main_url,
            'ti': config.database.ti_url or config.database.main_url,
            'governance': config.database.governance_url or config.database.main_url,
            'infra': config.database.infra_url or config.database.main_url
        }
        
        connection_url = knowledge_urls.get(table_suffix.lower(), config.database.main_url)
        return PostgresDAL(connection_url)


class DALManager:
    """
    Gerenciador de instâncias DAL com pool de conexões e reutilização.
    
    Implementa padrão Singleton para evitar múltiplas conexões desnecessárias
    e fornece métodos convenientes para operações comuns.
    """
    
    _instances: Dict[str, BaseDAL] = {}
    _logger = config.get_logger("DALManager")
    
    @classmethod
    def get_main_dal(cls) -> BaseDAL:
        """
        Obtém ou cria a instância DAL principal.
        
        Returns:
            Instância DAL principal (singleton)
        """
        if 'main' not in cls._instances:
            cls._logger.info("🏗️ Criando instância DAL principal")
            cls._instances['main'] = DALFactory.create_main_dal()
        
        return cls._instances['main']
    
    @classmethod
    def get_knowledge_dal(cls, table_suffix: str) -> BaseDAL:
        """
        Obtém ou cria instância DAL para base de conhecimento específica.
        
        Args:
            table_suffix: Sufixo da base de conhecimento (rh, ti, etc.)
            
        Returns:
            Instância DAL para a base de conhecimento específica
        """
        key = f"knowledge_{table_suffix}"
        
        if key not in cls._instances:
            cls._logger.info(f"🏗️ Criando instância DAL para {table_suffix}")
            cls._instances[key] = DALFactory.create_knowledge_dal(table_suffix)
        
        return cls._instances[key]
    
    @classmethod
    def test_all_connections(cls) -> Dict[str, Any]:
        """
        Testa todas as conexões ativas e retorna relatório de status.
        
        Returns:
            Dicionário com status de cada conexão
        """
        results = {}
        
        for name, dal in cls._instances.items():
            try:
                connection_info = dal.test_connection()
                results[name] = {
                    'status': connection_info.status.value,
                    'database': connection_info.database_name,
                    'host': connection_info.host,
                    'extensions': connection_info.extensions,
                    'error': connection_info.error_message
                }
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
    
    @classmethod
    def disconnect_all(cls) -> None:
        """Desconecta todas as instâncias DAL ativas."""
        cls._logger.info("🔌 Desconectando todas as instâncias DAL")
        
        for name, dal in cls._instances.items():
            try:
                dal.disconnect()
                cls._logger.info(f"✅ {name} desconectado com sucesso")
            except Exception as e:
                cls._logger.error(f"❌ Erro ao desconectar {name}: {e}")
        
        cls._instances.clear()
    
    @classmethod
    def get_connection_summary(cls) -> Dict[str, Any]:
        """
        Retorna resumo de todas as conexões ativas.
        
        Returns:
            Resumo com estatísticas das conexões
        """
        return {
            'total_connections': len(cls._instances),
            'active_connections': list(cls._instances.keys()),
            'status': cls.test_all_connections()
        }


# Instâncias de conveniência para uso direto
def get_main_dal() -> BaseDAL:
    """Função de conveniência para obter DAL principal."""
    return DALManager.get_main_dal()


def get_knowledge_dal(table_suffix: str) -> BaseDAL:
    """Função de conveniência para obter DAL de conhecimento."""
    return DALManager.get_knowledge_dal(table_suffix)


def search_knowledge(
    table_name: str,
    query_vector: list,
    limit: int = 10,
    table_suffix: Optional[str] = None
) -> list:
    """
    Função de conveniência para busca em bases de conhecimento.
    
    Args:
        table_name: Nome da tabela
        query_vector: Vetor de consulta (embedding)
        limit: Limite de resultados
        table_suffix: Sufixo da base (auto-detectado se não fornecido)
        
    Returns:
        Lista de documentos encontrados
    """
    # Auto-detectar sufixo se não fornecido
    if not table_suffix:
        table_lower = table_name.lower()
        if 'rh' in table_lower:
            table_suffix = 'rh'
        elif any(term in table_lower for term in ['ti', 'tech', 'governance', 'infra']):
            table_suffix = 'ti'
        else:
            table_suffix = 'main'
    
    dal = get_knowledge_dal(table_suffix)
    result = dal.search_vectors(table_name, query_vector, limit)
    return result.documents