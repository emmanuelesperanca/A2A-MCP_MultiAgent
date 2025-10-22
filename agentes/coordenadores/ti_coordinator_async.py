"""Coordenador de TI Hierárquico - VERSÃO ASSÍNCRONA
Gerencia sub-especialistas de TI de forma assíncrona para máxima performance"""

from __future__ import annotations

import logging
from typing import Dict, Optional
import asyncio

from agentes.subagentes.agente_dev_async import criar_agente_dev_async
from agentes.subagentes.agente_enduser_async import criar_agente_enduser_async
from agentes.subagentes.agente_governance_async import criar_agente_governance_async
# from agente_ti import criar_agente_ti  # OBSOLETO: Movido para obsoleto/
from subagents.hierarchical import TIHierarchicalAgent

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TICoordinatorAsync:
    """Coordenador de TI que gerencia sub-especialistas de forma ASSÍNCRONA"""
    
    def __init__(self, *, debug: bool = False):
        self.debug = debug
        self.hierarchical_agent: Optional[TIHierarchicalAgent] = None
        self.base_ti_agent = None
        
    async def initialize_async(self) -> bool:
        """Inicializa o coordenador TI e todos os sub-agentes de forma ASSÍNCRONA"""
        
        try:
            # 1. Criar agente TI base (OBSOLETO - comentado)
            # logger.info("🤖 Inicializando agente TI base (ASYNC)...")
            # self.base_ti_agent = await asyncio.to_thread(criar_agente_ti, debug=self.debug)
            # if not self.base_ti_agent:
            #     logger.error("❌ Falha ao criar agente TI base")
            #     return False
            
            # 2. Criar agente hierárquico (sem base agent por enquanto)
            logger.info("🏗️ Criando estrutura hierárquica (ASYNC)...")
            self.hierarchical_agent = TIHierarchicalAgent(base_agent=None)
            
            # 3. Criar e registrar sub-agentes de forma concorrente
            logger.info("👥 Inicializando sub-especialistas (ASYNC/CONCORRENTE)...")
            
            # Criar todos os sub-agentes em paralelo
            sub_agents_tasks = [
                asyncio.to_thread(criar_agente_governance_async, debug=self.debug),
                asyncio.to_thread(criar_agente_dev_async, debug=self.debug),
                asyncio.to_thread(criar_agente_enduser_async, debug=self.debug)
            ]
            
            sub_agents_results = await asyncio.gather(*sub_agents_tasks, return_exceptions=True)
            
            # Nomes dos sub-agentes para logging
            sub_agent_names = ['Governança', 'Desenvolvimento', 'End-User']
            
            # Registrar os sub-agentes criados com sucesso
            for i, (result, name) in enumerate(zip(sub_agents_results, sub_agent_names)):
                if isinstance(result, Exception):
                    logger.warning(f"⚠️ Erro ao criar sub-agente {name}: {result}")
                elif result:
                    self.hierarchical_agent.register_sub_agent(result)
                    logger.info(f"✅ Sub-agente {name} registrado")
                else:
                    logger.warning(f"⚠️ Falha ao criar sub-agente {name}")
            
            # 4. Verificar estatísticas
            stats = self.hierarchical_agent.get_hierarchy_stats()
            logger.info(f"📊 Hierarquia TI configurada (ASYNC): {stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na inicialização do TI Coordinator (ASYNC): {e}")
            return False
    
    async def processar_pergunta_async(
        self,
        pergunta: str,
        user_profile: Dict,
        sub_agentes_sugeridos: list = None
    ) -> str:
        """
        Processa pergunta usando hierarquia de especialistas de forma ASSÍNCRONA
        
        Args:
            pergunta: Pergunta do usuário
            user_profile: Perfil do usuário
            sub_agentes_sugeridos: 🆕 Lista de sub-agentes sugeridos pela LLM
        
        Returns:
            Resposta processada
        """
        
        logger.info(f"🎯 TI Coordinator recebeu pergunta (ASYNC): '{pergunta[:50]}...'")
        
        if sub_agentes_sugeridos:
            logger.info(f"💡 Sub-agentes sugeridos pela LLM: {sub_agentes_sugeridos}")
        
        if not self.hierarchical_agent:
            logger.error("❌ Sistema TI hierárquico não inicializado!")
            return "❌ Sistema TI hierárquico não inicializado."
        
        try:
            logger.info("🔄 Delegando para hierarquia TI (ASYNC)...")
            
            # 🆕 Se houver sugestões da LLM, tentar usar o agente mais relevante primeiro
            if sub_agentes_sugeridos and len(sub_agentes_sugeridos) > 0:
                agente_principal = sub_agentes_sugeridos[0]
                logger.info(f"🎯 Priorizando sub-agente sugerido: {agente_principal}")
                
                # Adicionar dica no contexto para o hierarchical agent
                pergunta_com_dica = f"[SUGESTÃO_AGENTE: {agente_principal}] {pergunta}"
            else:
                pergunta_com_dica = pergunta
            
            # Processar de forma assíncrona
            resultado = await asyncio.to_thread(
                self.hierarchical_agent.process_with_hierarchy,
                pergunta_com_dica,
                user_profile
            )
            
            # Log da delegação para debug
            stats = self.hierarchical_agent.get_hierarchy_stats()
            logger.info(f"📊 Delegações recentes: {stats.get('recent_delegations', [])}")
            logger.info(f"✅ TI Coordinator respondeu com {len(resultado)} caracteres (ASYNC)")
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento hierárquico (ASYNC): {e}")
            # Fallback para agente TI base
            if self.base_ti_agent:
                return await asyncio.to_thread(
                    self.base_ti_agent.processar_pergunta,
                    pergunta,
                    user_profile
                )
            else:
                return "❌ Erro no sistema de TI. Tente novamente ou contate o suporte."
    
    def get_info(self) -> Dict:
        """Retorna informações sobre a hierarquia TI"""
        if not self.hierarchical_agent:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "base_agent": self.base_ti_agent.config.name if self.base_ti_agent else "N/A",
            "hierarchy_stats": self.hierarchical_agent.get_hierarchy_stats(),
            "debug_mode": self.debug,
            "tipo": "async"
        }


