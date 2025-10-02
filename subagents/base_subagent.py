"""Infraestrutura compartilhada para criação de subagentes Neoson."""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from postgres_vector_store import PostgresVectorStore

warnings.simplefilter(action="ignore", category=FutureWarning)


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
        self.vector_store: Optional[PostgresVectorStore] = None
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
        load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Chave da API OPENAI_API_KEY não encontrada nas variáveis de ambiente")

        db_env = self.config.database_env_var
        table_env = self.config.table_env_var

        self.db_dsn = os.getenv(db_env or "DATABASE_URL") or os.getenv("DATABASE_URL")
        if not self.db_dsn:
            raise ValueError(
                f"Variável de ambiente DATABASE_URL ou {db_env} não configurada para o agente {self.config.identifier}."
            )

        self.table_name = os.getenv(table_env, self.config.table_name)
        self._log(f"✅ Fonte de conhecimento configurada: tabela '{self.table_name}'.")
        return api_key

    def inicializar_modelos(self, api_key: str) -> None:
        self._log(f"--- 🤖 Inicializando modelos OpenAI para {self.config.specialty}... ---")
        self.llm = ChatOpenAI(
            api_key=api_key,
            model=self.config.llm_model,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens,
        )
        self.embeddings = OpenAIEmbeddings(api_key=api_key, model=self.config.embedding_model)
        self._log("✅ Modelos OpenAI inicializados.")

    def configurar_vector_store(self) -> None:
        if not self.db_dsn:
            raise RuntimeError("Banco de dados não configurado. Execute carregar_configuracoes_e_dados primeiro.")

        self._log(f"--- 🗄️ Conectando à base vetorial '{self.table_name}'... ---")
        self.vector_store = PostgresVectorStore(self.table_name, dsn=self.db_dsn, min_connections=1, max_connections=5)
        self._log("✅ Conexão com a base de conhecimento estabelecida.")

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
        candidatos_originais = self.vector_store.similarity_search(consulta_embedding, limit=30)
        
        # Adicionar candidatos únicos baseado no ID ou conteúdo
        for candidato in candidatos_originais:
            id_unico = candidato.get("id", str(hash(candidato.get("conteudo_original", ""))))
            if id_unico not in candidatos_unicos:
                candidatos_unicos[id_unico] = candidato
        
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
            candidatos_traduzidos = self.vector_store.similarity_search(consulta_embedding_trad, limit=30)
            
            for candidato in candidatos_traduzidos:
                id_unico = candidato.get("id", str(hash(candidato.get("conteudo_original", ""))))
                if id_unico not in candidatos_unicos:
                    candidatos_unicos[id_unico] = candidato
        
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
                candidatos_gov = self.vector_store.similarity_search(consulta_embedding_gov, limit=10)
                
                for candidato in candidatos_gov:
                    id_unico = candidato.get("id", str(hash(candidato.get("conteudo_original", ""))))
                    if id_unico not in candidatos_unicos:
                        candidatos_unicos[id_unico] = candidato
        
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
            fonte = doc.get("fonte_documento", "").upper()
            
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
            self._log(f"📄 Selecionado internacional: {docs_internacionais[0].get('fonte_documento', 'sem nome')}")
        
        # 2. Sempre tentar incluir pelo menos 1 documento nacional BR (se houver) 
        if docs_nacionais_br and len(selecionados) < max_docs:
            selecionados.append(docs_nacionais_br[0])
            self._log(f"📄 Selecionado nacional BR: {docs_nacionais_br[0].get('fonte_documento', 'sem nome')}")
        
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
                    self._log(f"📄 Selecionado {nome_categoria}: {doc_selecionado.get('fonte_documento', 'sem nome')}")
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
        for registro in documentos:
            fonte = registro.get("fonte_documento") or "Documento interno"
            doc_id = registro.get("id", "N/A")
            conteudo = (registro.get("conteudo_original") or "").strip()
            partes.append(f"📄 {fonte} (ID: {doc_id}):\n{conteudo}")
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

    # ------------------------------------------------------------------
    # Fluxo principal
    # ------------------------------------------------------------------
    def processar_pergunta(self, pergunta: str, perfil_usuario: Dict[str, Any]) -> str:
        if not self.llm or not self.embeddings or not self.vector_store:
            raise RuntimeError("Subagente não inicializado corretamente.")

        nome_usuario = self._perfil_val(perfil_usuario, "nome", "Nome") or "usuário"
        usuario_id = self._usuario_id(perfil_usuario)
        
        # Reset rastreamento para nova pergunta
        self.last_sources_used = []
        self.last_tools_used = []

        try:
            self._log(f"🔍 {self.config.name} processando pergunta: '{pergunta}' para {nome_usuario}")
            
            # 1. Busca multilíngue na base de conhecimento
            candidatos = self._busca_multilingue(pergunta)
            self._log(f"🔎 Encontrados {len(candidatos)} candidatos brutos (busca multilíngue)")

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
            else:
                docs_selecionados = []
                self._log("⚠️ Nenhum documento aprovado. Resposta pode ser genérica.")
                if motivos_rejeicao:
                    info_restricoes = self._criar_mensagem_restricoes(motivos_rejeicao)

            historico_formatado = self.obter_historico_formatado(usuario_id)
            contexto = self._formatar_contexto(docs_selecionados, especialidade=self.config.specialty)

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

            fontes_consultadas = self._coletar_fontes(docs_selecionados)
            if fontes_consultadas:
                self.last_sources_used.extend(fontes_consultadas)
            
            # Adicionar informações de fontes e colaboração
            if self.last_sources_used:
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
            "pronto": self.vector_store is not None,
        }


def create_subagent(config: SubagentConfig) -> BaseSubagent:
    """Factory auxiliar para criação de subagentes parametrizados."""
    return BaseSubagent(config)
