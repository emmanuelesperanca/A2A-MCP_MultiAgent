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

    def find_top_candidates(self, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Encontra os top-k candidatos para fallback chain.
        
        Args:
            query: Pergunta do usuário
            top_k: Número máximo de candidatos a retornar
            
        Returns:
            Lista ordenada de (agente, score) por score decrescente
        """
        candidates = []
        query_lower = query.lower()
        
        print(f"🔍 Analisando query: '{query_lower}'")
        print(f"📋 Total de regras: {len(self.subspecialty_rules)}")
        
        for rule in self.subspecialty_rules:
            matches = 0
            matched_keywords = []
            
            for keyword in rule.keywords:
                if keyword.lower() in query_lower:
                    matches += 1
                    matched_keywords.append(keyword)
            
            if matches > 0:
                score = matches / len(rule.keywords)
                print(f"🎯 Regra '{rule.name}' → {matches} matches, score: {score:.3f}, threshold: {rule.confidence_threshold}")
                print(f"   Keywords matched: {matched_keywords}")
                
                if score >= rule.confidence_threshold:
                    candidates.append((rule.target_subagent, score))
                    print(f"   ✅ Adicionado candidato: {rule.target_subagent}")
                else:
                    print(f"   ❌ Score abaixo do threshold")
            else:
                print(f"⚪ Regra '{rule.name}' → 0 matches")
        
        # Ordenar por score decrescente e pegar os top-k
        candidates.sort(key=lambda x: x[1], reverse=True)
        print(f"🏆 Candidatos finais: {candidates}")
        return candidates[:top_k]
    
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
    
    def _is_generic_response(self, response: str) -> bool:
        """Verifica se a resposta é genérica (indica que o agente não encontrou dados específicos)."""
        generic_indicators = [
            "não localizei informações específicas sobre",
            "não localizei essa informação específica",
            "não tenho informações específicas",
            "não encontrei dados específicos",
            "preciso de mais informações",
            "não possuo dados detalhados",
            "não encontrei essa informação",
            "não tenho acesso a essa informação",
            "informações não disponíveis",
            "dados não encontrados",
            "não consta em nossa base",
            "não foi possível localizar",
            "não possuo informações sobre",
            "não há dados disponíveis",
            "informação não encontrada",
            "desculpe, mas não encontrei",
            "lamento, mas não possuo"
        ]
        
        response_lower = response.lower()
        is_generic = any(indicator in response_lower for indicator in generic_indicators)
        
        # Debug logging para acompanhar detecção
        if is_generic:
            print(f"🔍 Resposta genérica detectada: '{response[:100]}...'")
        
        return is_generic
    
    def _get_delegation_reason(self, query: str, agent_type: str, score: float) -> str:
        """Explica o motivo da delegação para transparência."""
        query_lower = query.lower()
        
        reasons = {
            'governance': {
                'keywords': ['regulamentação', 'anvisa', 'política', 'compliance', 'segurança', 'auditoria', 'norma', 'lei', 'decreto'],
                'description': 'Especialista em regulamentações, políticas e compliance'
            },
            'infrastructure': {
                'keywords': ['servidor', 'rede', 'infraestrutura', 'hardware', 'sistema', 'performance'],  
                'description': 'Especialista em infraestrutura e sistemas'
            },
            'dev': {
                'keywords': ['desenvolvimento', 'código', 'programação', 'api', 'software', 'aplicação'],
                'description': 'Especialista em desenvolvimento de software'
            },
            'enduser': {
                'keywords': ['usuário', 'interface', 'suporte', 'treinamento', 'manual', 'tutorial'],
                'description': 'Especialista em suporte ao usuário final'
            }
        }
        
        if agent_type in reasons:
            agent_info = reasons[agent_type]
            matched_keywords = [kw for kw in agent_info['keywords'] if kw in query_lower]
            
            if matched_keywords:
                return f"{agent_info['description']}. Palavras-chave identificadas: {', '.join(matched_keywords)}"
            else:
                return f"{agent_info['description']}. Score de relevância: {score:.3f}"
        
        return f"Agente com maior score de relevância ({score:.3f}) para esta consulta"
    
    def process_with_hierarchy(self, query: str, user_profile: Dict) -> str:
        """Processa pergunta usando hierarquia de sub-especialistas com fallback chain."""
        
        # Inicializar cadeia de decisão para transparência
        decision_chain = []
        decision_chain.append(f"🔍 **Análise inicial**: TI Hierarchy analisando pergunta sobre '{query[:50]}...'")
        
        # 1. Obter top 3 candidatos para fallback chain
        candidates = self.find_top_candidates(query, top_k=3)
        
        if candidates:
            candidate_info = [(agent, f'{score:.3f}') for agent, score in candidates]
            decision_chain.append(f"🎯 **Candidatos identificados**: {candidate_info}")
            decision_chain.append("📊 **Critério de seleção**: Relevância por palavras-chave e especialidade")
            
            # 2. Tentar cada candidato em ordem de score
            for i, (candidate_agent, score) in enumerate(candidates):
                if candidate_agent not in self.sub_agents:
                    continue
                    
                sub_agent = self.sub_agents[candidate_agent]
                
                # Log da delegação com motivo
                delegation_reason = self._get_delegation_reason(query, candidate_agent, score)
                decision_chain.append(f"🔄 **Tentativa #{i+1}**: Delegando para **{sub_agent.config.name}** (score: {score:.3f})")
                decision_chain.append(f"💡 **Motivo**: {delegation_reason}")
                
                logger.info(f"🔄 TI delegando para sub-especialista: {sub_agent.config.name}")
                
                try:
                    # Processa com o sub-agente especializado
                    print(f"🤖 Chamando {sub_agent.config.name} (tabela: {sub_agent.config.table_name})")
                    result = sub_agent.processar_pergunta(query, user_profile)
                    
                    print(f"📝 {sub_agent.config.name} retornou {len(result)} caracteres")
                    print(f"🔍 Primeiros 100 chars: '{result[:100]}...'")
                    
                    # Verificar se o resultado é genérico (indica que não achou dados)
                    if self._is_generic_response(result):
                        print(f"🔍 Resposta detectada como genérica por {sub_agent.config.name}")
                        decision_chain.append(f"❌ **Resultado**: {sub_agent.config.name} não encontrou informações específicas")
                        if i < len(candidates) - 1:  # Se não é o último candidato
                            decision_chain.append("⚡ **Ação**: Tentando próximo especialista na hierarquia...")
                        continue
                    
                    # Sucesso! Adiciona cadeia de decisão transparente
                    decision_chain.append(f"✅ **Sucesso**: {sub_agent.config.name} encontrou informações relevantes!")
                    
                    # Montar resposta com transparência completa
                    transparency_section = "\n\n" + "="*60 + "\n"
                    transparency_section += "🧠 **CADEIA DE DECISÃO E RACIOCÍNIO**\n"
                    transparency_section += "="*60 + "\n"
                    for step in decision_chain:
                        transparency_section += f"{step}\n"
                    
                    transparency_section += f"\n📋 **Resposta final fornecida por**: {sub_agent.config.name} ({sub_agent.config.specialty})"
                    if i > 0:
                        transparency_section += f"\n🔄 **Redirecionamentos**: {i} tentativa(s) anteriores"
                    transparency_section += "\n🎯 **Coordenado por**: Sistema TI Hierárquico"
                    transparency_section += "\n" + "="*60
                    
                    self.delegation_history.append(f"{query[:50]}... -> {candidate_agent}")
                    
                    return result + transparency_section
                    
                except Exception as e:
                    logger.error(f"Erro no sub-agente {candidate_agent}: {e}")
                    print(f"❌ Erro em {sub_agent.config.name}, tentando próximo...")
                    continue
        else:
            decision_chain.append("❓ **Resultado da análise**: Nenhum especialista específico identificado")
            decision_chain.append("🔄 **Ação**: Redirecionando diretamente para TI geral")
        
        # 3. Se nenhum candidato funcionou, usar TI principal
        decision_chain.append("❌ **Resultado**: Nenhum especialista encontrou informações específicas")
        decision_chain.append("🔄 **Fallback final**: Redirecionando para agente TI geral")
        
        logger.info("🤖 TI processando com conhecimento geral")
        result = self.base_agent.processar_pergunta(query, user_profile)
        
        # Montar transparência para fallback final
        transparency_section = "\n\n" + "="*60 + "\n"
        transparency_section += "🧠 **CADEIA DE DECISÃO E RACIOCÍNIO**\n"
        transparency_section += "="*60 + "\n"
        for step in decision_chain:
            transparency_section += f"{step}\n"
        
        transparency_section += f"\n📋 **Resposta final fornecida por**: {self.base_agent.config.name} (TI Geral)"
        transparency_section += "\n⚠️ **Motivo**: Especialistas não encontraram informações específicas"
        transparency_section += "\n🎯 **Coordenado por**: Sistema TI Hierárquico"
        transparency_section += "\n" + "="*60
        
        return result + transparency_section
    
    def get_hierarchy_stats(self) -> Dict:
        """Retorna estatísticas da hierarquia."""
        return {
            "sub_agents_count": len(self.sub_agents),
            "sub_agents": list(self.sub_agents.keys()),
            "rules_count": len(self.subspecialty_rules),
            "delegations_history": len(self.delegation_history),
            "recent_delegations": self.delegation_history[-5:] if self.delegation_history else []
        }
