"""Agente especializado em Teste - VERSÃO ASSÍNCRONA
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
Você é Teste Reload, um especialista em Teste. Você faz parte do ecossistema Neoson e orienta colaboradores internos com dúvidas relacionadas à Teste.

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

{historico_conversa}CONTEXTO DISPONÍVEL:
{contexto}

PERGUNTA DO COLABORADOR:
{pergunta}

RESPOSTA (considere teste e histórico ao responder):
    """
).strip()

KEYWORDS = ['teste']


class Agenteteste_reloadAsync:
    """Agente especializado em Teste com operações ASSÍNCRONAS"""

    def __init__(self, *, debug: bool = False) -> None:
        self.config = SubagentConfig(
            identifier="teste_reload",
            name="Teste Reload",
            specialty="Teste",
            description="teste",
            keywords=KEYWORDS,
            table_name="knowledge_teste_reload",
            prompt_template=PROMPT_TEMPLATE,
            debug=debug
        )
        
        # Inicializar componentes assíncronos
        self.dal_async = PostgresDALAsync()
        self.llm = None
        self.embeddings = None
        self.memoria_conversas = {}
        
        # Configuração de ferramentas MCP
        self.enable_mcp_tools = False
        self.mcp_tools_category = ""
        self.allowed_tools = []
        
        # Inicializar LLM e embeddings
        self._inicializar_llm()
    
    def _inicializar_llm(self):
        """Inicializa LLM e embeddings"""
        api_key = config.openai.api_key
        
        self.llm = ChatOpenAI(
            api_key=api_key,
            model="gpt-4o-mini",
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
            return "Desculpe, encontrei um erro ao processar sua pergunta sobre teste. Por favor, tente novamente."
        
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
            conteudo = doc.get('conteudo', doc.get('content', ''))
            metadata_str = doc.get('metadata', {})
            
            contexto_parts.append(f"[Documento {i}]")
            if metadata_str:
                contexto_parts.append(f"Metadados: {metadata_str}")
            contexto_parts.append(conteudo)
            contexto_parts.append("")  # Linha em branco
        
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


def criar_agente_teste_reload_async(*, debug: bool = False) -> Agenteteste_reloadAsync:
    """Factory function para criar o agente de Teste assíncrono"""
    return Agenteteste_reloadAsync(debug=debug)


if __name__ == "__main__":
    import asyncio
    
    async def test_agente_teste_reload_async():
        agente = criar_agente_teste_reload_async(debug=True)
        
        perfil_demo = {
            "Nome": "Teste Usuario",
            "Cargo": "Analista",
            "Departamento": "Teste",
            "nivel_hierarquico": 2,
            "geografia": "BR",
            "projetos": ["N/A"],
        }

        perguntas_demo = [
            "Teste de pergunta para Teste",
        ]

        for pergunta in perguntas_demo:
            print(f"\n❓ Pergunta: {pergunta}")
            resposta = await agente.processar_async(pergunta, perfil_demo)
            print(f"🤖 Teste Reload: {resposta}")
            print("-" * 80)
    
    asyncio.run(test_agente_teste_reload_async())
