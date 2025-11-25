"""Agent Factory - Cria coordenadores e subagentes dinamicamente
Sistema de pipeline para gerar agentes sob demanda"""

from __future__ import annotations

import os
import asyncio
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

from core.config import config
from dal.postgres_dal_async import PostgresDALAsync


class AgentType(Enum):
    """Tipo de agente a ser criado"""
    COORDINATOR = "coordinator"
    SUBAGENT = "subagent"


@dataclass
class AgentConfig:
    """Configuração para criar um agente"""
    # Dados básicos
    name: str  # Nome do agente (ex: "Carlos", "Marina")
    identifier: str  # ID único (ex: "dev", "enduser")
    specialty: str  # Especialidade (ex: "Desenvolvimento", "Suporte")
    description: str  # Descrição detalhada do agente
    agent_type: AgentType  # Tipo: COORDINATOR ou SUBAGENT
    
    # Configurações específicas de subagente
    table_name: Optional[str] = None  # Nome da tabela (ex: "knowledge_dev")
    keywords: List[str] = field(default_factory=list)  # Palavras-chave
    prompt_template: Optional[str] = None  # Template customizado
    
    # Configurações de coordenador
    children_agents: List[str] = field(default_factory=list)  # IDs dos filhos
    
    # Configurações de ferramentas (MCP)
    enable_mcp_tools: bool = False
    mcp_tools_category: Optional[str] = None
    mcp_tool_server_url: Optional[str] = None
    allowed_tools: List[str] = field(default_factory=list)
    
    # Configurações LLM
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 10000
    
    # Outros
    debug: bool = False
    error_message: Optional[str] = None


