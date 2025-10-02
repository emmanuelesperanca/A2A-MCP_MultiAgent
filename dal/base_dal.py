"""
Base Data Access Layer (DAL) - Classes e interfaces base para acesso a dados.

Define a interface comum que todas as implementações de DAL devem seguir,
garantindo consistência e permitindo diferentes tipos de banco de dados no futuro.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class DALException(Exception):
    """Exceção base para erros da camada de acesso a dados."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ConnectionStatus(Enum):
    """Status da conexão com o banco de dados."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class SearchResult:
    """Resultado de uma busca vetorial."""
    documents: List[Dict[str, Any]]
    total_count: int
    execution_time_ms: float
    similarity_scores: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConnectionInfo:
    """Informações sobre a conexão com o banco."""
    status: ConnectionStatus
    database_name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    extensions: Optional[List[str]] = None
    error_message: Optional[str] = None


class BaseDAL(ABC):
    """
    Classe base abstrata para todas as implementações de Data Access Layer.
    
    Define a interface comum que deve ser implementada por todas as classes DAL,
    garantindo consistência e permitindo polimorfismo.
    """
    
    def __init__(self, connection_string: str):
        """
        Inicializa a DAL com uma string de conexão.
        
        Args:
            connection_string: String de conexão para o banco de dados
        """
        self.connection_string = connection_string
        self._connection = None
        
    @abstractmethod
    def connect(self) -> bool:
        """
        Estabelece conexão com o banco de dados.
        
        Returns:
            True se a conexão foi estabelecida com sucesso, False caso contrário
            
        Raises:
            DALException: Se houver erro na conexão
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Encerra a conexão com o banco de dados.
        
        Returns:
            True se a conexão foi encerrada com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> ConnectionInfo:
        """
        Testa a conexão com o banco e retorna informações sobre o status.
        
        Returns:
            ConnectionInfo com detalhes sobre a conexão
        """
        pass
    
    @abstractmethod
    def search_vectors(
        self, 
        table_name: str,
        query_vector: List[float], 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        similarity_threshold: Optional[float] = None
    ) -> SearchResult:
        """
        Realiza busca por similaridade vetorial.
        
        Args:
            table_name: Nome da tabela para buscar
            query_vector: Vetor de consulta para busca por similaridade
            limit: Número máximo de resultados a retornar
            filters: Filtros adicionais a aplicar na consulta
            similarity_threshold: Threshold mínimo de similaridade
            
        Returns:
            SearchResult com os documentos encontrados e metadados
            
        Raises:
            DALException: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executa uma consulta SQL customizada.
        
        Args:
            query: Consulta SQL a ser executada
            parameters: Parâmetros para a consulta
            
        Returns:
            Lista de resultados da consulta
            
        Raises:
            DALException: Se houver erro na execução da consulta
        """
        pass
    
    @abstractmethod
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Obtém informações sobre uma tabela específica.
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            Dicionário com informações da tabela (colunas, índices, etc.)
            
        Raises:
            DALException: Se a tabela não existir ou houver erro
        """
        pass
    
    @abstractmethod
    def list_tables(self) -> List[str]:
        """
        Lista todas as tabelas disponíveis no banco.
        
        Returns:
            Lista com nomes das tabelas
            
        Raises:
            DALException: Se houver erro ao listar tabelas
        """
        pass
    
    def __enter__(self):
        """Context manager entry."""
        if not self.connect():
            raise DALException("Falha ao estabelecer conexão com o banco de dados")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False