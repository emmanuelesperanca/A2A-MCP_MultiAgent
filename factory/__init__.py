"""Factory module for dynamic agent creation
Permite criar coordenadores e subagentes de forma dinâmica via pipeline"""

from .agent_factory import AgentFactory, AgentType, AgentConfig
from .agent_registry import AgentRegistry

__all__ = ['AgentFactory', 'AgentType', 'AgentConfig', 'AgentRegistry']