class AgentFactory:
    """Fábrica para criar agentes dinamicamente"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.agents_created: List[str] = []
        self.dal = PostgresDALAsync()
        
    async def create_agent(self, agent_config: AgentConfig) -> Dict[str, Any]:
        """
        Cria um novo agente (coordenador ou subagente) baseado na configuração
        
        Args:
            agent_config: Configuração do agente
            
        Returns:
            Dict com status da criação e path do arquivo gerado
        """
        
        if agent_config.agent_type == AgentType.SUBAGENT:
            return await self._create_subagent(agent_config)
        else:
            return await self._create_coordinator(agent_config)
    
    async def _create_subagent(self, config: AgentConfig) -> Dict[str, Any]:
        """Cria um subagente especializado"""
        
        print(f"🏭 [Factory] Criando subagente: {config.identifier}")
        
        # 1. Validar configuração
        if not config.table_name:
            config.table_name = f"knowledge_{config.identifier}"
        
        # 2. Criar tabela no PostgreSQL
        table_created = await self._create_knowledge_table(config.table_name)
        if not table_created:
            return {
                "success": False,
                "error": f"Falha ao criar tabela {config.table_name}",
                "identifier": config.identifier,
                "message": f"Erro ao criar tabela {config.table_name}"
            }
        
        # 3. Gerar arquivo Python do agente
        agent_file_path = await self._generate_subagent_file(config)
        
        # 3.5. Gerar arquivo HTML do agente
        agent_html_path = await self._generate_agent_html(config, "subagent")
        
        # 4. Registrar no sistema
        from factory.agent_registry import get_registry
        registry = get_registry()
        
        # Usar caminho relativo para file_path
        relative_file_path = f"agentes/subagentes/agente_{config.identifier}_async.py"
        
        try:
            print(f"📋 [Factory] Registrando subagente no registry...")
            registry.register_agent({
                "identifier": config.identifier,
                "name": config.name,
                "specialty": config.specialty,
                "type": "subagent",
                "table_name": config.table_name,
                "file_path": relative_file_path,
                "html_path": str(agent_html_path),
                "keywords": config.keywords,
                "tools_enabled": config.enable_mcp_tools,
                "tools_category": config.mcp_tools_category
            })
            print(f"✅ [Factory] Subagente registrado com sucesso")
        except Exception as e:
            print(f"❌ [Factory] ERRO ao registrar subagente: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao registrar subagente: {str(e)}",
                "identifier": config.identifier,
                "message": f"Subagente criado mas falhou ao registrar"
            }
        
        self.agents_created.append(config.identifier)
        
        return {
            "success": True,
            "identifier": config.identifier,
            "file_path": str(agent_file_path),
            "table_name": config.table_name,
            "message": f"Subagente {config.name} criado com sucesso!"
        }
    
    async def _create_coordinator(self, config: AgentConfig) -> Dict[str, Any]:
        """Cria um agente coordenador"""
        
        print(f"🏭 [Factory] Criando coordenador: {config.identifier}")
        
        # 1. Validar que tem filhos
        if not config.children_agents:
            return {
                "success": False,
                "error": "Coordenador deve ter pelo menos um agente filho",
                "identifier": config.identifier,
                "message": "Erro: Coordenador precisa de agentes filhos"
            }
        
        # 2. Gerar arquivo Python do coordenador
        coordinator_file_path = await self._generate_coordinator_file(config)
        
        # 2.5. Gerar arquivo HTML do coordenador
        coordinator_html_path = await self._generate_agent_html(config, "coordinator")
        
        # 3. Registrar no sistema
        from factory.agent_registry import get_registry
        registry = get_registry()
        
        # Usar caminho relativo para file_path
        relative_file_path = f"agentes/coordenadores/agente_{config.identifier}_async.py"
        
        try:
            print(f"📋 [Factory] Registrando coordenador no registry...")
            registry.register_agent({
                "identifier": config.identifier,
                "name": config.name,
                "specialty": config.specialty,
                "type": "coordinator",
                "file_path": relative_file_path,
                "html_path": str(coordinator_html_path),
                "children": config.children_agents
            })
            print(f"✅ [Factory] Coordenador registrado com sucesso")
        except Exception as e:
            print(f"❌ [Factory] ERRO ao registrar coordenador: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao registrar coordenador: {str(e)}",
                "identifier": config.identifier,
                "message": f"Coordenador criado mas falhou ao registrar"
            }
        
        self.agents_created.append(config.identifier)
        
        return {
            "success": True,
            "identifier": config.identifier,
            "file_path": str(coordinator_file_path),
            "children": config.children_agents,
            "message": f"Coordenador {config.name} criado com sucesso!"
        }
    
    async def _create_knowledge_table(self, table_name: str) -> bool:
        """Cria tabela de conhecimento no PostgreSQL"""
        
        try:
            print(f"📊 [Factory] Criando tabela: {table_name}")
            
            await self.dal.connect()
            
            # Usar a função PostgreSQL para criar tabela
            query = f"SELECT create_knowledge_table('{table_name}');"
            
            await self.dal.execute_query_async(query)
            
            print(f"✅ [Factory] Tabela {table_name} criada com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ [Factory] Erro ao criar tabela {table_name}: {e}")
            return False
            
        finally:
            await self.dal.disconnect()
    
    async def _generate_subagent_file(self, config: AgentConfig) -> Path:
        """Gera arquivo Python do subagente"""
        
        # Ler template
        template = self._get_subagent_template()
        
        # Preparar prompt template se não fornecido
        if not config.prompt_template:
            config.prompt_template = self._generate_default_prompt(config)
        
        # Substituir variáveis no template
        agent_code = template.format(
            name=config.name,
            identifier=config.identifier,
            specialty=config.specialty,
            description=config.description,
            table_name=config.table_name,
            keywords=repr(config.keywords),
            prompt_template=config.prompt_template,
            llm_model=config.llm_model,
            llm_temperature=config.llm_temperature,
            llm_max_tokens=config.llm_max_tokens,
            error_message=config.error_message or f"Desculpe, encontrei um erro ao processar sua pergunta sobre {config.specialty.lower()}. Por favor, tente novamente.",
            enable_mcp_tools=config.enable_mcp_tools,
            mcp_tools_category=config.mcp_tools_category or "",
            mcp_tool_server_url=config.mcp_tool_server_url or "",
            allowed_tools=repr(config.allowed_tools)
        )
        
        # Salvar arquivo na pasta correta: agentes/subagentes/
        subagents_dir = self.base_path / "agentes" / "subagentes"
        subagents_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = subagents_dir / f"agente_{config.identifier}_async.py"
        
        print(f"📝 [Factory] Criando arquivo Python do subagente...")
        print(f"   Pasta: {subagents_dir}")
        print(f"   Arquivo: agente_{config.identifier}_async.py")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(agent_code)
        
        print(f"✅ [Factory] Arquivo de subagente criado: {file_path}")
        
        return file_path
    
    async def _generate_coordinator_file(self, config: AgentConfig) -> Path:
        """Gera arquivo Python do coordenador"""
        
        # Ler template
        template = self._get_coordinator_template()
        
        # Criar imports dos filhos
        children_imports = "\n".join([
            f"from agente_{child}_async import criar_agente_{child}_async"
            for child in config.children_agents
        ])
        
        # Criar tasks de inicialização dos filhos
        children_tasks = ",\n                ".join([
            f"asyncio.to_thread(criar_agente_{child}_async, debug=self.debug)"
            for child in config.children_agents
        ])
        
        # Criar nomes dos filhos para logging
        children_names = repr([child.title() for child in config.children_agents])
        
        # Substituir variáveis no template
        coordinator_code = template.format(
            name=config.name,
            identifier=config.identifier,
            specialty=config.specialty,
            description=config.description,
            children_imports=children_imports,
            children_tasks=children_tasks,
            children_names=children_names,
            children_count=len(config.children_agents)
        )
        
        # Salvar arquivo na pasta correta: agentes/coordenadores/
        coordinators_dir = self.base_path / "agentes" / "coordenadores"
        coordinators_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = coordinators_dir / f"agente_{config.identifier}_async.py"
        
        print(f"📝 [Factory] Criando arquivo Python do coordenador...")
        print(f"   Pasta: {coordinators_dir}")
        print(f"   Arquivo: agente_{config.identifier}_async.py")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(coordinator_code)
        
        print(f"✅ [Factory] Arquivo de coordenador criado: {file_path}")
        
        return file_path
    
    def _get_subagent_template(self) -> str:
        """Retorna template base para subagente"""
        
        return '''"""Agente especializado em {specialty} - VERSÃO ASSÍNCRONA
