"""Agente de TI hierárquico que coordena sub-especialistas."""

from __future__ import annotations

import logging
from typing import Dict, Optional

from agente_dev import criar_agente_dev
from agente_enduser import criar_agente_enduser
from agente_governance import criar_agente_governance
from agente_infra import criar_agente_infra
from agente_ti import criar_agente_ti
from subagents.hierarchical import TIHierarchicalAgent

# Configurar logging para debug
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TICoordinator:
    """Coordenador de TI que gerencia sub-especialistas hierarquicamente."""
    
    def __init__(self, *, debug: bool = False):
        self.debug = debug
        self.hierarchical_agent: Optional[TIHierarchicalAgent] = None
        self.base_ti_agent = None
        
    def initialize(self) -> bool:
        """Inicializa o coordenador TI e todos os sub-agentes."""
        
        try:
            # 1. Criar agente TI base
            logger.info("🤖 Inicializando agente TI base...")
            self.base_ti_agent = criar_agente_ti(debug=self.debug)
            if not self.base_ti_agent:
                logger.error("❌ Falha ao criar agente TI base")
                return False
            
            # 2. Criar agente hierárquico
            logger.info("🏗️ Criando estrutura hierárquica...")
            self.hierarchical_agent = TIHierarchicalAgent(self.base_ti_agent)
            
            # 3. Criar e registrar sub-agentes
            logger.info("👥 Inicializando sub-especialistas...")
            
            # Sub-agente de Governança
            governance_agent = criar_agente_governance(debug=self.debug)
            if governance_agent:
                self.hierarchical_agent.register_sub_agent(governance_agent)
                logger.info("✅ Sub-agente Governança registrado: Ana")
            else:
                logger.warning("⚠️ Falha ao criar sub-agente Governança")
            
            # Sub-agente de Infraestrutura
            infra_agent = criar_agente_infra(debug=self.debug)
            if infra_agent:
                self.hierarchical_agent.register_sub_agent(infra_agent)
                logger.info("✅ Sub-agente Infraestrutura registrado: Roberto")
            else:
                logger.warning("⚠️ Falha ao criar sub-agente Infraestrutura")
            
            # Sub-agente de Desenvolvimento
            dev_agent = criar_agente_dev(debug=self.debug)
            if dev_agent:
                self.hierarchical_agent.register_sub_agent(dev_agent)
                logger.info("✅ Sub-agente Desenvolvimento registrado: Carlos")
            else:
                logger.warning("⚠️ Falha ao criar sub-agente Desenvolvimento")
            
            # Sub-agente de Suporte ao Usuário Final
            enduser_agent = criar_agente_enduser(debug=self.debug)
            if enduser_agent:
                self.hierarchical_agent.register_sub_agent(enduser_agent)
                logger.info("✅ Sub-agente End-User registrado: Marina")
            else:
                logger.warning("⚠️ Falha ao criar sub-agente End-User")
            
            # 4. Verificar estatísticas
            stats = self.hierarchical_agent.get_hierarchy_stats()
            logger.info(f"📊 Hierarquia TI configurada: {stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na inicialização do TI Coordinator: {e}")
            return False
    
    def processar_pergunta(self, pergunta: str, user_profile: Dict) -> str:
        """Processa pergunta usando hierarquia de especialistas."""
        
        logger.info(f"🎯 TI Coordinator recebeu pergunta: '{pergunta[:50]}...'")
        
        if not self.hierarchical_agent:
            logger.error("❌ Sistema TI hierárquico não inicializado!")
            return "❌ Sistema TI hierárquico não inicializado."
        
        try:
            logger.info(f"🔄 Delegando para hierarquia TI...")
            # Delegar para hierarquia
            resultado = self.hierarchical_agent.process_with_hierarchy(pergunta, user_profile)
            
            # Log da delegação para debug
            stats = self.hierarchical_agent.get_hierarchy_stats()
            logger.info(f"� Delegações recentes: {stats.get('recent_delegations', [])}")
            logger.info(f"✅ TI Coordinator respondeu com {len(resultado)} caracteres")
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento hierárquico: {e}")
            # Fallback para agente TI base
            if self.base_ti_agent:
                return self.base_ti_agent.processar_pergunta(pergunta, user_profile)
            else:
                return "❌ Erro no sistema de TI. Tente novamente ou contate o suporte."
    
    def get_info(self) -> Dict:
        """Retorna informações sobre a hierarquia TI."""
        if not self.hierarchical_agent:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "base_agent": self.base_ti_agent.config.name if self.base_ti_agent else "N/A",
            "hierarchy_stats": self.hierarchical_agent.get_hierarchy_stats(),
            "debug_mode": self.debug
        }


# Factory function principal
def criar_ti_coordinator(*, debug: bool = False) -> Optional[TICoordinator]:
    """Cria e inicializa o coordenador TI hierárquico."""
    
    coordinator = TICoordinator(debug=debug)
    
    if coordinator.initialize():
        logger.info("🎉 TI Coordinator inicializado com sucesso!")
        return coordinator
    else:
        logger.error("💥 Falha na inicialização do TI Coordinator")
        return None


if __name__ == "__main__":
    # Configurar logging para teste
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Teste do sistema hierárquico
    print("🚀 Testando TI Coordinator Hierárquico...")
    
    coordinator = criar_ti_coordinator(debug=True)
    
    if not coordinator:
        print("❌ Falha na inicialização")
        exit(1)
    
    # Perfil de teste
    perfil_teste = {
        "nome": "João Tester",
        "cargo": "Analista",
        "area": "TI",
        "nivel_hierarquico": 2,
        "geografia": "BR",
        "projetos": ["Projeto X"]
    }
    
    # Perguntas de teste para diferentes especialistas
    perguntas_teste = [
        ("Governança", "Qual é a política de LGPD para desenvolvimento?"),
        ("Infraestrutura", "Como está o status dos servidores principais?"), 
        ("Desenvolvimento", "Qual é o processo de deploy em produção?"),
        ("TI Geral", "Como solicitar acesso ao sistema X?")
    ]
    
    print("\n" + "="*60)
    print("🧪 TESTES DE DELEGAÇÃO HIERÁRQUICA")
    print("="*60)
    
    for categoria, pergunta in perguntas_teste:
        print(f"\n🎯 [{categoria}] {pergunta}")
        print("-" * 50)
        
        resposta = coordinator.processar_pergunta(pergunta, perfil_teste)
        print(f"🤖 Resposta: {resposta[:200]}...")
        
    # Estatísticas finais
    print("\n" + "="*60)
    print("📊 ESTATÍSTICAS FINAIS")
    print("="*60)
    info = coordinator.get_info()
    print(f"Status: {info['status']}")
    print(f"Sub-agentes: {info['hierarchy_stats']['sub_agents']}")
    print(f"Delegações: {len(info['hierarchy_stats']['recent_delegations'])}")