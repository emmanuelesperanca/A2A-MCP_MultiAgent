"""Registry de tools MCP organizadas por categoria."""

import logging
from typing import Dict, List, Optional

from .base import MCPTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry centralizado de tools MCP organizadas por categoria/agente."""
    
    def __init__(self):
        """Inicializa o registry vazio."""
        self._tools_by_category: Dict[str, List[MCPTool]] = {}
        self._tools_by_name: Dict[str, MCPTool] = {}
    
    def register_tool(self, tool: MCPTool, category: Optional[str] = None) -> None:
        """Registra uma tool no registry.
        
        Args:
            tool: Tool a ser registrada
            category: Categoria/agente (usa tool.category se não fornecido)
        """
        category = category or tool.category or "general"
        
        # Verifica conflitos de nome
        if tool.name in self._tools_by_name:
            existing_tool = self._tools_by_name[tool.name]
            if existing_tool.category != category:
                raise ValueError(
                    f"Tool '{tool.name}' já existe na categoria '{existing_tool.category}'"
                )
        
        # Adiciona à categoria
        if category not in self._tools_by_category:
            self._tools_by_category[category] = []
        
        self._tools_by_category[category].append(tool)
        self._tools_by_name[tool.name] = tool
        
        logger.info(f"Tool '{tool.name}' registrada na categoria '{category}'")
    
    def get_tools_for_category(self, category: str) -> List[MCPTool]:
        """Retorna todas as tools de uma categoria.
        
        Args:
            category: Nome da categoria
            
        Returns:
            Lista de tools da categoria
        """
        return self._tools_by_category.get(category, [])
    
    def get_tool_by_name(self, name: str) -> Optional[MCPTool]:
        """Recupera uma tool pelo nome.
        
        Args:
            name: Nome da tool
            
        Returns:
            Tool encontrada ou None
        """
        return self._tools_by_name.get(name)
    
    def list_categories(self) -> List[str]:
        """Lista todas as categorias registradas.
        
        Returns:
            Lista de nomes de categorias
        """
        return list(self._tools_by_category.keys())
    
    def list_all_tools(self) -> List[MCPTool]:
        """Lista todas as tools registradas.
        
        Returns:
            Lista de todas as tools
        """
        return list(self._tools_by_name.values())
    
    def remove_tool(self, name: str) -> bool:
        """Remove uma tool do registry.
        
        Args:
            name: Nome da tool a remover
            
        Returns:
            True se removida com sucesso, False se não encontrada
        """
        tool = self._tools_by_name.get(name)
        if not tool:
            return False
        
        # Remove do mapeamento por nome
        del self._tools_by_name[name]
        
        # Remove da categoria
        category = tool.category or "general"
        if category in self._tools_by_category:
            self._tools_by_category[category] = [
                t for t in self._tools_by_category[category] if t.name != name
            ]
            
            # Remove categoria se ficou vazia
            if not self._tools_by_category[category]:
                del self._tools_by_category[category]
        
        logger.info(f"Tool '{name}' removida do registry")
        return True
    
    def clear_category(self, category: str) -> int:
        """Remove todas as tools de uma categoria.
        
        Args:
            category: Nome da categoria a limpar
            
        Returns:
            Número de tools removidas
        """
        if category not in self._tools_by_category:
            return 0
        
        tools = self._tools_by_category[category]
        count = len(tools)
        
        # Remove do mapeamento por nome
        for tool in tools:
            self._tools_by_name.pop(tool.name, None)
        
        # Remove categoria
        del self._tools_by_category[category]
        
        logger.info(f"Removidas {count} tools da categoria '{category}'")
        return count
    
    def get_stats(self) -> Dict[str, int]:
        """Retorna estatísticas do registry.
        
        Returns:
            Dict com estatísticas (total_tools, categories_count, etc.)
        """
        return {
            "total_tools": len(self._tools_by_name),
            "categories_count": len(self._tools_by_category),
            "tools_by_category": {
                category: len(tools) 
                for category, tools in self._tools_by_category.items()
            }
        }


# Registry global padrão
default_registry = ToolRegistry()