Gerado automaticamente pela Agent Factory"""

from __future__ import annotations

from textwrap import dedent
import asyncio

from subagents.base_subagent import SubagentConfig
from dal.postgres_dal_async import PostgresDALAsync
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from core.config import config

PROMPT_TEMPLATE = dedent(
    """
{prompt_template}
    """
).strip()

KEYWORDS = {keywords}


class Agente{identifier}Async:
    """Agente especializado em {specialty} com operações ASSÍNCRONAS"""

    def __init__(self, *, debug: bool = False) -> None:
        self.config = SubagentConfig(
            identifier="{identifier}",
            name="{name}",
            specialty="{specialty}",
            description="{description}",
            keywords=KEYWORDS,
            table_name="{table_name}",
            prompt_template=PROMPT_TEMPLATE,
            debug=debug
        )
        
        # Inicializar componentes assíncronos
        self.dal_async = PostgresDALAsync()
        self.llm = None
        self.embeddings = None
        self.memoria_conversas = {{}}
        
        # Configuração de ferramentas MCP
        self.enable_mcp_tools = {enable_mcp_tools}
        self.mcp_tools_category = "{mcp_tools_category}"
        self.allowed_tools = {allowed_tools}
        
        # Inicializar LLM e embeddings
        self._inicializar_llm()
    
    def _inicializar_llm(self):
        """Inicializa LLM e embeddings"""
        api_key = config.openai.api_key
        
        self.llm = ChatOpenAI(
            api_key=api_key,
            model="{llm_model}",
            temperature={llm_temperature},
            max_tokens={llm_max_tokens}
        )
        
        self.embeddings = OpenAIEmbeddings(
            api_key=api_key,
            model=config.openai.embedding_model
        )
    
    async def processar_async(self, pergunta: str, user_profile: dict) -> str:
        """Processa pergunta de forma ASSÍNCRONA"""
        try:
            if self.config.debug:
                print(f"🔄 [{{self.config.name}}] Processando pergunta (ASYNC): '{{pergunta[:50]}}...'")
            
            # Conectar ao banco de forma assíncrona
            await self.dal_async.connect()
            
            # Gerar embedding da pergunta
            query_embedding = await asyncio.to_thread(
                self.embeddings.embed_query,
                pergunta
            )
            
            # Buscar contexto relevante de forma assíncrona
            search_result = await self.dal_async.search_vectors_async(
                table_name=self.config.table_name,
                query_vector=query_embedding,
                limit=5,
                similarity_threshold=0.5
            )
            
            if self.config.debug:
                print(f"📊 [{{self.config.name}}] Encontrados {{len(search_result.documents)}} documentos relevantes")
            
            # Preparar contexto
            contexto_str = self._preparar_contexto(search_result.documents)
            
            # Preparar histórico
            usuario_id = f"{{user_profile.get('Nome', 'usuario')}}_{{user_profile.get('Departamento', 'geral')}}"
            historico_str = self._preparar_historico(usuario_id)
            
            # Preparar prompt
            prompt_final = self.config.prompt_template.format(
                historico_conversa=historico_str,
                contexto=contexto_str,
                pergunta=pergunta
            )
            
            # Gerar resposta de forma assíncrona
            if self.config.debug:
                print(f"🤖 [{{self.config.name}}] Gerando resposta com LLM (ASYNC)...")
            
            resposta = await asyncio.to_thread(
                self.llm.invoke,
                prompt_final
            )
            
            resposta_texto = resposta.content if hasattr(resposta, 'content') else str(resposta)
            
            # Armazenar na memória
            self._adicionar_memoria(usuario_id, pergunta, resposta_texto)
            
            if self.config.debug:
                print(f"✅ [{{self.config.name}}] Resposta gerada com {{len(resposta_texto)}} caracteres")
            
            return resposta_texto
            
        except Exception as e:
            error_msg = f"❌ Erro ao processar pergunta (Agente {{self.config.name}}): {{str(e)}}"
            print(error_msg)
            return "{error_message}"
        
        finally:
            await self.dal_async.disconnect()
    
    def processar_pergunta(self, pergunta: str, user_profile: dict) -> str:
        """Wrapper síncrono para compatibilidade com sistema hierárquico"""
        return asyncio.run(self.processar_async(pergunta, user_profile))
    
    def _preparar_contexto(self, documents: list) -> str:
        """Prepara o contexto a partir dos documentos recuperados"""
        if not documents:
            return "Nenhum documento relevante encontrado na base de conhecimento."
        
        contexto_parts = []
        for i, doc in enumerate(documents, 1):
            conteudo = (
                doc.get('conteudo')
                or doc.get('conteudo_original')
                or doc.get('content')
                or doc.get('texto')
                or ''
            )

            if isinstance(conteudo, str):
                conteudo = conteudo.strip()
            else:
                conteudo = ''

            if not conteudo:
                continue

            metadata_parts = []
            fonte = doc.get('fonte_documento') or doc.get('fonte')
            idioma = doc.get('idioma')
            validade = doc.get('data_validade')
            responsavel = doc.get('responsavel')

            if fonte:
                metadata_parts.append(f"Fonte: {{fonte}}")
            if idioma:
                metadata_parts.append(f"Idioma: {{idioma}}")
            if validade:
                metadata_parts.append(f"Validade: {{validade}}")
            if responsavel:
                metadata_parts.append(f"Responsável: {{responsavel}}")

            metadata_dict = doc.get('metadata')
            if isinstance(metadata_dict, dict) and metadata_dict:
                metadata_parts.append(f"Metadados extras: {{metadata_dict}}")

            contexto_parts.append(f"[Documento {{i}}]")
            if metadata_parts:
                contexto_parts.append(" | ".join(metadata_parts))
            contexto_parts.append(conteudo)
            contexto_parts.append("")

        if not contexto_parts:
            return "Nenhum documento relevante encontrado na base de conhecimento."
        
        return "\\n".join(contexto_parts)
    
    def _preparar_historico(self, usuario_id: str) -> str:
        """Prepara o histórico de conversas do usuário"""
        if usuario_id not in self.memoria_conversas:
            return ""
        
        historico = self.memoria_conversas[usuario_id]
        if not historico:
            return ""
        
        # Pegar últimas 3 interações para contexto
        ultimas_interacoes = historico[-3:]
        historico_parts = ["HISTÓRICO DA CONVERSA:"]
        
        for i, (pergunta_ant, resposta_ant) in enumerate(ultimas_interacoes, 1):
            historico_parts.append(f"[Interação {{i}}]")
            historico_parts.append(f"Pergunta: {{pergunta_ant}}")
            historico_parts.append(f"Resposta: {{resposta_ant[:200]}}...")
            historico_parts.append("")
        
        historico_parts.append("---")
        return "\\n".join(historico_parts)
    
    def _adicionar_memoria(self, usuario_id: str, pergunta: str, resposta: str):
        """Adiciona interação à memória de conversas"""
        if usuario_id not in self.memoria_conversas:
            self.memoria_conversas[usuario_id] = []
        
        self.memoria_conversas[usuario_id].append((pergunta, resposta))
        
        # Manter apenas últimas 10 interações por usuário
        if len(self.memoria_conversas[usuario_id]) > 10:
            self.memoria_conversas[usuario_id] = self.memoria_conversas[usuario_id][-10:]


def criar_agente_{identifier}_async(*, debug: bool = False) -> Agente{identifier}Async:
    """Factory function para criar o agente de {specialty} assíncrono"""
    return Agente{identifier}Async(debug=debug)


if __name__ == "__main__":
    import asyncio
    
    async def test_agente_{identifier}_async():
        agente = criar_agente_{identifier}_async(debug=True)
        
        perfil_demo = {{
            "Nome": "Teste Usuario",
            "Cargo": "Analista",
            "Departamento": "{specialty}",
            "nivel_hierarquico": 2,
            "geografia": "BR",
            "projetos": ["N/A"],
        }}

        perguntas_demo = [
            "Teste de pergunta para {specialty}",
        ]

        for pergunta in perguntas_demo:
            print(f"\\n❓ Pergunta: {{pergunta}}")
            resposta = await agente.processar_async(pergunta, perfil_demo)
            print(f"🤖 {name}: {{resposta}}")
            print("-" * 80)
    
    asyncio.run(test_agente_{identifier}_async())
'''
    
    def _get_coordinator_template(self) -> str:
        """Retorna template base para coordenador"""
        
        return '''"""Coordenador de {specialty} - VERSÃO ASSÍNCRONA
