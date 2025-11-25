"""Agente especializado em Governança de TI - VERSÃO ASSÍNCRONA
Baseado no BaseSubagent mas com suporte completo a operações assíncronas"""

from __future__ import annotations

from textwrap import dedent
import asyncio

from subagents.base_subagent import SubagentConfig
from dal.postgres_dal_async import PostgresDALAsync
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from core.config import config

PROMPT_TEMPLATE = dedent(
    """
    Você é Ariel, um(a) especialista em Governança de TI. Você faz parte do ecossistema Neoson e orienta colaboradores internos com dúvidas relacionadas à especialidade.

    IMPORTANTE:
    1. RESPONDA SEMPRE NO MESMO IDIOMA da pergunta do usuário (português, inglês, espanhol, etc.)
    2. CONSULTE TODAS as documentações disponíveis independente do idioma (português, inglês, espanhol)
    3. TRADUZA e ADAPTE o conteúdo dos documentos para o idioma da resposta
    4. CITE SEMPRE as fontes originais com seus nomes originais

    Somos uma empresa global e seguimos normas nacionais e internacionais de governança, compliance e segurança da informação.

    ESTRUTURA DA RESPOSTA:
    - Para cada política/norma encontrada, organize por fonte
    - Traduza o conteúdo para o idioma da pergunta mantendo precisão técnica
    - Indique claramente qual norma/política cada resposta se refere
    - Mantenha os nomes originais dos documentos nas citações

    DIRETRIZES DE RESPOSTA:
    - Detecte automaticamente o idioma da pergunta e responda no mesmo idioma
    - Adote tom profissional, cordial e acessível
    - Explique termos técnicos quando necessário
    - Para documentos em inglês respondendo em português: traduza mantendo termos técnicos precisos
    - Para documentos em português respondendo em inglês: traduza mantendo conformidade regulatória
    - Mencione histórico prévio quando aplicável
    - Utilize emojis moderadamente para humanizar a conversa (opcional)
    - Alerte quando o conteúdo parecer desatualizado

    CASOS ESPECIAIS POR IDIOMA:
    
    Se pergunta em PORTUGUÊS:
    - Sem informação: "Não localizei essa informação na base atual. Recomendo acionar o time responsável ou registrar um ticket."
    - Informação restrita: "Essa informação é restrita. Solicite autorização formal à liderança."
    - Conteúdo obsoleto: "⚠️ Atenção: essa informação pode estar desatualizada. Valide com o time responsável."
    
    Se pergunta em INGLÊS:
    - Sem informação: "I couldn't find this information in the current database. I recommend contacting the responsible team or submitting a ticket."
    - Informação restrita: "This information is restricted. Please request formal authorization from leadership."
    - Conteúdo obsoleto: "⚠️ Warning: this information may be outdated. Please validate with the responsible team."
    
    Se pergunta em ESPANHOL:
    - Sem informação: "No pude encontrar esta información en la base actual. Recomiendo contactar al equipo responsable o crear un ticket."
    - Informação restrita: "Esta información es restringida. Solicite autorización formal del liderazgo."
    - Conteúdo obsoleto: "⚠️ Atención: esta información puede estar desactualizada. Valide con el equipo responsable."

    {historico_conversa}CONTEXTO DISPONÍVEL:
    {contexto}

    PERGUNTA DO COLABORADOR:
    {pergunta}

    RESPOSTA (no mesmo idioma da pergunta, consultando documentos em qualquer idioma):
    """
).strip()

KEYWORDS = [
    'governança', 'compliance', 'política', 'procedimento', 'norma', 
    'auditoria', 'controle', 'risco', 'segurança', 'iso', 'itil', 
    'cobit', 'sox', 'gdpr', 'lgpd', 'data governance', 'cybersecurity',
    'governance', 'policy', 'standard', 'audit', 'risk', 'security',
    'gobernanza', 'cumplimiento', 'politica', 'auditoria', 'riesgo'
]


