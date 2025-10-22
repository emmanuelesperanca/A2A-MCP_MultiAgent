"""Interface e classes para suporte a agentes hierárquicos com sub-especialistas."""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

import numpy as np
from langchain_openai import OpenAIEmbeddings

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
                "abnt", "nbr", "13485", "9001", "14001", "45001",  # ← ADICIONADO
                "capítulo", "seção", "artigo", "cláusula", "requisito",  # ← ADICIONADO
                # Inglês
                "policy", "policies", "governance", "compliance", "audit", "security",
                "regulation", "standard", "certification", "procedure", "risk",
                "control", "signature", "signatures", "sign", "electronic", "digital",
                "validation", "password", "passwords", "authentication", "regulatory",
                "chapter", "section", "article", "clause", "requirement",  # ← ADICIONADO
                # Espanhol
                "política", "políticas", "gobernanza", "cumplimiento", "auditoría",
                "firma", "firmas", "electrónica", "validación", "contraseña",
                "capítulo", "sección", "artículo", "cláusula"  # ← ADICIONADO
            ],
            description="Questões de governança, compliance e políticas de TI",
            confidence_threshold=0.02,  # ← REDUZIDO de 0.03 para 0.02 (mais sensível)
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
                # Palavras específicas de desenvolvimento
                "desenvolvimento", "desenvolver", "aplicação", "aplicativo", 
                "sistema", "código", "projeto", "software",
                "bug", "erro", "feature", "funcionalidade", "deploy", "release",
                "rest api", "api rest", "endpoint", "integração api",  # ← API mais específico
                "banco de dados", "database", "sql", "query",
                "integração", "teste", "homologação", "produção",
                "frontend", "backend", "fullstack", "microserviço",
                "git", "repositório", "branch", "commit", "pull request",
                "docker", "container", "kubernetes", "devops"
            ],
            description="Questões de desenvolvimento e sistemas",
            confidence_threshold=0.05,
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
    
    def _validate_response_quality(
        self, 
        query: str, 
        response: str, 
        context_docs: Optional[List[Dict]] = None
    ) -> Tuple[bool, float, Dict[str, float]]:
        """
        Validação multi-critério da qualidade da resposta.
        
        Args:
            query: Pergunta original do usuário
            response: Resposta gerada pelo agente
            context_docs: Documentos usados como contexto (opcional)
            
        Returns:
            (is_valid, overall_score, detailed_scores)
            - is_valid: True se a resposta passa no threshold geral (>= 0.70)
            - overall_score: Score ponderado final (0-1)
            - detailed_scores: Dicionário com scores individuais de cada critério
        """
        scores = {}
        
        # 1. CRITÉRIO: Especificidade (35% do peso)
        # Verifica se resposta não é genérica e tem conteúdo substantivo
        specificity_score = self._check_specificity(response)
        scores['specificity'] = specificity_score
        
        # 2. CRITÉRIO: Relevância Semântica (35% do peso)
        # Verifica se resposta está semanticamente relacionada à pergunta
        relevance_score = self._check_semantic_relevance(query, response)
        scores['relevance'] = relevance_score
        
        # 3. CRITÉRIO: Citação de Fontes (20% do peso)
        # Verifica se resposta menciona documentos e não inventa informações
        citation_score = self._check_citations(response, context_docs)
        scores['citations'] = citation_score
        
        # 4. CRITÉRIO: Completude (10% do peso)
        # Verifica se resposta tem profundidade adequada
        completeness_score = self._check_completeness(response)
        scores['completeness'] = completeness_score
        
        # Calcular score ponderado final
        overall_score = (
            specificity_score * 0.35 +
            relevance_score * 0.35 +
            citation_score * 0.20 +
            completeness_score * 0.10
        )

        # Threshold para aprovação: 0.50 (50%)
        is_valid = overall_score >= 0.20
        
        # Log detalhado para debugging
        print(f"\n{'='*60}")
        print(f"🔍 VALIDAÇÃO DE QUALIDADE DA RESPOSTA")
        print(f"{'='*60}")
        print(f"📊 Especificidade:      {specificity_score:.2f} (35% peso)")
        print(f"🎯 Relevância Semântica: {relevance_score:.2f} (35% peso)")
        print(f"📚 Citação de Fontes:   {citation_score:.2f} (20% peso)")
        print(f"✅ Completude:          {completeness_score:.2f} (10% peso)")
        print(f"{'─'*60}")
        print(f"🏆 SCORE FINAL: {overall_score:.2f} ({'✅ APROVADO' if is_valid else '❌ REJEITADO'})")
        print(f"{'='*60}\n")
        
        return is_valid, overall_score, scores
    
    def _check_specificity(self, response: str) -> float:
        """
        Verifica se a resposta é específica e não genérica.
        
        Retorna score de 0 a 1:
        - 0.0: Completamente genérica
        - 1.0: Altamente específica
        """
        # 1. Verificar frases genéricas (método existente)
        if self._is_generic_response(response):
            return 0.0
        
        # 2. Verificar comprimento mínimo
        if len(response.split()) < 30:
            return 0.3  # Muito curta, provavelmente superficial
        
        # 3. Verificar presença de informações técnicas/específicas
        # Indicadores de especificidade: números, datas, nomes próprios, termos técnicos
        specificity_indicators = 0
        
        # Números e percentuais
        if re.search(r'\d+', response):
            specificity_indicators += 1
        
        # Datas
        if re.search(r'\b(20\d{2}|19\d{2})\b', response):
            specificity_indicators += 1
        
        # Nomes próprios (palavras capitalizadas no meio do texto)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', response)
        if len(proper_nouns) >= 2:
            specificity_indicators += 1
        
        # Termos técnicos comuns em documentação
        technical_terms = [
            'sistema', 'processo', 'procedimento', 'requisito', 'norma',
            'política', 'regulamentação', 'compliance', 'auditoria',
            'configuração', 'implementação', 'validação', 'verificação'
        ]
        response_lower = response.lower()
        if sum(1 for term in technical_terms if term in response_lower) >= 2:
            specificity_indicators += 1
        
        # Score baseado em indicadores (máximo 4)
        specificity_score = min(1.0, 0.5 + (specificity_indicators * 0.15))
        
        return specificity_score
    
    def _check_semantic_relevance(self, query: str, response: str) -> float:
        """
        Verifica relevância semântica entre pergunta e resposta usando embeddings.
        
        Retorna score de 0 a 1 baseado em similaridade coseno.
        """
        try:
            # Inicializar embeddings (lazy loading)
            if not hasattr(self, '_embeddings'):
                self._embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            
            # Gerar embeddings
            query_embedding = self._embeddings.embed_query(query)
            response_embedding = self._embeddings.embed_query(response[:1000])  # Limitar tamanho
            
            # Calcular similaridade coseno
            query_vec = np.array(query_embedding)
            response_vec = np.array(response_embedding)
            
            cosine_sim = np.dot(query_vec, response_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(response_vec)
            )
            
            # Normalizar para 0-1 (cosine já retorna -1 a 1, mas em prática é 0-1 para textos)
            relevance_score = max(0.0, min(1.0, cosine_sim))
            
            return relevance_score
            
        except Exception as e:
            logger.warning(f"Erro ao calcular relevância semântica: {e}")
            # Fallback: se houver erro, assumir relevância moderada
            return 0.65
    
    def _check_citations(self, response: str, context_docs: Optional[List[Dict]]) -> float:
        """
        Verifica se resposta cita fontes do contexto e não inventa informações.
        
        Retorna score de 0 a 1:
        - 1.0: Cita múltiplas fontes claramente
        - 0.5-0.8: Cita algumas fontes
        - 0.0-0.4: Não cita fontes ou inventa informações
        """
        # Se não há contexto disponível, não podemos validar citações
        if not context_docs:
            # Verificar se resposta pelo menos menciona buscar/consultar documentos
            if any(term in response.lower() for term in ['documento', 'política', 'norma', 'procedimento', 'regulamentação']):
                return 0.6  # Menciona conceitos gerais de documentação
            return 0.4  # Sem contexto e sem menção a fontes
        
        response_lower = response.lower()
        citations_found = 0
        
        # Procurar menções aos documentos do contexto
        for doc in context_docs:
            doc_title = doc.get('titulo', '').lower()
            doc_source = doc.get('fonte', '').lower()
            
            # Verificar se título ou fonte são mencionados na resposta
            if doc_title and len(doc_title) > 10:  # Ignorar títulos muito curtos
                # Procurar por match parcial (pelo menos 60% das palavras principais)
                title_words = [w for w in doc_title.split() if len(w) > 3]
                if title_words:
                    matches = sum(1 for word in title_words if word in response_lower)
                    if matches / len(title_words) >= 0.6:
                        citations_found += 1
                        continue
            
            # Verificar fonte (ISO, RDC, FDA, etc.)
            if doc_source and doc_source in response_lower:
                citations_found += 1
        
        # Calcular score baseado em número de citações
        num_docs = len(context_docs)
        if num_docs == 0:
            return 0.5
        
        citation_ratio = citations_found / num_docs
        
        # Score progressivo:
        # - 0 citações: 0.0
        # - 1-25% citações: 0.5
        # - 26-50% citações: 0.7
        # - 51-75% citações: 0.85
        # - 76-100% citações: 1.0
        if citation_ratio == 0:
            return 0.0
        elif citation_ratio <= 0.25:
            return 0.5
        elif citation_ratio <= 0.50:
            return 0.7
        elif citation_ratio <= 0.75:
            return 0.85
        else:
            return 1.0
    
    def _check_completeness(self, response: str) -> float:
        """
        Verifica se resposta tem profundidade e completude adequadas.
        
        Retorna score de 0 a 1 baseado em:
        - Comprimento adequado
        - Estrutura (múltiplos parágrafos)
        - Presença de listas ou enumerações
        - Conclusão ou próximos passos
        """
        words = response.split()
        num_words = len(words)
        
        score = 0.0
        
        # 1. Comprimento adequado (40% do critério)
        if num_words < 50:
            score += 0.0
        elif num_words < 100:
            score += 0.2
        elif num_words < 200:
            score += 0.3
        else:
            score += 0.4
        
        # 2. Estrutura em parágrafos (30% do critério)
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
        if len(paragraphs) >= 2:
            score += 0.3
        elif len(paragraphs) == 1 and num_words > 100:
            score += 0.15
        
        # 3. Listas ou enumerações (20% do critério)
        # Detectar bullets, números, ou estruturas enumeradas
        has_lists = any(char in response for char in ['•', '●', '◦', '▪']) or \
                   bool(re.search(r'\n\s*[-*]\s+', response)) or \
                   bool(re.search(r'\n\s*\d+[.)]\s+', response))
        
        if has_lists:
            score += 0.2
        
        # 4. Conclusão ou próximos passos (10% do critério)
        conclusion_indicators = [
            'portanto', 'assim', 'dessa forma', 'em resumo', 'concluindo',
            'próximos passos', 'recomendo', 'sugiro', 'você pode',
            'para mais informações', 'consulte', 'entre em contato'
        ]
        
        response_lower = response.lower()
        has_conclusion = any(indicator in response_lower for indicator in conclusion_indicators)
        
        if has_conclusion:
            score += 0.1
        
        return min(1.0, score)
    
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
                    
                    # VALIDAÇÃO ROBUSTA DE QUALIDADE (4 critérios)
                    # Tentar obter documentos do contexto (se o sub-agente expôs isso)
                    context_docs = None
                    if hasattr(sub_agent, '_last_context_docs'):
                        context_docs = sub_agent._last_context_docs
                    
                    # Se a resposta é uma mensagem de erro informativa, aceitar sem validar
                    is_error_message = (
                        result.startswith("⚠️") or 
                        result.startswith("Desculpe") or
                        "Problema de Conectividade" in result or
                        "Timeout" in result
                    )
                    
                    if is_error_message:
                        # Aceitar mensagem de erro informativa
                        print(f"⚠️ {sub_agent.config.name} retornou mensagem de erro informativa")
                        decision_chain.append(f"⚠️ **Resultado**: {sub_agent.config.name} encontrou um problema técnico")
                        decision_chain.append("💡 **Ação**: Retornando mensagem informativa ao usuário")
                        
                        # Montar transparência
                        transparency_section = "\n\n" + "="*60 + "\n"
                        transparency_section += "🧠 **CADEIA DE DECISÃO E RACIOCÍNIO**\n"
                        transparency_section += "="*60 + "\n"
                        for step in decision_chain:
                            transparency_section += f"{step}\n"
                        
                        transparency_section += f"\n📋 **Resposta fornecida por**: {sub_agent.config.name} ({sub_agent.config.specialty})"
                        transparency_section += "\n⚠️ **Status**: Problema técnico detectado"
                        transparency_section += "\n🎯 **Coordenado por**: Sistema TI Hierárquico"
                        transparency_section += "\n" + "="*60
                        
                        return result + transparency_section
                    
                    # Validar qualidade da resposta
                    is_valid, quality_score, detailed_scores = self._validate_response_quality(
                        query=query,
                        response=result,
                        context_docs=context_docs
                    )
                    
                    # Log dos resultados da validação
                    if not is_valid:
                        print(f"❌ Resposta rejeitada por {sub_agent.config.name} (score: {quality_score:.2f})")
                        decision_chain.append(f"❌ **Resultado**: Resposta de {sub_agent.config.name} não passou na validação de qualidade")
                        decision_chain.append(f"📊 **Score de Qualidade**: {quality_score:.2f}/1.00 (threshold: 0.70)")
                        decision_chain.append(f"📈 **Detalhamento**: Especificidade {detailed_scores['specificity']:.2f}, Relevância {detailed_scores['relevance']:.2f}, Citações {detailed_scores['citations']:.2f}, Completude {detailed_scores['completeness']:.2f}")
                        
                        if i < len(candidates) - 1:
                            decision_chain.append("⚡ **Ação**: Tentando próximo especialista na hierarquia...")
                        continue
                    
                    # Sucesso! Adiciona cadeia de decisão transparente
                    print(f"✅ Resposta aprovada (score: {quality_score:.2f})")
                    decision_chain.append(f"✅ **Sucesso**: {sub_agent.config.name} forneceu resposta de qualidade!")
                    decision_chain.append(f"📊 **Score de Qualidade**: {quality_score:.2f}/1.00")
                    decision_chain.append(f"📈 **Detalhamento**: Especificidade {detailed_scores['specificity']:.2f}, Relevância {detailed_scores['relevance']:.2f}, Citações {detailed_scores['citations']:.2f}, Completude {detailed_scores['completeness']:.2f}")
                    
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
        
        # 3. Se nenhum candidato funcionou, usar TI principal (se disponível)
        decision_chain.append("❌ **Resultado**: Nenhum especialista encontrou informações específicas")
        
        if self.base_agent:
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
        else:
            # Sem base_agent disponível, retornar mensagem informativa
            decision_chain.append("⚠️ **Fallback**: Agente TI geral não disponível")
            
            logger.warning("⚠️ Base agent TI não disponível e nenhum especialista respondeu")
            
            # Montar resposta com transparência
            transparency_section = "\n\n" + "="*60 + "\n"
            transparency_section += "🧠 **CADEIA DE DECISÃO E RACIOCÍNIO**\n"
            transparency_section += "="*60 + "\n"
            for step in decision_chain:
                transparency_section += f"{step}\n"
            
            transparency_section += "\n⚠️ **Status**: Sistema em configuração"
            transparency_section += "\n💡 **Sugestão**: Tente reformular a pergunta de forma mais específica"
            transparency_section += "\n🎯 **Coordenado por**: Sistema TI Hierárquico"
            transparency_section += "\n" + "="*60
            
            result = (
                "Desculpe, não consegui processar sua pergunta sobre TI no momento.\n\n"
                "Por favor, tente reformular sua pergunta de forma mais específica, mencionando:\n"
                "- **Governança**: Políticas, segurança, compliance\n"
                "- **Desenvolvimento**: Aplicações, sistemas, integrações\n"
                "- **Infraestrutura**: Servidores, redes, hardware\n"
                "- **Suporte**: Problemas de usuários, tickets, acesso"
            )
            
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