Gerencia sub-especialistas de forma assíncrona
Gerado automaticamente pela Agent Factory"""

from __future__ import annotations

import logging
from typing import Dict, Optional
import asyncio

{children_imports}
from agente_{identifier} import criar_agente_{identifier}
from subagents.hierarchical import {identifier}HierarchicalAgent

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class {identifier}CoordinatorAsync:
    """Coordenador de {specialty} que gerencia sub-especialistas de forma ASSÍNCRONA"""
    
    def __init__(self, *, debug: bool = False):
        self.debug = debug
        self.hierarchical_agent: Optional[{identifier}HierarchicalAgent] = None
        self.base_agent = None
        
    async def initialize_async(self) -> bool:
        """Inicializa o coordenador e todos os sub-agentes de forma ASSÍNCRONA"""
        
        try:
            # 1. Criar agente base (em thread separada para não bloquear)
            logger.info("🤖 Inicializando agente {specialty} base (ASYNC)...")
            self.base_agent = await asyncio.to_thread(criar_agente_{identifier}, debug=self.debug)
            if not self.base_agent:
                logger.error("❌ Falha ao criar agente {specialty} base")
                return False
            
            # 2. Criar agente hierárquico
            logger.info("🏗️ Criando estrutura hierárquica (ASYNC)...")
            self.hierarchical_agent = {identifier}HierarchicalAgent(self.base_agent)
            
            # 3. Criar e registrar sub-agentes de forma concorrente
            logger.info("👥 Inicializando sub-especialistas (ASYNC/CONCORRENTE)...")
            
            # Criar todos os sub-agentes em paralelo
            sub_agents_tasks = [
                {children_tasks}
            ]
            
            sub_agents_results = await asyncio.gather(*sub_agents_tasks, return_exceptions=True)
            
            # Nomes dos sub-agentes para logging
            sub_agent_names = {children_names}
            
            # Registrar os sub-agentes criados com sucesso
            for i, (result, name) in enumerate(zip(sub_agents_results, sub_agent_names)):
                if isinstance(result, Exception):
                    logger.warning(f"⚠️ Erro ao criar sub-agente {{name}}: {{result}}")
                elif result:
                    self.hierarchical_agent.register_sub_agent(result)
                    logger.info(f"✅ Sub-agente {{name}} registrado")
                else:
                    logger.warning(f"⚠️ Falha ao criar sub-agente {{name}}")
            
            # 4. Verificar estatísticas
            stats = self.hierarchical_agent.get_hierarchy_stats()
            logger.info(f"📊 Hierarquia {specialty} configurada (ASYNC): {{stats}}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na inicialização do {identifier} Coordinator (ASYNC): {{e}}")
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
            sub_agentes_sugeridos: Lista de sub-agentes sugeridos pela LLM
        
        Returns:
            Resposta processada
        """
        
        logger.info(f"🎯 {identifier} Coordinator recebeu pergunta (ASYNC): '{{pergunta[:50]}}...'")
        
        if sub_agentes_sugeridos:
            logger.info(f"💡 Sub-agentes sugeridos pela LLM: {{sub_agentes_sugeridos}}")
        
        if not self.hierarchical_agent:
            logger.error("❌ Sistema {specialty} hierárquico não inicializado!")
            return "❌ Sistema {specialty} hierárquico não inicializado."
        
        try:
            logger.info("🔄 Delegando para hierarquia {specialty} (ASYNC)...")
            
            # Se houver sugestões da LLM, tentar usar o agente mais relevante primeiro
            if sub_agentes_sugeridos and len(sub_agentes_sugeridos) > 0:
                agente_principal = sub_agentes_sugeridos[0]
                logger.info(f"🎯 Priorizando sub-agente sugerido: {{agente_principal}}")
                
                # Adicionar dica no contexto para o hierarchical agent
                pergunta_com_dica = f"[SUGESTÃO_AGENTE: {{agente_principal}}] {{pergunta}}"
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
            logger.info(f"📊 Delegações recentes: {{stats.get('recent_delegations', [])}}")
            logger.info(f"✅ {identifier} Coordinator respondeu com {{len(resultado)}} caracteres (ASYNC)")
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento hierárquico (ASYNC): {{e}}")
            # Fallback para agente base
            if self.base_agent:
                return await asyncio.to_thread(
                    self.base_agent.processar_pergunta,
                    pergunta,
                    user_profile
                )
            else:
                return "❌ Erro no sistema de {specialty}. Tente novamente ou contate o suporte."
    
    def get_info(self) -> Dict:
        """Retorna informações sobre a hierarquia {specialty}"""
        if not self.hierarchical_agent:
            return {{"status": "not_initialized"}}
        
        return {{
            "status": "active",
            "base_agent": self.base_agent.config.name if self.base_agent else "N/A",
            "hierarchy_stats": self.hierarchical_agent.get_hierarchy_stats(),
            "debug_mode": self.debug,
            "tipo": "async"
        }}


