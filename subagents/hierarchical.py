"""Interface e classes para suporte a agentes hierárquicos com sub-especialistas."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from subagents.base_subagent import BaseSubagent

logger = logging.getLogger(__name__)


@dataclass
class SubSpecialtyRule:
    """Regra para delegação para sub-especialistas."""
    name: str
    target_subagent: str
    keywords: List[str]
    description: str
    confidence_threshold: float = 0.3
    priority: int = 1  # Maior número = maior prioridade


class HierarchicalAgent(ABC):
    """Interface para agentes que podem ter sub-agentes especializados."""
    
    def __init__(self):
        self.sub_agents: Dict[str, 'BaseSubagent'] = {}
        self.subspecialty_rules: List[SubSpecialtyRule] = []
        self.delegation_history: List[str] = []
    
    def register_sub_agent(self, sub_agent: 'BaseSubagent') -> None:
        """Registra um sub-agente especializado."""
        identifier = sub_agent.config.identifier
        self.sub_agents[identifier] = sub_agent
        logger.info(f"Sub-agente registrado: {identifier} sob {self.__class__.__name__}")
    
    def add_subspecialty_rule(self, rule: SubSpecialtyRule) -> None:
        """Adiciona regra de sub-especialização."""
        self.subspecialty_rules.append(rule)
        # Ordena por prioridade (maior número primeiro)
        self.subspecialty_rules.sort(key=lambda r: r.priority, reverse=True)
    
    def find_best_subagent(self, query: str) -> Tuple[Optional[str], float]:
        """Encontra o melhor sub-agente para uma pergunta."""
        best_match = None
        best_score = 0.0
        
        query_lower = query.lower()
        print(f"🔎 Analisando palavras-chave em: '{query_lower}'")
        logger.debug(f"Analisando query: '{query_lower}'")
        
        for rule in self.subspecialty_rules:
            # Calcula score baseado nas keywords
            matches = 0
            matched_keywords = []
            
            for keyword in rule.keywords:
                if keyword.lower() in query_lower:
                    matches += 1
                    matched_keywords.append(keyword)
            
            if matches > 0:
                # Score baseado no número de matches e peso das palavras
                score = matches / len(rule.keywords)
                
                print(f"📝 Regra '{rule.target_subagent}': {matches} matches {matched_keywords}, score: {score:.3f}")
                logger.debug(f"Regra '{rule.name}': {matches} matches {matched_keywords}, score: {score:.3f}, threshold: {rule.confidence_threshold}")
                
                if score >= rule.confidence_threshold and score > best_score:
                    best_match = rule.target_subagent
                    best_score = score
                    print(f"🎯 Nova melhor opção: {best_match} (score: {score:.3f})")
                    logger.debug(f"Nova melhor opção: {best_match} (score: {score:.3f})")
        
        logger.info(f"Delegação hierárquica: '{query[:50]}...' -> {best_match} (score: {best_score:.3f})")
        return best_match, best_score
    
    @abstractmethod
    def process_with_hierarchy(self, query: str, user_profile: Dict) -> str:
        """Processa pergunta considerando hierarquia de sub-agentes."""
        pass


class TIHierarchicalAgent(HierarchicalAgent):
    """Agente de TI com capacidade hierárquica."""
    
    def __init__(self, base_agent: 'BaseSubagent'):
        super().__init__()
        self.base_agent = base_agent
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """Configura regras padrão de sub-especialização para TI."""
        
        # Governance - Políticas, compliance, segurança
        governance_rule = SubSpecialtyRule(
            name="governance_delegation",
            target_subagent="governance",
            keywords=[
                # Português
                "política", "compliance", "auditoria", "segurança", "lgpd",
                "iso", "itil", "governança", "riscos", "controle", "norma",
                "certificação", "procedimento", "regulamentação", "27001",
                "assinatura", "assinaturas", "eletrônica", "digital", "validação",
                "senhas", "senha", "autenticação", "conformidade",
                # Inglês
                "policy", "policies", "governance", "compliance", "audit", "security",
                "regulation", "standard", "certification", "procedure", "risk",
                "control", "signature", "signatures", "sign", "electronic", "digital",
                "validation", "password", "passwords", "authentication", "regulatory",
                # Espanhol
                "política", "políticas", "gobernanza", "cumplimiento", "auditoría",
                "firma", "firmas", "electrónica", "validación", "contraseña"
            ],
            description="Questões de governança, compliance e políticas de TI",
            confidence_threshold=0.03,  # Threshold ainda mais baixo para captar melhor
            priority=3
        )
        
        # Infraestrutura - Servidores, redes, hardware
        infra_rule = SubSpecialtyRule(
            name="infra_delegation",
            target_subagent="infra",
            keywords=[
                "servidor", "rede", "hardware", "datacenter", "backup",
                "disaster", "recovery", "uptime", "monitoramento", "capacidade",
                "performance", "storage", "virtualização", "cloud", "aws", "status"
            ],
            description="Questões de infraestrutura e operações",
            confidence_threshold=0.05,  # Threshold mais baixo
            priority=2
        )
        
        # Desenvolvimento - Aplicações, sistemas, projetos
        dev_rule = SubSpecialtyRule(
            name="dev_delegation",
            target_subagent="dev",
            keywords=[
                "desenvolvimento", "aplicação", "sistema", "código", "projeto",
                "bug", "feature", "deploy", "release", "api", "banco", "dados",
                "integração", "teste", "homologação", "produção", "aplicação"
            ],
            description="Questões de desenvolvimento e sistemas",
            confidence_threshold=0.05,  # Threshold mais baixo
            priority=1
        )
        
        # Suporte ao Usuário Final - Senha, login, ferramentas básicas
        enduser_rule = SubSpecialtyRule(
            name="enduser_delegation",
            target_subagent="enduser",
            keywords=[
                "senha", "login", "acesso", "reset", "email", "outlook",
                "word", "excel", "teams", "usuario", "conta", "perfil",
                "suporte", "help", "ajuda", "como usar", "tutorial"
            ],
            description="Questões de suporte ao usuário final e ferramentas básicas",
            confidence_threshold=0.05,
            priority=4  # Maior prioridade para questões de usuário
        )
        
        self.add_subspecialty_rule(enduser_rule)  # Adicionar primeiro (maior prioridade)
        self.add_subspecialty_rule(governance_rule)
        self.add_subspecialty_rule(infra_rule)
        self.add_subspecialty_rule(dev_rule)
    
    def process_with_hierarchy(self, query: str, user_profile: Dict) -> str:
        """Processa pergunta usando hierarquia de sub-especialistas."""
        
        print(f"🔍 TI Hierarchy analisando: '{query[:50]}...'")
        
        # 1. Tentar encontrar sub-agente mais adequado
        best_subagent, score = self.find_best_subagent(query)
        
        print(f"📊 TI Hierarchy: Melhor match = {best_subagent}, Score = {score:.3f}")
        logger.info(f"TI Hierarchy: Best match = {best_subagent}, Score = {score:.3f}")
        
        # 2. Se encontrou sub-agente específico, delegar
        if best_subagent and best_subagent in self.sub_agents:
            sub_agent = self.sub_agents[best_subagent]
            
            print(f"✅ Delegando para sub-especialista: {sub_agent.config.name}")
            logger.info(f"🔄 TI delegando para sub-especialista: {sub_agent.config.name}")
            
            try:
                # Processa com o sub-agente especializado
                print(f"🤖 Processando com {sub_agent.config.name}...")
                result = sub_agent.processar_pergunta(query, user_profile)
                
                # Adiciona attribution da hierarquia
                attribution = f"\n\n📋 Resposta fornecida por: {sub_agent.config.name} ({sub_agent.config.specialty})"
                attribution += "\n🎯 Coordenado pelo time de TI"
                
                self.delegation_history.append(f"{query[:50]}... -> {best_subagent}")
                
                return result + attribution
                
            except Exception as e:
                logger.error(f"Erro no sub-agente {best_subagent}: {e}")
                # Fallback para agente TI principal
        
        # 3. Se não encontrou sub-agente ou deu erro, usar TI principal
        print("⚠️ Nenhum sub-agente específico encontrado, usando TI geral")
        logger.info("🤖 TI processando com conhecimento geral")
        result = self.base_agent.processar_pergunta(query, user_profile)
        
        attribution = f"\n\n📋 Resposta fornecida por: {self.base_agent.config.name} (TI Geral)"
        
        return result + attribution
    
    def get_hierarchy_stats(self) -> Dict:
        """Retorna estatísticas da hierarquia."""
        return {
            "sub_agents_count": len(self.sub_agents),
            "sub_agents": list(self.sub_agents.keys()),
            "rules_count": len(self.subspecialty_rules),
            "delegations_history": len(self.delegation_history),
            "recent_delegations": self.delegation_history[-5:] if self.delegation_history else []
        }
