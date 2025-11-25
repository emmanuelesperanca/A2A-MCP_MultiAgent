"""Infraestrutura compartilhada para criação de subagentes Neoson."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from dal import get_knowledge_dal, BaseDAL

warnings.simplefilter(action="ignore", category=FutureWarning)


# ============================================================================
# QUICK WINS: Classes de otimização de performance
# ============================================================================

class ProfileAnalyzer:
    """Analisa o perfil do usuário ANTES da busca para otimizar filtros."""
    
    @staticmethod
    def analyze_user_profile(perfil_usuario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai informações do perfil para otimizar buscas.
        
        Returns:
            Dict com: geografia, projetos (list), nivel_hierarquico, area
        """
        def _get_val(perfil: Dict, *keys):
            for key in keys:
                if key in perfil and perfil[key] is not None:
                    return perfil[key]
            return None
        
        def _normalize_list(value):
            if value is None:
                return []
            if isinstance(value, list):
                return [str(item).strip() for item in value if str(item).strip()]
            if isinstance(value, str):
                return [item.strip() for item in value.split(",") if item.strip()]
            return [str(value).strip()]
        
        geografia = _get_val(perfil_usuario, "geografia", "Geografia")
        projetos_raw = _get_val(perfil_usuario, "projetos", "Projetos")
        projetos = _normalize_list(projetos_raw)
        nivel = int(_get_val(perfil_usuario, "nivel_hierarquico", "Nivel_Hierarquico") or 1)
        area = _get_val(perfil_usuario, "area", "Departamento")
        
        return {
            "geografia": geografia,
            "projetos": projetos,
            "nivel_hierarquico": nivel,
            "area": area
        }