# Factory function assíncrona
async def criar_{identifier}_coordinator_async(*, debug: bool = False) -> Optional[{identifier}CoordinatorAsync]:
    """Cria e inicializa o coordenador {specialty} hierárquico de forma ASSÍNCRONA"""
    
    coordinator = {identifier}CoordinatorAsync(debug=debug)
    
    if await coordinator.initialize_async():
        logger.info("🎉 {identifier} Coordinator ASYNC inicializado com sucesso!")
        return coordinator
    else:
        logger.error("❌ Falha na inicialização do {identifier} Coordinator ASYNC")
        return None


if __name__ == "__main__":
    import asyncio
    
    async def test_{identifier}_coordinator():
        logger.info("🧪 Teste do {identifier} Coordinator ASYNC")
        
        coordinator = await criar_{identifier}_coordinator_async(debug=True)
        
        if coordinator:
            perfil_demo = {{
                "Nome": "Teste Usuario",
                "Cargo": "Analista",
                "Departamento": "{specialty}",
                "nivel_hierarquico": 2,
                "geografia": "BR"
            }}
            
            pergunta_teste = "Teste de pergunta para {specialty}"
            
            resposta = await coordinator.processar_pergunta_async(
                pergunta_teste,
                perfil_demo
            )
            
            print(f"\\n📋 Resposta: {{resposta}}")
            print(f"\\n📊 Info: {{coordinator.get_info()}}")
        
    asyncio.run(test_{identifier}_coordinator())
