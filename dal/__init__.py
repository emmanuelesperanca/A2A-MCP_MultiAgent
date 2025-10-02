"""
Data Access Layer (DAL) - Camada de Acesso a Dados

Este módulo centraliza toda a lógica de acesso ao banco de dados PostgreSQL,
isolando os agentes e outras partes da aplicação dos detalhes de implementação
do banco de dados.

Uso recomendado:
    from dal import get_main_dal, search_knowledge
    
    # Para busca simples
    docs = search_knowledge("knowledge_rh", embedding_vector, limit=5)
    
    # Para operações avançadas
    dal = get_main_dal()
    with dal:
        result = dal.search_vectors("table_name", vector, filters={...})
"""

from .postgres_dal import PostgresDAL
from .base_dal import BaseDAL, DALException, SearchResult, ConnectionInfo
from .manager import (
    DALManager, DALFactory,
    get_main_dal, get_knowledge_dal, search_knowledge
)

__all__ = [
    'PostgresDAL', 'BaseDAL', 'DALException', 'SearchResult', 'ConnectionInfo',
    'DALManager', 'DALFactory',
    'get_main_dal', 'get_knowledge_dal', 'search_knowledge'
]