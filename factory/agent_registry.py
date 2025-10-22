"""Agent Registry - Sistema de registro e rastreamento de agentes criados
Mantém registro de todos os agentes criados pela factory"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class AgentRegistry:
    """Gerencia registro de agentes criados dinamicamente"""
    
    def __init__(self, registry_file: Optional[str] = None):
        if registry_file is None:
            base_path = Path(__file__).parent.parent
            registry_file = base_path / "factory" / "agents_registry.json"
        
        self.registry_file = Path(registry_file)
        self.agents: Dict[str, Dict[str, Any]] = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Dict[str, Any]]:
        """Carrega registro do arquivo JSON"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Erro ao carregar registry: {e}")
                return {}
        return {}
    
    def reload(self):
        """Recarrega o registry do arquivo JSON"""
        print(f"🔄 [Registry] Recarregando dados do arquivo...")
        self.agents = self._load_registry()
        print(f"✅ [Registry] {len(self.agents)} agentes recarregados")
    
    def _save_registry(self):
        """Salva registro no arquivo JSON"""
        try:
            # Criar diretório se não existir
            self.registry_file.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"💾 Salvando registry em: {self.registry_file.absolute()}")
            print(f"📊 Total de agentes: {len(self.agents)}")
            
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.agents, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Registry salvo com sucesso: {self.registry_file}")
            
            # Verificar se o arquivo foi realmente salvo
            if self.registry_file.exists():
                file_size = self.registry_file.stat().st_size
                print(f"✅ Arquivo confirmado: {file_size} bytes")
            else:
                print(f"⚠️ AVISO: Arquivo não encontrado após salvar!")
                
        except PermissionError as e:
            print(f"❌ ERRO DE PERMISSÃO ao salvar registry: {e}")
            print(f"   Verifique se o arquivo {self.registry_file} não está aberto em outro programa")
        except Exception as e:
            print(f"❌ ERRO ao salvar registry: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    def register_agent(self, agent_data: Dict[str, Any]):
        """
        Registra um novo agente
        
        Args:
            agent_data: Dicionário com dados do agente
                - identifier: ID único do agente
                - name: Nome do agente
                - specialty: Especialidade
                - type: 'coordinator' ou 'subagent'
                - file_path: Path do arquivo gerado
                - table_name: Nome da tabela (para subagents)
                - children: Lista de filhos (para coordinators)
                - keywords: Lista de palavras-chave
                - tools_enabled: Se usa ferramentas MCP
                - tools_category: Categoria das ferramentas
        """
        
        identifier = agent_data.get('identifier')
        if not identifier:
            raise ValueError("Agent identifier é obrigatório")
        
        print(f"📋 [Registry] Registrando agente: {identifier}")
        print(f"   Nome: {agent_data.get('name')}")
        print(f"   Tipo: {agent_data.get('type')}")
        
        # Adicionar timestamp
        agent_data['created_at'] = datetime.now().isoformat()
        agent_data['updated_at'] = datetime.now().isoformat()
        
        # Registrar
        self.agents[identifier] = agent_data
        
        print(f"   Total de agentes no registry: {len(self.agents)}")
        
        # Salvar
        self._save_registry()
        
        print(f"✅ [Registry] Agente registrado com sucesso: {identifier}")
    
    def get_agent(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Retorna dados de um agente específico"""
        return self.agents.get(identifier)
    
    def list_agents(self, agent_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista todos os agentes registrados
        
        Args:
            agent_type: Filtrar por tipo ('coordinator' ou 'subagent')
        
        Returns:
            Lista de agentes
        """
        if agent_type:
            return [
                agent for agent in self.agents.values()
                if agent.get('type') == agent_type
            ]
        return list(self.agents.values())
    
    def list_subagents(self) -> List[Dict[str, Any]]:
        """Lista apenas subagentes"""
        return self.list_agents(agent_type='subagent')
    
    def list_coordinators(self) -> List[Dict[str, Any]]:
        """Lista apenas coordenadores"""
        return self.list_agents(agent_type='coordinator')
    
    def update_agent(self, identifier: str, updates: Dict[str, Any]):
        """Atualiza dados de um agente"""
        if identifier not in self.agents:
            raise ValueError(f"Agente {identifier} não encontrado no registry")
        
        # Atualizar dados
        self.agents[identifier].update(updates)
        self.agents[identifier]['updated_at'] = datetime.now().isoformat()
        
        # Salvar
        self._save_registry()
        
        print(f"📝 Agente atualizado: {identifier}")
    
    def delete_agent(self, identifier: str) -> bool:
        """Remove um agente do registro"""
        if identifier in self.agents:
            del self.agents[identifier]
            self._save_registry()
            print(f"🗑️ Agente removido: {identifier}")
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas sobre os agentes registrados"""
        total = len(self.agents)
        subagents = len(self.list_subagents())
        coordinators = len(self.list_coordinators())
        
        # Agentes com ferramentas MCP
        with_tools = len([
            a for a in self.agents.values()
            if a.get('tools_enabled', False)
        ])
        
        return {
            "total": total,
            "subagents": subagents,
            "coordinators": coordinators,
            "with_mcp_tools": with_tools,
            "agents": list(self.agents.keys())
        }
    
    def export_to_frontend_config(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Exporta configuração para o frontend
        Formato compatível com o index.html
        """
        
        coordinators = []
        subagents = []
        
        for agent in self.agents.values():
            agent_info = {
                "id": agent.get('identifier'),
                "identifier": agent.get('identifier'),  # ✅ Campo para compatibilidade com JS
                "name": agent.get('name'),
                "specialty": agent.get('specialty'),
                "description": agent.get('description', ''),
                "icon": self._get_agent_icon(agent.get('specialty', ''))
            }
            
            if agent.get('type') == 'coordinator':
                agent_info['children'] = agent.get('children', [])
                coordinators.append(agent_info)
            else:
                agent_info['table'] = agent.get('table_name', '')
                agent_info['keywords'] = agent.get('keywords', [])
                subagents.append(agent_info)
        
        return {
            "coordinators": coordinators,
            "subagents": subagents
        }
    
    def _get_agent_icon(self, specialty: str) -> str:
        """Retorna ícone FontAwesome baseado na especialidade"""
        
        icon_map = {
            "TI": "fas fa-server",
            "Desenvolvimento": "fas fa-code",
            "Infraestrutura": "fas fa-network-wired",
            "Governança": "fas fa-gavel",
            "Suporte": "fas fa-headset",
            "RH": "fas fa-users",
            "Financeiro": "fas fa-dollar-sign",
            "Vendas": "fas fa-chart-line",
            "Marketing": "fas fa-bullhorn",
            "Operações": "fas fa-cogs"
        }
        
        # Buscar por palavra-chave na especialidade
        for key, icon in icon_map.items():
            if key.lower() in specialty.lower():
                return icon
        
        # Ícone padrão
        return "fas fa-robot"


# Singleton instance
_registry_instance = None

def get_registry() -> AgentRegistry:
    """Retorna instância singleton do registry"""
    global _registry_instance
    if _registry_instance is None:
        print("🔧 [Registry] Criando nova instância do AgentRegistry")
        _registry_instance = AgentRegistry()
        print(f"🔧 [Registry] Arquivo de registro: {_registry_instance.registry_file.absolute()}")
        print(f"🔧 [Registry] Agentes carregados: {len(_registry_instance.agents)}")
    else:
        print(f"🔧 [Registry] Usando instância existente ({len(_registry_instance.agents)} agentes)")
    return _registry_instance