# Factory function assíncrona
async def criar_ti_coordinator_async(*, debug: bool = False) -> Optional[TICoordinatorAsync]:
    """Cria e inicializa o coordenador TI hierárquico de forma ASSÍNCRONA"""
    
    coordinator = TICoordinatorAsync(debug=debug)
    
    if await coordinator.initialize_async():
        logger.info("🎉 TI Coordinator ASYNC inicializado com sucesso!")
        return coordinator
    else:
        logger.error("💥 Falha na inicialização do TI Coordinator ASYNC")
        return None


if __name__ == "__main__":
    import asyncio
    
    async def teste_coordinator():
        """Teste do sistema hierárquico assíncrono"""
        # Configurar logging para teste
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        print("🚀 Testando TI Coordinator Hierárquico ASYNC...")
        
        coordinator = await criar_ti_coordinator_async(debug=True)
        
        if not coordinator:
            print("❌ Falha na inicialização")
            return
        
        # Perfil de teste
        perfil_teste = {
            "Nome": "João Tester",
            "Cargo": "Analista",
            "Departamento": "TI",
            "Nivel_Hierarquico": 2,
            "Geografia": "BR",
            "Projetos": ["Projeto X"]
        }
        
        # Perguntas de teste para diferentes especialistas
        perguntas_teste = [
            ("Governança", "Qual é a política de LGPD para desenvolvimento?"),
            ("Infraestrutura", "Como está o status dos servidores principais?"),
            ("Desenvolvimento", "Qual é o processo de deploy em produção?"),
            ("TI Geral", "Como solicitar acesso ao sistema X?")
        ]
        
        print("\n" + "="*60)
        print("🧪 TESTES DE DELEGAÇÃO HIERÁRQUICA (ASYNC)")
        print("="*60)
        
        # Processar perguntas de forma sequencial (para melhor visualização dos logs)
        for categoria, pergunta in perguntas_teste:
            print(f"\n🎯 [{categoria}] {pergunta}")
            print("-" * 50)
            
            resposta = await coordinator.processar_pergunta_async(pergunta, perfil_teste)
            print(f"🤖 Resposta: {resposta[:200]}...")
        
        # Estatísticas finais
        print("\n" + "="*60)
        print("📊 ESTATÍSTICAS FINAIS")
        print("="*60)
        info = coordinator.get_info()
        print(f"Status: {info['status']}")
        print(f"Tipo: {info.get('tipo', 'N/A')}")
        print(f"Sub-agentes: {info['hierarchy_stats']['sub_agents']}")
        print(f"Delegações: {len(info['hierarchy_stats']['recent_delegations'])}")
    
    # Executar teste
    asyncio.run(teste_coordinator())