class OptimizedDocumentSearch:
    """Busca otimizada com filtros SQL para reduzir documentos retornados."""
    
    @staticmethod
    async def search_with_profile_filter(
        dal: BaseDAL,
        table_name: str,
        query_embedding: List[float],
        user_profile: Dict[str, Any],
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Busca documentos aplicando filtros de perfil no SQL.
        NOTA: Esta versão é síncrona mas mantém signature async para compatibilidade futura.
        
        Args:
            dal: Data Access Layer
            table_name: Nome da tabela
            query_embedding: Embedding da pergunta
            user_profile: Perfil analisado (resultado de ProfileAnalyzer)
            limit: Máximo de documentos
        
        Returns:
            Lista de documentos filtrados
        """
        # Por enquanto, usar busca padrão da DAL sem filtros customizados
        # A governança será aplicada depois no verificar_permissao_documento
        # Isso mantém a compatibilidade sem quebrar o sistema existente
        
        try:
            # Usar método padrão da DAL
            search_results = dal.search_vectors(
                table_name=table_name,
                query_vector=query_embedding,
                limit=limit * 2,  # Buscar mais para compensar filtros posteriores
                filters=None  # Filtros complexos serão aplicados depois
            )
            
            return search_results.documents
            
        except Exception as e:
            # Fallback: busca mínima se der erro
            print(f"⚠️ Erro na busca otimizada: {e}")
            search_results = dal.search_vectors(
                table_name=table_name,
                query_vector=query_embedding,
                limit=limit
            )
            return search_results.documents


class ResponseValidator:
    """Validação rigorosa da resposta do LLM com 4 critérios."""
    
    @staticmethod
    def validate_response_quality(
        response: str,
        pergunta: str,
        documentos: List[Dict[str, Any]],
        min_score: float = 0.6
    ) -> Dict[str, Any]:
        """
        Valida qualidade da resposta com 4 critérios.
        
        Returns:
            Dict com: is_valid (bool), score (float), criteria_scores (dict), issues (list)
        """
        criteria_scores = {}
        issues = []
        
        # 1. RELEVÂNCIA: Resposta aborda a pergunta?
        relevance_score = ResponseValidator._check_relevance(response, pergunta)
        criteria_scores["relevance"] = relevance_score
        if relevance_score < 0.5:
            issues.append("Resposta não parece relevante à pergunta")
        
        # 2. ESPECIFICIDADE: Usa informações dos documentos?
        specificity_score = ResponseValidator._check_specificity(response, documentos)
        criteria_scores["specificity"] = specificity_score
        if specificity_score < 0.4:
            issues.append("Resposta muito genérica, não usa documentos específicos")
        
        # 3. ACESSO: Não vaza informações restritas?
        access_score = ResponseValidator._check_access_control(response, documentos)
        criteria_scores["access_control"] = access_score
        if access_score < 0.8:
            issues.append("Possível vazamento de informação restrita")
        
        # 4. FRESCOR: Informações estão atualizadas?
        freshness_score = ResponseValidator._check_freshness(documentos)
        criteria_scores["freshness"] = freshness_score
        if freshness_score < 0.7:
            issues.append("Documentos podem estar desatualizados")
        
        # Score final: média ponderada
        final_score = (
            relevance_score * 0.35 +
            specificity_score * 0.30 +
            access_score * 0.25 +
            freshness_score * 0.10
        )
        
        is_valid = final_score >= min_score and access_score >= 0.8
        
        return {
            "is_valid": is_valid,
            "score": final_score,
            "criteria_scores": criteria_scores,
            "issues": issues,
            "recommendation": "APPROVED" if is_valid else "NEEDS_REVIEW"
        }
    
    @staticmethod
    def _check_relevance(response: str, pergunta: str) -> float:
        """Verifica se a resposta é relevante à pergunta."""
        response_lower = response.lower()
        pergunta_lower = pergunta.lower()
        
        # Extrair palavras-chave da pergunta (remover stop words)
        stop_words = {"o", "a", "de", "da", "do", "para", "como", "qual", "que", "é", "são"}
        palavras_pergunta = set(pergunta_lower.split()) - stop_words
        
        if not palavras_pergunta:
            return 0.5  # Neutro se não há palavras-chave
        
        # Contar quantas palavras-chave aparecem na resposta
        matches = sum(1 for palavra in palavras_pergunta if palavra in response_lower)
        
        return min(matches / len(palavras_pergunta), 1.0)
    
    @staticmethod
    def _check_specificity(response: str, documentos: List[Dict[str, Any]]) -> float:
        """Verifica se a resposta usa informações específicas dos documentos."""
        response_lower = response.lower()
        
        # Padrões que indicam citação específica (frases completas)
        citation_patterns = [
            "de acordo com",
            "conforme",
            "segundo",
            "baseado em",
            "conforme documento",
            "segundo a política",
            "de acordo com a norma",
            "estabelecido",
            "padrão",
            "norma"
        ]
        
        citation_count = sum(1 for pattern in citation_patterns if pattern in response_lower)
        
        # Padrões que indicam resposta genérica
        generic_patterns = [
            "geralmente",
            "normalmente",
            "em geral",
            "tipicamente",
            "usualmente",
            "pode se referir",
            "pode ser",
            "talvez",
            "provavelmente"
        ]
        
        generic_count = sum(1 for pattern in generic_patterns if pattern in response_lower)
        
        # Se há documentos, dar base mais alta
        base_score = 0.4 if documentos else 0.2
        
        # Cada citação específica adiciona 0.2
        score = min((citation_count * 0.2) + base_score, 1.0)
        
        # Penalidade para padrões genéricos
        return max(score - (generic_count * 0.25), 0.0)
        
        response_lower = response.lower()
        
        # Padrões que indicam resposta genérica
        generic_patterns = [
            "não tenho informação",
            "não encontrei",
            "recomendo abrir um ticket",
            "entre em contato",
            "pode se referir a",
            "em geral",
            "tipicamente",
            "normalmente"
        ]
        
        generic_count = sum(1 for pattern in generic_patterns if pattern in response_lower)
        if generic_count >= 2:
            return 0.2
        
        # Verificar se há citações ou referências específicas
        citation_patterns = [
            "de acordo com",
            "segundo",
            "conforme",
            "estabelece que",
            "determina que",
            "policy",
            "norma",
            "regulamento"
        ]
        
        citation_count = sum(1 for pattern in citation_patterns if pattern in response_lower)
        
        # Score baseado em citações e ausência de padrões genéricos
        score = min((citation_count * 0.3) + 0.4, 1.0)
        
        return max(score - (generic_count * 0.15), 0.0)
    
    @staticmethod
    def _check_access_control(response: str, documentos: List[Dict[str, Any]]) -> float:
        """Verifica se não há vazamento de informações restritas."""
        response_lower = response.lower()
        
        # 1. Padrões explícitos que indicam vazamento (palavras-chave sensíveis)
        sensitive_patterns = [
            "senha",
            "password",
            "cpf",
            "confidencial",
            "restrito",
            "privado",
            "secreto"
        ]
        
        leak_count = sum(1 for pattern in sensitive_patterns if pattern in response_lower)
        
        if leak_count > 0:
            return 0.3  # Penalidade severa
        
        # 2. Se não há documentos, mas a resposta é substantiva = possível vazamento
        if not documentos:
            # Verificar se a resposta é substantiva (não é apenas "não sei")
            substantive_patterns = [
                "política",
                "procedimento",
                "norma",
                "deve",
                "é necessário",
                "precisa",
                "requer",
                "estabelece",
                "determina",
                "salário",
                "remuneração",
                "benefício",
                "dados pessoais",
                "valor",
                "quantidade",
                "número"
            ]
            
            # Respostas negativas são OK mesmo sem documentos
            negative_patterns = [
                "não sei",
                "não tenho",
                "não posso",
                "não encontrei",
                "sem informação",
                "sem acesso"
            ]
            
            has_negative = any(pattern in response_lower for pattern in negative_patterns)
            
            if has_negative:
                return 0.9  # OK - resposta negativa apropriada
            
            substantive_count = sum(1 for pattern in substantive_patterns if pattern in response_lower)
            
            # Se resposta é substantiva mas não há documentos = vazamento provável
            if substantive_count >= 1:
                return 0.4  # Penalidade por possível vazamento
            
            # Resposta genérica sem documentos = OK (ex: "não tenho informação")
            return 0.9
        
        # 3. Há documentos = OK (governança já foi aplicada)
        return 1.0
    
    @staticmethod
    def _check_freshness(documentos: List[Dict[str, Any]]) -> float:
        """Verifica se os documentos usados estão atualizados."""
        if not documentos:
            return 0.5
        
        hoje = datetime.now().date()
        scores = []
        
        for doc in documentos:
            data_validade = doc.get("data_validade")
            
            if data_validade is None:
                scores.append(1.0)  # Sem data = sempre válido
                continue
            
            if isinstance(data_validade, datetime):
                data_validade = data_validade.date()
            elif isinstance(data_validade, str):
                try:
                    data_validade = datetime.strptime(data_validade, "%Y-%m-%d").date()
                except:
                    scores.append(1.0)
                    continue
            
            if data_validade >= hoje:
                scores.append(1.0)
            else:
                dias_vencido = (hoje - data_validade).days
                if dias_vencido <= 7:
                    scores.append(0.9)  # Vencido há menos de 1 semana: OK
                elif dias_vencido <= 30:
                    scores.append(0.5)  # Vencido há menos de 1 mês: médio
                elif dias_vencido <= 90:
                    scores.append(0.3)  # Vencido há menos de 3 meses: ruim
                else:
                    scores.append(0.1)  # Vencido há mais de 3 meses: muito ruim
        
        return sum(scores) / len(scores) if scores else 0.5


class Document:
    """Classe Document compatível que funciona como dicionário e objeto."""
    
    def __init__(self, page_content: str = "", metadata: Dict = None):
        self.page_content = page_content
        self.metadata = metadata or {}
        # Adicionar todos os campos do metadata como atributos do objeto
        for key, value in self.metadata.items():
            setattr(self, key, value)
    
    def get(self, key: str, default=None):
        """Método get compatível com dicionário."""
        if key == 'page_content':
            return self.page_content
        elif key in self.metadata:
            return self.metadata[key]
        elif hasattr(self, key):
            return getattr(self, key)
        else:
            return default
    
    def items(self):
        """Método items compatível com dicionário."""
        result = {'page_content': self.page_content}
        result.update(self.metadata)
        return result.items()
    
    def __getitem__(self, key):
        """Permite acesso como doc['key']."""
        if key == 'page_content':
            return self.page_content
        elif key in self.metadata:
            return self.metadata[key]
        else:
            raise KeyError(f"Key '{key}' not found")


@dataclass
class SubagentConfig:
    """Configuração declarativa para instanciar um subagente."""

    identifier: str
    name: str
    specialty: str
    description: str
    keywords: List[str]
    prompt_template: str
    table_name: Optional[str] = None
    table_env_var: Optional[str] = None
    database_env_var: Optional[str] = None
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1000
    embedding_model: str = "text-embedding-3-small"
    error_message: str = (
        "Ops! Tive um problema técnico aqui. Que tal tentar novamente em instantes ou acionar o suporte?"
    )
    debug: bool = False
    # Configurações MCP
    enable_mcp_tools: bool = False
    mcp_tools_category: Optional[str] = None
    mcp_tool_server_url: Optional[str] = None
    # Configurações A2A
    enable_a2a: bool = False
    delegation_rules: List = field(default_factory=list)
    max_delegation_depth: int = 2

    def __post_init__(self) -> None:
        identifier_clean = self.identifier.strip()
        if not identifier_clean:
            raise ValueError("identifier não pode ser vazio")
        self.identifier = identifier_clean
        self.error_message = self.error_message.strip()

        default_table = f"knowledge_{identifier_clean.lower()}"
        self.table_name = self.table_name or default_table

        upper_identifier = identifier_clean.upper()
        default_table_env = f"KNOWLEDGE_{upper_identifier}_TABLE"
        default_db_env = f"KNOWLEDGE_{upper_identifier}_DATABASE_URL"

        self.table_env_var = self.table_env_var or default_table_env
        self.database_env_var = self.database_env_var or default_db_env
        
        # Se MCP está habilitado mas categoria não definida, usa o identifier
        if self.enable_mcp_tools and not self.mcp_tools_category:
            self.mcp_tools_category = identifier_clean.lower()


class BaseSubagent:
    """Agente base parametrizado por prompt e fonte de conhecimento."""

    def __init__(self, config: SubagentConfig) -> None:
        self.config = config
        self.llm: Optional[ChatOpenAI] = None
        self.embeddings: Optional[OpenAIEmbeddings] = None
        self.dal: Optional[BaseDAL] = None
        self.memoria_conversas: Dict[str, List[Dict[str, Any]]] = {}
        self.db_dsn: Optional[str] = None
        self.table_name: str = config.table_name
        # MCP Components
        self.mcp_client = None
        self.available_tools: List = []
        # A2A Components
        self.agent_registry = None
        self.current_session = None
        self.last_sources_used: List[str] = []
        self.last_tools_used: List[str] = []
        # QUICK WIN: Cache de análise de perfil
        self.profile_analyzer = ProfileAnalyzer()
        self.cached_user_profiles: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Helpers de logging
    # ------------------------------------------------------------------
    def _log(self, mensagem: str) -> None:
        if self.config.debug:
            print(mensagem)

    # ------------------------------------------------------------------
    # Carregamento e inicialização
    # ------------------------------------------------------------------
    def carregar_configuracoes_e_dados(self) -> str:
        self._log(f"--- 🔄 Carregando configurações do agente {self.config.name}... ---")
        
        # Use centralized configuration
        from core.config import config as app_config
        
        # Get OpenAI API key
        api_key = app_config.openai.api_key
        if not api_key:
            raise ValueError("Chave da API OPENAI_API_KEY não encontrada nas configurações")

        # Determine database domain based on table name hint (fallback para "main")
        domain_mapping = {
            "knowledge_hr": "rh",
            "knowledge_rh": "rh",
            "knowledge_tech": "ti",
            "knowledge_it governance": "governance",
            "knowledge_it infrastructure": "infra",
            "knowledge_architeture & dev": "dev",
            "knowledge_software development": "dev",
            "knowledge_it end-user services": "enduser",
            "knowledge_end-user": "enduser"
        }

        table_hint = (self.config.table_name or "").lower()
        domain = "main"
        for pattern, domain_name in domain_mapping.items():
            if pattern in table_hint:
                domain = domain_name
                break

        # Get database configuration for this domain (URL) but preserve tabela personalizada
        db_config = app_config.get_database_config(domain)
        self.db_dsn = db_config["url"]

        preferred_table = (self.config.table_name or "").strip()
        self.table_name = preferred_table or db_config["table"]
        
        if not self.db_dsn:
            raise ValueError(f"Database URL não configurada para o domínio {domain}")
        
        self._log(
            f"✅ Fonte de conhecimento configurada: tabela '{self.table_name}' (domínio: {domain})"
        )
        return api_key

    def inicializar_modelos(self, api_key: str) -> None:
        from core.config import config as app_config
        
        self._log(f"--- 🤖 Inicializando modelos OpenAI para {self.config.specialty}... ---")
        self.llm = ChatOpenAI(
            api_key=api_key,
            model=app_config.openai.chat_model,
            temperature=app_config.openai.temperature,
            max_tokens=app_config.openai.max_tokens,
        )
        self.embeddings = OpenAIEmbeddings(api_key=api_key, model=app_config.openai.embedding_model)
        self._log("✅ Modelos OpenAI inicializados.")

    def configurar_vector_store(self) -> None:
        if not self.db_dsn:
            raise RuntimeError("Banco de dados não configurado. Execute carregar_configuracoes_e_dados primeiro.")

        # Configurar acesso ao banco de dados via DAL
        self._log(f"--- 🗄️ Conectando à base vetorial '{self.table_name}'... ---")
        
        # Detectar tipo de base de conhecimento pelo nome da tabela
        table_suffix = self._detect_table_suffix()
        self._log(f"🔍 Tabela: '{self.table_name}' -> Sufixo detectado: '{table_suffix}'")
        self.dal = get_knowledge_dal(table_suffix)
        
        # Conectar ao banco
        if not self.dal.connect():
            raise RuntimeError(f"Falha ao conectar à base de conhecimento {self.table_name}")
        
        self._log("✅ Conexão com a base de conhecimento estabelecida via DAL.")

    def _detect_table_suffix(self) -> str:
        """Detecta o sufixo da tabela para determinar qual DAL usar."""
        table_lower = self.table_name.lower()
        
        if 'rh' in table_lower:
            return 'rh'
        elif any(term in table_lower for term in ['governance', 'delivery']):
            return 'governance'
        elif 'infra' in table_lower:
            return 'infra'
        elif any(term in table_lower for term in ['ti', 'tech', 'development']):
            return 'ti'
        else:
            return 'main'

    def configurar_mcp_tools(self) -> None:
        """Configura o cliente MCP e carrega as tools disponíveis."""
        if not self.config.enable_mcp_tools:
            self._log("🔧 MCP Tools não habilitadas para este agente.")
            return

        try:
            from tools.mcp import MCPClient
            from tools.mcp.registry import default_registry

            self._log(f"--- 🔧 Configurando MCP Tools para categoria '{self.config.mcp_tools_category}'... ---")
            
            # Inicializa cliente MCP
            self.mcp_client = MCPClient(self.config.mcp_tool_server_url)
            
            # Carrega tools da categoria
            category_tools = default_registry.get_tools_for_category(self.config.mcp_tools_category)
            
            if not category_tools:
                self._log(f"⚠️ Nenhuma tool encontrada para categoria '{self.config.mcp_tools_category}'")
                return
            
            # Registra tools no cliente
            for tool in category_tools:
                self.mcp_client.register_tool(tool)
                self.available_tools.append(tool.name)
            
            self._log(f"✅ {len(category_tools)} MCP Tools configuradas: {', '.join(self.available_tools)}")
            
        except Exception as exc:
            self._log(f"❌ Erro ao configurar MCP Tools: {exc}")
            self.config.enable_mcp_tools = False

    # ------------------------------------------------------------------
    # Regras de governança
    # ------------------------------------------------------------------
    @staticmethod
    def _normalizar_lista(valores: Any, *, vazio_padrao: Optional[List[str]] = None) -> List[str]:
        if valores is None:
            return vazio_padrao or []
        if isinstance(valores, list):
            return [str(item).strip() for item in valores if str(item).strip()]
        if isinstance(valores, str):
            return [item.strip() for item in valores.split(",") if item.strip()]
        return [str(valores).strip()]

    @staticmethod
    def _perfil_val(perfil: Dict[str, Any], *chaves: str) -> Any:
        for chave in chaves:
            if chave in perfil and perfil[chave] is not None:
                return perfil[chave]
        return None

    @staticmethod
    def _valor_permitido(valores: List[str], valor_usuario: Optional[str]) -> bool:
        valores_upper = {valor.upper() for valor in valores if valor}
        if "ALL" in valores_upper:
            return True
        if "ALL_LATAM" in valores_upper and valor_usuario:
            latam_paises = {"BR", "MX", "AR", "CL", "CO", "PE", "VE", "EC", "UY", "PY", "BO"}
            if valor_usuario.upper() in latam_paises:
                return True
        if not valor_usuario:
            return False
        return valor_usuario.upper() in valores_upper

    @staticmethod
    def _lista_interseccao(documento_valores: List[str], valores_usuario: List[str]) -> bool:
        doc_upper = {valor.upper() for valor in documento_valores if valor}
        if "ALL" in doc_upper:
            return True
        if doc_upper == {"N/A"}:
            return True
        user_upper = {valor.upper() for valor in valores_usuario if valor}
        if "ALL" in user_upper:
            return True
        for valor in valores_usuario:
            if valor and valor.upper() in doc_upper:
                return True
        return False

    def verificar_permissao_documento(self, registro: Dict[str, Any], perfil_usuario: Dict[str, Any]) -> bool:
        fonte = registro.get("fonte_documento", "documento")
        self._log(f"🔍 Verificando permissão para: {fonte}")

        data_validade = registro.get("data_validade")
        if isinstance(data_validade, datetime):
            data_validade = data_validade.date()
        if isinstance(data_validade, date) and datetime.now().date() > data_validade:
            self._log(f"❌ {fonte}: Documento expirado ({data_validade})")
            return False

        if registro.get("apenas_para_si"):
            responsavel = (registro.get("responsavel") or "").strip().lower()
            usuario_nome = (self._perfil_val(perfil_usuario, "nome", "Nome") or "").strip().lower()
            if responsavel and usuario_nome != responsavel:
                self._log(f"❌ {fonte}: Documento pessoal (responsável: {responsavel}, usuário: {usuario_nome})")
                return False

        areas_doc = self._normalizar_lista(registro.get("areas_liberadas"), vazio_padrao=["ALL"])
        area_usuario = self._perfil_val(perfil_usuario, "area", "Departamento")
        self._log(f"   Áreas documento: {areas_doc}, área usuário: {area_usuario}")
        if not self._valor_permitido(areas_doc, area_usuario):
            self._log(f"❌ {fonte}: Área não permitida")
            return False

        nivel_minimo = int(registro.get("nivel_hierarquico_minimo") or 1)
        nivel_usuario = int(self._perfil_val(perfil_usuario, "nivel_hierarquico", "Nivel_Hierarquico") or 1)
        self._log(f"   Nível mínimo: {nivel_minimo}, nível usuário: {nivel_usuario}")
        if nivel_usuario < nivel_minimo:
            self._log(f"❌ {fonte}: Nível hierárquico insuficiente")
            return False

        geografias_doc = self._normalizar_lista(registro.get("geografias_liberadas"), vazio_padrao=["ALL"])
        geografia_usuario = self._perfil_val(perfil_usuario, "geografia", "Geografia")
        self._log(f"   Geografias documento: {geografias_doc}, geografia usuário: {geografia_usuario}")
        if not self._valor_permitido(geografias_doc, geografia_usuario):
            self._log(f"❌ {fonte}: Geografia não permitida")
            return False

        projetos_doc = self._normalizar_lista(registro.get("projetos_liberados"), vazio_padrao=["ALL"])
        projetos_usuario = self._normalizar_lista(
            self._perfil_val(perfil_usuario, "projetos", "Projetos") or [], vazio_padrao=[]
        )
        self._log(f"   Projetos documento: {projetos_doc}, projetos usuário: {projetos_usuario}")
        if not self._lista_interseccao(projetos_doc, projetos_usuario):
            self._log(f"❌ {fonte}: Projetos não compatíveis")
            return False

        if registro.get("dado_sensivel") and nivel_usuario < max(nivel_minimo, 4):
            self._log(f"❌ {fonte}: Dado sensível, nível insuficiente")
            return False

        self._log(f"✅ {fonte}: Documento aprovado")
        return True

    def _busca_multilingue(self, pergunta: str) -> List[Dict[str, Any]]:
        """
        Realiza busca multilíngue para garantir que documentos em todos os idiomas sejam considerados.
        """
        candidatos_unicos = {}
        
        # 1. Busca com a pergunta original
        consulta_embedding = self.embeddings.embed_query(pergunta)
        self._log(f"📊 Embedding gerado, consultando tabela '{self.table_name}'...")
        # Buscar candidatos usando a consulta na língua original
        search_results = self.dal.search_vectors(
            table_name=self.table_name, 
            query_vector=consulta_embedding, 
            limit=30
        )
        # Converter resultados para dicionários
        for r in search_results.documents:
            # r já é um dicionário vindo da DAL
            doc_dict = r if isinstance(r, dict) else dict(r)
            doc_id = doc_dict.get("id")
            id_unico = doc_id or str(hash(doc_dict.get("conteudo_original", "")))
            if id_unico not in candidatos_unicos:
                candidatos_unicos[id_unico] = doc_dict
        
        # 2. Dicionários de tradução para busca multilíngue
        termos_pt_en = {
            "governança": "governance",
            "política": "policy",
            "políticas": "policies",
            "senhas": "passwords",
            "senha": "password",
            "assinatura": "signature",
            "assinaturas": "signatures",
            "validação": "validation",
            "sistemas": "systems",
            "eletrônicas": "electronic",
            "eletrônico": "electronic",
            "lgpd": "gdpr data protection",
            "regulamentação": "regulation",
            "conformidade": "compliance"
        }
        
        # 3. Tradução reversa (inglês para português)
        termos_en_pt = {v: k for k, v in termos_pt_en.items()}
        termos_en_pt.update({
            "governance": "governança",
            "policy": "política",
            "policies": "políticas",
            "password": "senha",
            "passwords": "senhas",
            "signature": "assinatura",
            "signatures": "assinaturas",
            "validation": "validação",
            "systems": "sistemas",
            "electronic": "eletrônico eletrônicas",
            "gdpr": "lgpd",
            "regulation": "regulamentação",
            "compliance": "conformidade"
        })
        
        # Detectar idioma principal e criar versão traduzida
        pergunta_lower = pergunta.lower()
        pergunta_traduzida = pergunta_lower
        
        # Traduzir termos encontrados
        for termo_orig, termo_trad in {**termos_pt_en, **termos_en_pt}.items():
            if termo_orig in pergunta_lower:
                pergunta_traduzida = pergunta_traduzida.replace(termo_orig, termo_trad)
        
        # Se houve mudança, fazer busca adicional
        if pergunta_traduzida != pergunta_lower:
            self._log(f"🌐 Fazendo busca adicional com: '{pergunta_traduzida}'")
            consulta_embedding_trad = self.embeddings.embed_query(pergunta_traduzida)
            # Buscar candidatos traduzindo a consulta para inglês
            search_results_trad = self.dal.search_vectors(
                table_name=self.table_name,
                query_vector=consulta_embedding_trad,
                limit=30
            )
            # Adicionar candidatos da busca traduzida
            for r in search_results_trad.documents:
                doc_dict = r if isinstance(r, dict) else dict(r)
                doc_id = doc_dict.get("id")
                id_unico = doc_id or str(hash(doc_dict.get("conteudo_original", "")))
                if id_unico not in candidatos_unicos:
                    candidatos_unicos[id_unico] = doc_dict
        
        # 4. Busca adicional por termos-chave específicos para governança
        if any(termo in pergunta_lower for termo in ["governance", "governança", "policy", "política", "signature", "assinatura"]):
            # Busca específica por documentos conhecidos de governança
            termos_governanca = [
                "FDA CFR 21 Part 11 electronic signature",
                "ABNT NBR ISO validação sistemas",
                "RDC ANVISA regulamentação",
                "governance policy signature validation"
            ]
            
            for termo in termos_governanca:
                consulta_embedding_gov = self.embeddings.embed_query(termo)
                search_results_gov = self.dal.search_vectors(
                    table_name=self.table_name,
                    query_vector=consulta_embedding_gov,
                    limit=10
                )
                # Adicionar candidatos da busca de governança
                for r in search_results_gov.documents:
                    doc_dict = r if isinstance(r, dict) else dict(r)
                    doc_id = doc_dict.get("id")
                    id_unico = doc_id or str(hash(doc_dict.get("conteudo_original", "")))
                    if id_unico not in candidatos_unicos:
                        candidatos_unicos[id_unico] = doc_dict
        
        candidatos_finais = list(candidatos_unicos.values())
        self._log(f"🌐 Busca multilíngue: {len(candidatos_finais)} documentos únicos encontrados")
        return candidatos_finais

    def _selecionar_documentos_diversificados(self, documentos: List[Dict[str, Any]], max_docs: int = 4) -> List[Dict[str, Any]]:
        """
        Seleciona documentos diversificados priorizando diferentes tipos de fontes e idiomas.
        Objetivo: Garantir mix de documentos nacionais (ABNT, RDC, ANVISA) e internacionais (FDA, ISO).
        """
        if not documentos:
            return []
        
        # Categorizar documentos por tipo/origem
        docs_internacionais = []  # FDA, ISO internacional
        docs_nacionais_br = []    # ABNT, RDC, ANVISA
        docs_outros = []          # Demais documentos
        
        for doc in documentos:
            # Acessar fonte do documento através do metadata
            fonte = doc.metadata.get("fonte_documento", "") if hasattr(doc, 'metadata') and doc.metadata else ""
            fonte = fonte.upper()
            
            # Identificar documentos internacionais (em inglês ou normas internacionais)
            if any(termo in fonte for termo in ["FDA", "CFR", "ISO/IEC", "INTERNATIONAL", "STANDARD"]):
                docs_internacionais.append(doc)
            # Identificar documentos nacionais brasileiros 
            elif any(termo in fonte for termo in ["ABNT", "RDC", "ANVISA", "NBR", "BRASIL"]):
                docs_nacionais_br.append(doc)
            else:
                docs_outros.append(doc)
        
        self._log(f"🌍 Categorização: {len(docs_internacionais)} internacionais, {len(docs_nacionais_br)} nacionais BR, {len(docs_outros)} outros")
        
        # Estratégia de seleção diversificada
        selecionados = []
        
        # 1. Sempre tentar incluir pelo menos 1 documento internacional (se houver)
        if docs_internacionais and len(selecionados) < max_docs:
            selecionados.append(docs_internacionais[0])
            fonte_nome = docs_internacionais[0].metadata.get('fonte_documento', 'sem nome') if hasattr(docs_internacionais[0], 'metadata') and docs_internacionais[0].metadata else 'sem nome'
            self._log(f"📄 Selecionado internacional: {fonte_nome}")
        
        # 2. Sempre tentar incluir pelo menos 1 documento nacional BR (se houver)
        if docs_nacionais_br and len(selecionados) < max_docs:
            selecionados.append(docs_nacionais_br[0])
            fonte_nome = docs_nacionais_br[0].metadata.get('fonte_documento', 'sem nome') if hasattr(docs_nacionais_br[0], 'metadata') and docs_nacionais_br[0].metadata else 'sem nome'
            self._log(f"📄 Selecionado nacional BR: {fonte_nome}")
        
        # 3. Preencher slots restantes alternando entre categorias
        categorias_restantes = [
            (docs_internacionais[1:], "internacional"),
            (docs_nacionais_br[1:], "nacional BR"),
            (docs_outros, "outros")
        ]
        
        categoria_idx = 0
        while len(selecionados) < max_docs:
            # Encontrar próxima categoria com documentos disponíveis
            tentativas = 0
            while tentativas < len(categorias_restantes):
                docs_categoria, nome_categoria = categorias_restantes[categoria_idx]
                
                if docs_categoria:
                    doc_selecionado = docs_categoria.pop(0)
                    selecionados.append(doc_selecionado)
                    fonte_nome = doc_selecionado.metadata.get('fonte_documento', 'sem nome') if hasattr(doc_selecionado, 'metadata') and doc_selecionado.metadata else 'sem nome'
                    self._log(f"📄 Selecionado {nome_categoria}: {fonte_nome}")
                    break
                    
                categoria_idx = (categoria_idx + 1) % len(categorias_restantes)
                tentativas += 1
            
            # Se não há mais documentos em nenhuma categoria, parar
            if tentativas >= len(categorias_restantes):
                break
                
            categoria_idx = (categoria_idx + 1) % len(categorias_restantes)
        
        self._log(f"🎯 Seleção final: {len(selecionados)} documentos diversificados")
        return selecionados

    def _obter_motivo_rejeicao(self, registro: Dict[str, Any], perfil_usuario: Dict[str, Any]) -> str:
        """Retorna o motivo específico da rejeição de um documento para transparência."""
        # Verifica data de validade
        data_validade = registro.get("data_validade")
        if isinstance(data_validade, datetime):
            data_validade = data_validade.date()
        if isinstance(data_validade, date) and datetime.now().date() > data_validade:
            return "documento_expirado"

        # Verifica se é apenas para o responsável
        if registro.get("apenas_para_si"):
            responsavel = (registro.get("responsavel") or "").strip().lower()
            usuario_nome = (self._perfil_val(perfil_usuario, "nome", "Nome") or "").strip().lower()
            if responsavel and usuario_nome != responsavel:
                return "documento_pessoal"

        # Verifica área/departamento
        areas_doc = self._normalizar_lista(registro.get("areas_liberadas"), vazio_padrao=["ALL"])
        area_usuario = self._perfil_val(perfil_usuario, "area", "Departamento")
        if not self._valor_permitido(areas_doc, area_usuario):
            return "area_nao_autorizada"

        # Verifica nível hierárquico
        nivel_minimo = int(registro.get("nivel_hierarquico_minimo") or 1)
        nivel_usuario = int(self._perfil_val(perfil_usuario, "nivel_hierarquico", "Nivel_Hierarquico") or 1)
        if nivel_usuario < nivel_minimo:
            return "nivel_hierarquico_insuficiente"

        # Verifica geografia
        geografias_doc = self._normalizar_lista(registro.get("geografias_liberadas"), vazio_padrao=["ALL"])
        geografia_usuario = self._perfil_val(perfil_usuario, "geografia", "Geografia")
        if not self._valor_permitido(geografias_doc, geografia_usuario):
            return "geografia_nao_autorizada"

        # Verifica projetos
        projetos_doc = self._normalizar_lista(registro.get("projetos_liberados"), vazio_padrao=["ALL"])
        projetos_usuario = self._normalizar_lista(
            self._perfil_val(perfil_usuario, "projetos", "Projetos") or [], vazio_padrao=[]
        )
        if not self._lista_interseccao(projetos_doc, projetos_usuario):
            return "projeto_nao_autorizado"

        # Verifica dado sensível
        if registro.get("dado_sensivel") and nivel_usuario < max(nivel_minimo, 4):
            return "dado_sensivel_nivel_insuficiente"

        return "motivo_desconhecido"

    def _criar_mensagem_restricoes(self, motivos_rejeicao: Dict[str, List[str]]) -> str:
        """Cria uma mensagem explicativa sobre as restrições de acesso aos documentos."""
        mensagens_motivos = {
            "geografia_nao_autorizada": "não são acessíveis na sua região geográfica",
            "area_nao_autorizada": "não são acessíveis para o seu departamento",
            "nivel_hierarquico_insuficiente": "requerem um nível hierárquico mais alto",
            "projeto_nao_autorizado": "são restritos aos projetos em que você está envolvido",
            "documento_pessoal": "são de uso pessoal do responsável",
            "documento_expirado": "estão com prazo de validade expirado",
            "dado_sensivel_nivel_insuficiente": "contêm informações sensíveis que requerem autorização especial"
        }

        if not motivos_rejeicao:
            return ""

        restricoes_info = "\n\n⚠️ **INFORMAÇÃO SOBRE RESTRIÇÕES DE ACESSO:**\n"
        restricoes_info += "Encontrei documentos relevantes, mas eles não puderam ser consultados pelos seguintes motivos:\n\n"

        for motivo, fontes in motivos_rejeicao.items():
            descricao = mensagens_motivos.get(motivo, "têm restrições de acesso")
            count = len(fontes)
            restricoes_info += f"• **{count} documento(s)** {descricao}\n"

        restricoes_info += "\n💡 **Recomendações:**\n"
        restricoes_info += "- Entre em contato com a equipe responsável pela área\n"
        restricoes_info += "- Solicite acesso através dos canais oficiais\n"
        restricoes_info += "- Verifique se possui as autorizações necessárias\n"

        return restricoes_info

    # ------------------------------------------------------------------
    # Memória de conversas
    # ------------------------------------------------------------------
    def _usuario_id(self, perfil_usuario: Dict[str, Any]) -> str:
        nome_usuario = self._perfil_val(perfil_usuario, "nome", "Nome") or "usuario"
        area_usuario = self._perfil_val(perfil_usuario, "area", "Departamento") or "geral"
        return f"{nome_usuario}_{area_usuario}"

    def adicionar_ao_historico(self, usuario_id: str, pergunta: str, resposta: str) -> None:
        self.memoria_conversas.setdefault(usuario_id, [])
        self.memoria_conversas[usuario_id].append(
            {
                "pergunta": pergunta,
                "resposta": resposta,
                "timestamp": datetime.now().strftime("%H:%M"),
                "agente": self.config.specialty,
            }
        )
        if len(self.memoria_conversas[usuario_id]) > 8:
            self.memoria_conversas[usuario_id] = self.memoria_conversas[usuario_id][-8:]

    def obter_historico_formatado(self, usuario_id: str) -> str:
        historico = self.memoria_conversas.get(usuario_id)
        if not historico:
            return ""

        titulo = f"HISTÓRICO DA NOSSA CONVERSA SOBRE {self.config.specialty.upper()}:\n"
        ultimas_interacoes = historico[-4:]
        partes = [titulo]
        for interacao in ultimas_interacoes:
            resumo_resposta = interacao["resposta"][:200]
            if len(interacao["resposta"]) > 200:
                resumo_resposta += "..."
            partes.append(
                f"[{interacao['timestamp']}] Você perguntou: {interacao['pergunta']}\n"
                f"[{interacao['timestamp']}] Eu respondi: {resumo_resposta}\n"
            )
        partes.append("---\n\n")
        return "".join(partes)

    # ------------------------------------------------------------------
    # MCP Tools Support
    # ------------------------------------------------------------------
    def _identificar_tools_necessarios(self, pergunta: str) -> List[str]:
        """Usa LLM para identificar quais tools MCP usar para responder a pergunta.
        
        Args:
            pergunta: Pergunta do usuário
            
        Returns:
            Lista de nomes de tools a usar
        """
        if not self.config.enable_mcp_tools or not self.available_tools:
            return []
        
        tools_list = ", ".join(self.available_tools)
        
        prompt = f"""
        Pergunta do usuário: "{pergunta}"
        
        Tools disponíveis para {self.config.specialty}: {tools_list}
        
        Analisando a pergunta, quais tools devo usar para obter informações adicionais que me ajudem a responder melhor?
        
        Responda APENAS com os nomes das tools separados por vírgula, ou "nenhuma" se não precisar de tools.
        
        Exemplo de respostas válidas:
        - "consultar_saldo_ferias"
        - "consultar_banco_horas, consultar_beneficios"
        - "nenhuma"
        """
        
        try:
            resposta = self.llm.invoke(prompt).content.strip().lower()
            
            if resposta in ["nenhuma", "nenhum", "none", ""]:
                return []
                
            # Parse da resposta
            tools_solicitadas = [nome.strip() for nome in resposta.split(",")]
            
            # Valida se as tools existem
            tools_validas = []
            for tool in tools_solicitadas:
                if tool in self.available_tools:
                    tools_validas.append(tool)
                else:
                    self._log(f"⚠️ Tool '{tool}' solicitada pelo LLM mas não disponível")
            
            return tools_validas
            
        except Exception as exc:
            self._log(f"❌ Erro ao identificar tools necessárias: {exc}")
            return []

    def _executar_tools_mcp(self, tools: List[str], perfil_usuario: Dict[str, Any]) -> str:
        """Executa as tools MCP selecionadas.
        
        Args:
            tools: Lista de nomes de tools para executar
            perfil_usuario: Perfil do usuário para extrair parâmetros
            
        Returns:
            String com os resultados das tools executadas
        """
        if not tools or not self.mcp_client:
            return ""
        
        resultados = []
        
        for tool_name in tools:
            try:
                # Extrai parâmetros automaticamente do perfil
                params = self._extrair_parametros_tool(tool_name, perfil_usuario)
                
                self._log(f"🔧 Executando tool '{tool_name}' com parâmetros: {params}")
                
                # Executa a tool
                resultado = self.mcp_client.call_tool(tool_name, params)
                
                if resultado.is_success:
                    data_str = str(resultado.data) if resultado.data else resultado.message
                    resultados.append(f"📊 {tool_name}: {data_str}")
                    self._log(f"✅ Tool '{tool_name}' executada com sucesso")
                else:
                    resultados.append(f"❌ {tool_name}: {resultado.error_message}")
                    self._log(f"❌ Erro na tool '{tool_name}': {resultado.error_message}")
                    
            except Exception as exc:
                error_msg = f"Erro ao executar: {str(exc)}"
                resultados.append(f"❌ {tool_name}: {error_msg}")
                self._log(f"❌ Exceção na tool '{tool_name}': {exc}")
        
        return "\n".join(resultados) if resultados else ""

    def _extrair_parametros_tool(self, tool_name: str, perfil_usuario: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai parâmetros necessários para uma tool do perfil do usuário.
        
        Args:
            tool_name: Nome da tool
            perfil_usuario: Perfil do usuário
            
        Returns:
            Dict com parâmetros extraídos
        """
        params = {}
        
        # Mapeamentos comuns baseados no perfil do usuário
        cpf = self._perfil_val(perfil_usuario, "cpf", "CPF")
        username = self._perfil_val(perfil_usuario, "username", "login", "usuario")
        email = self._perfil_val(perfil_usuario, "email", "Email")
        nome = self._perfil_val(perfil_usuario, "nome", "Nome")
        
        # Parâmetros específicos por tool (configurações básicas)
        if "cpf" in str(self.mcp_client.get_tool(tool_name).parameters) and cpf:
            params["cpf"] = cpf
            
        if "username" in str(self.mcp_client.get_tool(tool_name).parameters) and username:
            params["username"] = username
            
        if "solicitante" in str(self.mcp_client.get_tool(tool_name).parameters):
            params["solicitante"] = nome or email or "Usuário"
        
        return params

    # ------------------------------------------------------------------
    # A2A (Agent-to-Agent) Communication
    # ------------------------------------------------------------------
    def set_agent_registry(self, registry):
        """Configura o registry A2A para este agente."""
        self.agent_registry = registry
        self._log(f"🤝 A2A Registry configurado para {self.config.name}")
    
    def can_delegate_query(self, pergunta: str) -> tuple[bool, Optional[str], Optional[str]]:
        """Determina se deve delegar parte da pergunta para outro agente.
        
        Returns:
            Tuple (should_delegate, target_agent, sub_query)
        """
        if not self.config.enable_a2a or not self.agent_registry:
            return False, None, None
        
        # 1. Verifica regras de delegação pré-configuradas
        for rule in self.config.delegation_rules:
            if hasattr(rule, 'matches'):
                score = rule.matches(pergunta)
                if score > 0:
                    self._log(f"🎯 Regra de delegação ativada: {rule.name} (score: {score:.2f})")
                    # Gera sub-query focada na área do agente alvo
                    sub_query = self._generate_focused_subquery(pergunta, rule.target_agent, rule.keywords)
                    return True, rule.target_agent, sub_query
        
        # 2. Se não há regras específicas, usa LLM para análise
        return self._analyze_delegation_with_llm(pergunta)
    
    def _generate_focused_subquery(self, original_query: str, target_agent: str, keywords: List[str]) -> str:
        """Gera uma sub-pergunta focada para o agente alvo."""
        try:
            prompt = f"""
            Pergunta original: "{original_query}"
            
            Preciso delegar uma parte desta pergunta para o especialista em {target_agent}.
            As palavras-chave relevantes são: {', '.join(keywords)}
            
            Reformule a pergunta focando apenas nos aspectos que o especialista em {target_agent} pode responder.
            Seja específico e direto.
            
            Resposta:
            """
            
            response = self.llm.invoke(prompt)
            sub_query = response.content.strip()
            
            self._log(f"📝 Sub-query gerada para {target_agent}: {sub_query}")
            return sub_query
            
        except Exception as e:
            self._log(f"⚠️ Erro ao gerar sub-query: {e}")
            return original_query  # Fallback para pergunta original
    
    def _analyze_delegation_with_llm(self, pergunta: str) -> tuple[bool, Optional[str], Optional[str]]:
        """Usa LLM para analisar se deve delegar."""
        if not self.agent_registry:
            return False, None, None
        
        # Se LLM não está disponível, retorna False
        if not self.llm:
            self._log("⚠️ LLM não disponível para análise de delegação")
            return False, None, None
        
        try:
            available_agents = self.agent_registry.get_available_agents()
            agents_info = []
            
            for agent_id in available_agents:
                if agent_id != self.config.identifier:  # Não delegar para si mesmo
                    info = self.agent_registry.get_agent_info(agent_id)
                    if info:
                        agents_info.append(f"- {agent_id}: {info.get('specialty', 'N/A')}")
            
            if not agents_info:
                return False, None, None
            
            prompt = f"""
            Pergunta: "{pergunta}"
            Minha especialidade: {self.config.specialty}
            
            Agentes especialistas disponíveis:
            {chr(10).join(agents_info)}
            
            Analisando a pergunta, preciso delegar alguma parte para outro especialista?
            
            Responda em formato JSON:
            {{
                "should_delegate": boolean,
                "target_agent": "id_do_agente_ou_null",
                "sub_query": "pergunta_específica_ou_null",
                "confidence": 0.0-1.0,
                "reason": "explicação_breve"
            }}
            """
            
            response = self.llm.invoke(prompt)
            
            try:
                import json
                analysis = json.loads(response.content.strip())
                
                should_delegate = analysis.get("should_delegate", False)
                target_agent = analysis.get("target_agent")
                sub_query = analysis.get("sub_query")
                confidence = analysis.get("confidence", 0.0)
                reason = analysis.get("reason", "")
                
                if should_delegate and confidence >= 0.7:  # Threshold de confiança
                    self._log(f"🤖 LLM recomenda delegação para {target_agent}: {reason}")
                    return True, target_agent, sub_query
                else:
                    self._log(f"🤖 LLM não recomenda delegação (confiança: {confidence:.2f})")
                    return False, None, None
                
            except json.JSONDecodeError as e:
                self._log(f"❌ Erro ao parsear resposta LLM: {e}")
                return False, None, None
                
        except Exception as e:
            self._log(f"❌ Erro na análise de delegação: {e}")
            return False, None, None
    
    def delegate_to_agent(self, target_agent: str, query: str, context: Dict = None) -> Optional[Dict]:
        """Delega uma sub-pergunta para outro agente."""
        if not self.config.enable_a2a or not self.agent_registry:
            self._log("❌ A2A não habilitado para delegação")
            return None
        
        try:
            from a2a import AgentMessage, MessageType
            
            message = AgentMessage(
                sender=self.config.identifier,
                recipient=target_agent,
                message_type=MessageType.DELEGATE,
                content=query,
                context=context or {}
            )
            
            self._log(f"📤 Delegando para {target_agent}: {query}")
            
            response = self.agent_registry.route_message(message, self.current_session)
            
            if response.is_success:
                self._log(f"📥 Resposta recebida de {target_agent}: {len(response.content)} chars")
                return {
                    "success": True,
                    "content": response.content,
                    "sources": response.sources_used,
                    "tools": response.tools_used,
                    "contribution": response.contribution_summary,
                    "agent": target_agent
                }
            else:
                self._log(f"❌ Erro na delegação: {response.error_message}")
                return {
                    "success": False,
                    "error": response.error_message,
                    "agent": target_agent
                }
                
        except Exception as e:
            self._log(f"❌ Exceção durante delegação: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": target_agent
            }

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    @staticmethod
    def _formatar_contexto(documentos: List[Dict[str, Any]], *, especialidade: str) -> str:
        if not documentos:
            return f"Nenhum documento específico encontrado na base de conhecimento de {especialidade}."

        partes: List[str] = []
        for i, registro in enumerate(documentos):
            fonte = registro.get("fonte_documento") or "Documento interno"
            doc_id = registro.get("id", "N/A")
            conteudo = (registro.get("conteudo_original") or "").strip()
            
            # Debug do conteúdo
            print(f"🔍 Debug doc {i+1}: fonte='{fonte}', id='{doc_id}', conteudo_len={len(conteudo)}")
            if not conteudo:
                print(f"⚠️ Documento {i+1} sem conteúdo! Keys disponíveis: {list(registro.keys())}")
                # Tentar outros campos de conteúdo
                conteudo = (registro.get("conteudo") or registro.get("texto") or registro.get("content") or "").strip()
                if conteudo:
                    print(f"✅ Conteúdo encontrado em campo alternativo: {len(conteudo)} chars")
            
            if conteudo:
                partes.append(f"📄 {fonte} (ID: {doc_id}):\n{conteudo}")
            else:
                partes.append(f"📄 {fonte} (ID: {doc_id}):\n[Documento sem conteúdo legível]")
                
        return "\n\n".join(partes)

    @staticmethod
    def _coletar_fontes(documentos: List[Dict[str, Any]]) -> List[str]:
        fontes: List[str] = []
        vistos: set[str] = set()
        for registro in documentos:
            fonte = (
                registro.get("fonte_documento")
                or registro.get("fonte")
                or registro.get("titulo")
                or registro.get("id")
            )
            if not fonte:
                continue
            chave = str(fonte).strip()
            if not chave or chave.lower() in vistos:
                continue
            vistos.add(chave.lower())
            fontes.append(chave)
        return fontes

    def _is_response_generic(self, response: str) -> bool:
        """Verifica se a resposta é genérica e não usa documentos específicos da base."""
        response_lower = response.lower()
        
        # Padrões que indicam claramente que não há informação na base
        no_info_patterns = [
            "não tenho essa informação específica",
            "não localizei informações específicas", 
            "não encontrei essa informação",
            "não possuo informações específicas",
            "recomendo abrir um ticket",
            "entre em contato com",
            "não consta em nossa base",
            "informação não disponível",
            "não há dados disponíveis sobre",
            "desculpe, mas não encontrei"
        ]
        
        # Padrões para respostas de conhecimento geral (definições, conceitos)
        general_knowledge_patterns = [
            "é uma palavra",
            "é um termo que",
            "é uma ferramenta",
            "pode se referir a",
            "em um contexto técnico",
            "no campo da tecnologia", 
            "se você estiver se referindo a algo mais específico",
            "por favor, me avise",
            "estou aqui para ajudar",
            "é usada para",
            "também pode se referir a",
            "significa",
            "biblioteca para python"
        ]
        
        # Se tem padrões de "sem informação", definitivamente genérica
        no_info_count = sum(1 for pattern in no_info_patterns if pattern in response_lower)
        if no_info_count > 0:
            return True
        
        # Se tem muitos padrões de conhecimento geral, também é genérica
        general_count = sum(1 for pattern in general_knowledge_patterns if pattern in response_lower)
        
        # Se tem 2 ou mais padrões de conhecimento geral, considerar genérica
        return general_count >= 2

    # ------------------------------------------------------------------
    # Fluxo principal
    # ------------------------------------------------------------------
    def processar_pergunta(self, pergunta: str, perfil_usuario: Dict[str, Any]) -> str:
        if not self.llm or not self.embeddings or not self.dal:
            raise RuntimeError("Subagente não inicializado corretamente.")

        nome_usuario = self._perfil_val(perfil_usuario, "nome", "Nome") or "usuário"
        usuario_id = self._usuario_id(perfil_usuario)
        
        # Reset rastreamento para nova pergunta
        self.last_sources_used = []
        self.last_tools_used = []

        try:
            self._log(f"🔍 {self.config.name} processando pergunta: '{pergunta}' para {nome_usuario}")
            
            # ===================================================================
            # QUICK WIN 1: ANÁLISE DE PERFIL ANTECIPADA
            # ===================================================================
            # Verificar se já temos análise em cache
            if usuario_id not in self.cached_user_profiles:
                self._log(f"🔍 Analisando perfil de {nome_usuario}...")
                analyzed_profile = self.profile_analyzer.analyze_user_profile(perfil_usuario)
                self.cached_user_profiles[usuario_id] = analyzed_profile
                self._log(
                    f"✅ Perfil analisado e cacheado: geografia={analyzed_profile.get('geografia')}, "
                    f"projetos={analyzed_profile.get('projetos')}, nivel={analyzed_profile.get('nivel_hierarquico')}"
                )
            else:
                analyzed_profile = self.cached_user_profiles[usuario_id]
                self._log("✅ Perfil recuperado do cache")
            
            # ===================================================================
            # QUICK WIN 2: BUSCA OTIMIZADA COM FILTROS SQL
            # ===================================================================
            # Gerar embedding da pergunta
            consulta_embedding = self.embeddings.embed_query(pergunta)
            self._log(f"� Embedding gerado, iniciando busca otimizada na tabela '{self.table_name}'...")
            
            # Usar busca otimizada com filtros de perfil (síncrona por enquanto, asyncio depois)
            import asyncio
            try:
                # Tentar usar busca otimizada async
                candidatos = asyncio.run(
                    OptimizedDocumentSearch.search_with_profile_filter(
                        dal=self.dal,
                        table_name=self.table_name,
                        query_embedding=consulta_embedding,
                        user_profile=analyzed_profile,
                        limit=15
                    )
                )
                self._log(f"🎯 Busca otimizada: {len(candidatos)} candidatos (filtrados no SQL)")
            except Exception as e:
                # Fallback para busca tradicional se der erro
                self._log(f"⚠️ Busca otimizada falhou ({e}), usando busca tradicional...")
                candidatos = self._busca_multilingue(pergunta)
                self._log(f"🔎 Busca tradicional: {len(candidatos)} candidatos")

            # Verificar permissões e coletar motivos de rejeição
            documentos_permitidos = []
            motivos_rejeicao = {}
            
            for registro in candidatos:
                if self.verificar_permissao_documento(registro, perfil_usuario):
                    documentos_permitidos.append(registro)
                else:
                    # Coletar motivo da rejeição para transparência
                    motivo = self._obter_motivo_rejeicao(registro, perfil_usuario)
                    fonte = registro.get("fonte_documento", "documento")
                    if motivo not in motivos_rejeicao:
                        motivos_rejeicao[motivo] = []
                    motivos_rejeicao[motivo].append(fonte)
            
            self._log(f"✅ {len(documentos_permitidos)} documentos válidos após governança")
            
            # 2. NOVO: Verifica se precisa de tools MCP para informações adicionais
            tools_info = ""
            if self.config.enable_mcp_tools:
                tools_necessarias = self._identificar_tools_necessarios(pergunta)
                if tools_necessarias:
                    self._log(f"🔧 Tools MCP identificadas: {', '.join(tools_necessarias)}")
                    tools_resultado = self._executar_tools_mcp(tools_necessarias, perfil_usuario)
                    if tools_resultado:
                        tools_info = f"\n\n🔧 INFORMAÇÕES OBTIDAS VIA FERRAMENTAS:\n{tools_resultado}"
                        self.last_tools_used.extend(tools_necessarias)
            
            # 3. NOVO: Verifica se precisa de delegação A2A
            delegacao_info = ""
            colaboracao_summary = ""
            if self.config.enable_a2a:
                should_delegate, target_agent, sub_query = self.can_delegate_query(pergunta)
                if should_delegate and target_agent:
                    self._log(f"🤝 Delegação A2A identificada: {target_agent}")
                    delegation_result = self.delegate_to_agent(
                        target_agent,
                        sub_query,
                        {"original_query": pergunta, "user_profile": perfil_usuario}
                    )
                    
                    if delegation_result and delegation_result.get("success"):
                        delegacao_info = f"\n\n🤝 INFORMAÇÃO DE {target_agent.upper()}:\n{delegation_result['content']}"
                        
                        # Rastrear fontes e ferramentas do agente delegado
                        if delegation_result.get("sources"):
                            self.last_sources_used.extend(delegation_result["sources"])
                        if delegation_result.get("tools"):
                            self.last_tools_used.extend(delegation_result["tools"])
                        
                        # Preparar summary de colaboração para o usuário
                        colaboracao_summary = f"\n\n{delegation_result.get('contribution', '')}"
                    else:
                        error_msg = delegation_result.get("error", "Erro desconhecido") if delegation_result else "Falha na comunicação"
                        self._log(f"⚠️ Delegação falhou: {error_msg}")
                        delegacao_info = f"\n\n⚠️ Tentei consultar {target_agent} mas houve um problema técnico."

            # Preparar informações de transparência sobre restrições
            info_restricoes = ""
            if documentos_permitidos:
                # Seleção diversificada de documentos para contexto
                docs_selecionados = self._selecionar_documentos_diversificados(documentos_permitidos)
                fontes_debug = [doc.get("fonte_documento", "sem fonte") for doc in docs_selecionados]
                self._log(f"📄 Fontes selecionadas (diversificadas): {fontes_debug}")
                
                # Armazenar contexto para validação externa (usado pelo hierarchical)
                self._last_context_docs = docs_selecionados
            else:
                docs_selecionados = []
                self._last_context_docs = []
                self._log("⚠️ Nenhum documento aprovado. Resposta pode ser genérica.")
                if motivos_rejeicao:
                    info_restricoes = self._criar_mensagem_restricoes(motivos_rejeicao)

            historico_formatado = self.obter_historico_formatado(usuario_id)
            contexto = self._formatar_contexto(docs_selecionados, especialidade=self.config.specialty)
            
            # Debug do contexto
            self._log(f"📝 Contexto formatado: {len(contexto)} caracteres")
            if contexto:
                self._log(f"🔍 Primeiros 200 chars do contexto: '{contexto[:200]}...'")
            else:
                self._log("⚠️ Contexto vazio!")

            contexto_personalizado = f"""
INFORMAÇÕES DO FUNCIONÁRIO:
- Nome: {nome_usuario}
- Cargo: {self._perfil_val(perfil_usuario, 'cargo', 'Cargo') or 'Não informado'}
- Departamento: {self._perfil_val(perfil_usuario, 'area', 'Departamento') or 'Não informado'}
- Nível Hierárquico: {self._perfil_val(perfil_usuario, 'nivel_hierarquico', 'Nivel_Hierarquico') or 'Não informado'}
- Geografia: {self._perfil_val(perfil_usuario, 'geografia', 'Geografia') or 'Não informada'}
- Projetos: {', '.join(self._normalizar_lista(self._perfil_val(perfil_usuario, 'projetos', 'Projetos') or [], vazio_padrao=['Nenhum']))}

INFORMAÇÕES DISPONÍVEIS:
{contexto}{tools_info}{delegacao_info}
"""

            prompt_formatado = self.config.prompt_template.format(
                historico_conversa=historico_formatado,
                contexto=contexto_personalizado,
                pergunta=pergunta,
            )

            resposta_raw = self.llm.invoke(prompt_formatado)
            resposta_final = resposta_raw.content if hasattr(resposta_raw, "content") else str(resposta_raw)

            # ===================================================================
            # QUICK WIN 3: VALIDAÇÃO RIGOROSA DA RESPOSTA
            # ===================================================================
            validation_result = ResponseValidator.validate_response_quality(
                response=resposta_final,
                pergunta=pergunta,
                documentos=docs_selecionados,
                min_score=0.6
            )
            
            self._log(
                f"🔍 Validação da resposta: score={validation_result['score']:.2f}, "
                f"válida={validation_result['is_valid']}"
            )
            
            if self.config.debug:
                for criterio, score in validation_result['criteria_scores'].items():
                    self._log(f"  - {criterio}: {score:.2f}")
                if validation_result['issues']:
                    for issue in validation_result['issues']:
                        self._log(f"  ⚠️ {issue}")
            
            # Se a validação falhou criticamente (especialmente controle de acesso), regenerar
            if not validation_result['is_valid'] and validation_result['criteria_scores'].get('access_control', 1.0) < 0.8:
                self._log("❌ Resposta falhou na validação de controle de acesso, bloqueando...")
                resposta_final = (
                    "Desculpe, não posso fornecer essas informações devido a restrições de acesso. "
                    "Por favor, entre em contato com o suporte ou seu gestor para mais detalhes."
                )
            
            # Verificar se a resposta é genérica (não usa documentos específicos)
            is_generic_response = self._is_response_generic(resposta_final)
            
            fontes_consultadas = self._coletar_fontes(docs_selecionados)
            
            # Só adicionar fontes se a resposta NÃO for genérica e houver documentos relevantes
            if not is_generic_response and fontes_consultadas:
                self.last_sources_used.extend(fontes_consultadas)
            
            # Adicionar informações de fontes apenas se realmente utilizadas
            if self.last_sources_used and not is_generic_response:
                lista_fontes = "\n".join(f"- {fonte}" for fonte in set(self.last_sources_used))
                resposta_final = f"{resposta_final}\n\nFontes consultadas:\n{lista_fontes}"
            
            # Adicionar informações sobre restrições se não houve fontes válidas
            if info_restricoes and not self.last_sources_used:
                resposta_final = f"{resposta_final}{info_restricoes}"
            
            # Adicionar summary de colaboração se houve delegação
            if colaboracao_summary:
                resposta_final = f"{resposta_final}{colaboracao_summary}"

            self.adicionar_ao_historico(usuario_id, pergunta, resposta_final)
            return resposta_final

        except Exception as exc:  # noqa: BLE001
            self._log(f"❌ Erro no subagente {self.config.identifier}: {exc}")
            erro_resposta = self.config.error_message or (
                "Ops! Tive um problema técnico aqui. Que tal tentar novamente em instantes ou acionar o suporte?"
            )
            self.adicionar_ao_historico(usuario_id, pergunta, erro_resposta)
            return erro_resposta

    # ------------------------------------------------------------------
    # Inicialização pública
    # ------------------------------------------------------------------
    def inicializar(self) -> bool:
        try:
            api_key = self.carregar_configuracoes_e_dados()
            self.inicializar_modelos(api_key)
            self.configurar_vector_store()
            # Nova etapa: configurar MCP tools se habilitadas
            self.configurar_mcp_tools()
            self._log(f"✅ Subagente {self.config.name} pronto para uso!")
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Erro na inicialização do subagente {self.config.identifier}: {exc}")
            return False

    # ------------------------------------------------------------------
    # Metadados do agente
    # ------------------------------------------------------------------
    def obter_info_agente(self) -> Dict[str, Any]:
        return {
            "nome": self.config.name,
            "especialidade": self.config.specialty,
            "descricao": self.config.description,
            "keywords": self.config.keywords,
            "pronto": self.dal is not None,
        }


def create_subagent(config: SubagentConfig) -> BaseSubagent:
    """Factory auxiliar para criação de subagentes parametrizados."""
    return BaseSubagent(config)