class AgenteGovernanceAsync:
    """Agente especializado em Governança de TI com operações ASSÍNCRONAS"""

    def __init__(self, *, debug: bool = False) -> None:
        self.config = SubagentConfig(
            identifier="governance",
            name="Ariel",
            specialty="Governança de TI",
            description="Especialista em governança de TI, compliance, políticas e procedimentos corporativos",
            keywords=KEYWORDS,
            table_name="knowledge_it_governance_delivery_methods",
            prompt_template=PROMPT_TEMPLATE,
            debug=debug
        )
        
        # Inicializar componentes assíncronos
        self.dal_async = PostgresDALAsync()
        self.llm = None
        self.embeddings = None
        self.memoria_conversas = {}
        
        # Inicializar LLM e embeddings
        self._inicializar_llm()
    
    def _inicializar_llm(self):
        """Inicializa LLM e embeddings"""
        api_key = config.openai.api_key
        
        self.llm = ChatOpenAI(
            api_key=api_key,
            model=config.openai.chat_model,
            temperature=0.3,
            max_tokens=10000
        )
        
        self.embeddings = OpenAIEmbeddings(
            api_key=api_key,
            model=config.openai.embedding_model
        )
    
    async def processar_async(self, pergunta: str, user_profile: dict) -> str:
        """Processa pergunta de forma ASSÍNCRONA"""
        try:
            if self.config.debug:
                print(f"🔄 [{self.config.name}] Processando pergunta (ASYNC): '{pergunta[:50]}...'")
            
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
                print(f"📊 [{self.config.name}] Encontrados {len(search_result.documents)} documentos relevantes")
            
            # Preparar contexto
            contexto_str = self._preparar_contexto(search_result.documents)
            
            # Preparar histórico
            usuario_id = f"{user_profile.get('Nome', 'usuario')}_{user_profile.get('Departamento', 'geral')}"
            historico_str = self._preparar_historico(usuario_id)
            
            # Preparar prompt
            prompt_final = self.config.prompt_template.format(
                historico_conversa=historico_str,
                contexto=contexto_str,
                pergunta=pergunta
            )
            
            # Gerar resposta de forma assíncrona
            if self.config.debug:
                print(f"🤖 [{self.config.name}] Gerando resposta com LLM (ASYNC)...")
            
            resposta = await asyncio.to_thread(
                self.llm.invoke,
                prompt_final
            )
            
            resposta_texto = resposta.content if hasattr(resposta, 'content') else str(resposta)
            
            # Armazenar na memória
            self._adicionar_memoria(usuario_id, pergunta, resposta_texto)
            
            if self.config.debug:
                print(f"✅ [{self.config.name}] Resposta gerada com {len(resposta_texto)} caracteres")
            
            return resposta_texto
            
        except Exception as e:
            error_msg = f"❌ Erro ao processar pergunta (Agente {self.config.name}): {str(e)}"
            print(error_msg)
            
            # Mensagem específica para timeout de conexão
            if "Timeout" in str(e) or "tempo limite" in str(e).lower():
                return (
                    "⚠️ **Problema de Conectividade**\n\n"
                    "Não consegui acessar a base de conhecimento de Governança devido a um problema de conexão com o banco de dados.\n\n"
                    "**Possíveis causas:**\n"
                    "- VPN desconectada ou instável\n"
                    "- Firewall bloqueando acesso ao banco\n"
                    "- Servidor de banco de dados fora do ar\n\n"
                    "**Sugestões:**\n"
                    "1. Verifique sua conexão VPN\n"
                    "2. Tente novamente em alguns segundos\n"
                    "3. Contate o suporte de TI se o problema persistir"
                )
            
            return "Desculpe, encontrei um erro ao processar sua pergunta sobre governança. Por favor, tente novamente."
        
        finally:
            await self.dal_async.disconnect()
    
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
                metadata_parts.append(f"Fonte: {fonte}")
            if idioma:
                metadata_parts.append(f"Idioma: {idioma}")
            if validade:
                metadata_parts.append(f"Validade: {validade}")
            if responsavel:
                metadata_parts.append(f"Responsável: {responsavel}")

            metadata_dict = doc.get('metadata')
            if isinstance(metadata_dict, dict) and metadata_dict:
                metadata_parts.append(f"Metadados extras: {metadata_dict}")

            contexto_parts.append(f"[Documento {i}]")
            if metadata_parts:
                contexto_parts.append(" | ".join(metadata_parts))
            contexto_parts.append(conteudo)
            contexto_parts.append("")

        if not contexto_parts:
            return "Nenhum documento relevante encontrado na base de conhecimento."
        
        return "\n".join(contexto_parts)
    
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
            historico_parts.append(f"[Interação {i}]")
            historico_parts.append(f"Pergunta: {pergunta_ant}")
            historico_parts.append(f"Resposta: {resposta_ant[:200]}...")
            historico_parts.append("")
        
        historico_parts.append("---")
        return "\n".join(historico_parts)
    
    def _adicionar_memoria(self, usuario_id: str, pergunta: str, resposta: str):
        """Adiciona interação à memória de conversas"""
        if usuario_id not in self.memoria_conversas:
            self.memoria_conversas[usuario_id] = []
        
        self.memoria_conversas[usuario_id].append((pergunta, resposta))
        
        # Manter apenas últimas 10 interações por usuário
        if len(self.memoria_conversas[usuario_id]) > 10:
            self.memoria_conversas[usuario_id] = self.memoria_conversas[usuario_id][-10:]

    def processar_pergunta(self, pergunta: str, user_profile: dict) -> str:
        """Método síncrono de compatibilidade para o sistema hierárquico"""
        import asyncio
        try:
            # Criar e executar loop de eventos se necessário
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Já existe um loop rodando, criar uma nova tarefa
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self.processar_async(pergunta, user_profile)
                        )
                        return future.result()
                else:
                    return loop.run_until_complete(self.processar_async(pergunta, user_profile))
            except RuntimeError:
                # Não há loop de eventos, criar um novo
                return asyncio.run(self.processar_async(pergunta, user_profile))
        except Exception as e:
            print(f"❌ Erro no método de compatibilidade: {e}")
            return "Desculpe, encontrei um erro ao processar sua pergunta sobre governança. Por favor, tente novamente."


def criar_agente_governance_async(*, debug: bool = False) -> AgenteGovernanceAsync:
    """Factory function para criar o agente de Governança de TI assíncrono"""
    return AgenteGovernanceAsync(debug=debug)


if __name__ == "__main__":
    async def test_agente_governance_async():
        agente = criar_agente_governance_async(debug=True)
        
        perfil_demo = {
            "Nome": "Fulano de Tal",
            "Cargo": "Analista de Governança",
            "Departamento": "Governança",
            "nivel_hierarquico": 3,
            "geografia": "BR",
            "projetos": ["N/A"],
        }

        perguntas_demo = [
            "Quais são as políticas de segurança da informação?",
            "Como funciona o processo de auditoria interna?",
        ]

        for pergunta in perguntas_demo:
            print(f"\n❓ Pergunta: {pergunta}")
            resposta = await agente.processar_async(pergunta, perfil_demo)
            print(f"🤖 Ariel: {resposta}")
            print("-" * 80)
    
    asyncio.run(test_agente_governance_async())