'''
    
    def _generate_default_prompt(self, config: AgentConfig) -> str:
        """Gera prompt padrão para o agente"""
        
        return f"""Você é {config.name}, um especialista em {config.specialty}. Você faz parte do ecossistema Neoson e orienta colaboradores internos com dúvidas relacionadas à {config.specialty}.

IMPORTANTE: Baseie suas respostas SOMENTE nas informações do contexto fornecido abaixo.

DIRETRIZES DE RESPOSTA:
- Adote tom profissional, cordial e acessível
- Explique termos técnicos quando necessário
- Mencione histórico prévio quando aplicável
- Varie saudações e evite repetição excessiva
- Utilize emojis moderadamente para humanizar a conversa (opcional)
- Alerte quando o conteúdo parecer desatualizado ou incompleto

CASOS ESPECIAIS:
- Sem informação relevante: "Não localizei essa informação na base atual. Recomendo acionar o time responsável ou registrar um ticket conforme o procedimento padrão."
- Informação restrita: "Essa informação é restrita. Solicite autorização formal à liderança ou registre um ticket justificando a necessidade."
- Conteúdo possivelmente obsoleto: "⚠️ Atenção: essa informação pode estar desatualizada. Valide com o time responsável antes de seguir."

{{historico_conversa}}CONTEXTO DISPONÍVEL:
{{contexto}}

PERGUNTA DO COLABORADOR:
{{pergunta}}

RESPOSTA (considere {config.specialty.lower()} e histórico ao responder):"""
    
    async def _generate_agent_html(self, config: AgentConfig, agent_type: str) -> Path:
        """Gera arquivo HTML para visualização do agente"""
        
        from datetime import datetime
        
        # Ler template HTML
        template_path = self.base_path / "templates" / "agent_template.html"
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
        except FileNotFoundError:
            print(f"⚠️ [Factory] Template HTML não encontrado em {template_path}")
            # Criar um HTML simples se template não existir
            html_template = self._get_simple_html_template()
        
        # Escolher ícone emoji baseado na especialidade
        icon_emoji = self._get_icon_emoji(config.specialty, agent_type)
        
        # Preparar keywords HTML
        keywords_html = "\n                ".join([
            f'<span class="keyword-tag">{keyword}</span>'
            for keyword in config.keywords
        ]) if config.keywords else '<span class="keyword-tag">Nenhuma palavra-chave definida</span>'
        
        # Preparar seção de ferramentas
        tools_section = ""
        if config.enable_mcp_tools and config.allowed_tools:
            tools_list = "\n                    ".join([
                f'<li>{tool}</li>'
                for tool in config.allowed_tools
            ])
            tools_section = f'''
            <div class="tools-section">
                <h3>🔧 Ferramentas MCP Disponíveis</h3>
                <ul class="tools-list">
                    {tools_list}
                </ul>
            </div>
            '''
        
        # Preparar meta de tabela (apenas para subagentes)
        table_meta = ""
        if agent_type == "subagent" and config.table_name:
            table_meta = f'''
                <div class="meta-item">
                    <div class="meta-label">Base de Dados</div>
                    <div class="meta-value">{config.table_name}</div>
                </div>
            '''
        
        # Tipo para exibição
        agent_type_display = "Subagente" if agent_type == "subagent" else "Coordenador"
        
        # Substituir variáveis no template
        html_content = html_template.format(
            name=config.name,
            identifier=config.identifier,
            specialty=config.specialty,
            description=config.description,
            agent_type_display=agent_type_display,
            icon_emoji=icon_emoji,
            keywords_html=keywords_html,
            tools_section=tools_section,
            table_meta=table_meta,
            created_at=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        )
        
        # Salvar arquivo HTML
        html_file_path = self.base_path / "templates" / "agents" / f"{config.identifier}.html"
        
        # Criar diretório se não existir
        html_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 [Factory] HTML criado: {html_file_path}")
        
        return html_file_path
    
    def _get_icon_emoji(self, specialty: str, agent_type: str) -> str:
        """Retorna emoji baseado na especialidade"""
        
        icon_map = {
            "TI": "💻",
            "Desenvolvimento": "👨‍💻",
            "Infraestrutura": "🖥️",
            "Governança": "⚖️",
            "Suporte": "🎧",
            "Service Desk": "📞",
            "End-User": "👤",
            "RH": "👥",
            "Recursos Humanos": "👥",
            "Financeiro": "💰",
            "Vendas": "📈",
            "CRM": "🤝",
            "Marketing": "📢",
            "Operações": "⚙️",
            "Segurança": "🔒",
            "Dados": "📊",
            "Analytics": "📉"
        }
        
        # Buscar por palavra-chave na especialidade
        for key, emoji in icon_map.items():
            if key.lower() in specialty.lower():
                return emoji
        
        # Ícone padrão baseado no tipo
        return "🤖" if agent_type == "subagent" else "👨‍✈️"
    
    def _get_simple_html_template(self) -> str:
        """Retorna template HTML simples caso o arquivo não exista"""
        return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - {specialty}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .card {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; }}
        .meta {{ color: #666; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>{icon_emoji} {name}</h1>
        <p class="meta"><strong>Especialidade:</strong> {specialty}</p>
        <p class="meta"><strong>ID:</strong> {identifier}</p>
        <p>{description}</p>
        {keywords_html}
        {tools_section}
        {table_meta}
        <hr>
        <p><small>Criado em: {created_at}</small></p>
    </div>
</body>
</html>'''


# Funções utilitárias
async def create_subagent_from_config(
    name: str,
    identifier: str,
    specialty: str,
    description: str,
    keywords: List[str],
    **kwargs
) -> Dict[str, Any]:
    """Helper para criar subagente rapidamente"""
    
    factory = AgentFactory()
    
    agent_config = AgentConfig(
        name=name,
        identifier=identifier,
        specialty=specialty,
        description=description,
        agent_type=AgentType.SUBAGENT,
        keywords=keywords,
        **kwargs
    )
    
    return await factory.create_agent(agent_config)


async def create_coordinator_from_config(
    name: str,
    identifier: str,
    specialty: str,
    description: str,
    children_agents: List[str],
    **kwargs
) -> Dict[str, Any]:
    """Helper para criar coordenador rapidamente"""
    
    factory = AgentFactory()
    
    agent_config = AgentConfig(
        name=name,
        identifier=identifier,
        specialty=specialty,
        description=description,
        agent_type=AgentType.COORDINATOR,
        children_agents=children_agents,
        **kwargs
    )
    
    return await factory.create_agent(agent_config)
