"""Agente especializado em Recursos Humanos - VERSÃO ASSÍNCRONA
Baseado no BaseSubagent mas com suporte completo a operações assíncronas"""

from __future__ import annotations

from textwrap import dedent
from typing import Optional
import asyncio

from subagents.base_subagent import SubagentConfig
from dal.postgres_dal_async import PostgresDALAsync
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from core.config import config

PROMPT_TEMPLATE = dedent(
    """
    Você é Ana, uma especialista em Recursos Humanos. Você faz parte do ecossistema Neoson e orienta colaboradores internos com dúvidas relacionadas à área de RH.

    IMPORTANTE: Baseie suas respostas SOMENTE nas informações do contexto fornecido abaixo.

    DIRETRIZES DE RESPOSTA:
    - Adote tom profissional, cordial e acessível
    - Explique políticas e procedimentos de forma clara e compreensível
    - Mencione histórico prévio quando aplicável
    - Varie saudações e evite repetição excessiva
    - Utilize emojis moderadamente para humanizar a conversa (opcional)
    - Alerte quando o conteúdo parecer desatualizado ou incompleto

    CASOS ESPECIAIS:
    - Sem informação relevante: "Não localizei essa informação na base atual. Recomendo acionar o time de RH diretamente ou registrar um ticket conforme o procedimento padrão."
    - Informação restrita: "Essa informação é confidencial. Solicite autorização formal à liderança de RH ou registre um ticket justificando a necessidade."
    - Conteúdo possivelmente obsoleto: "⚠️ Atenção: essa informação pode estar desatualizada. Valide com o time de RH antes de seguir."

    {historico_conversa}CONTEXTO DISPONÍVEL:
    {contexto}

    PERGUNTA DO COLABORADOR:
    {pergunta}

    RESPOSTA (considere políticas de RH e histórico ao responder):
    """
).strip()

KEYWORDS = [
    'rh', 'recursos humanos', 'férias', 'benefícios', 'salário', 'contrato',
    'home office', 'folga', 'falta', 'atestado', 'demissão', 'contratação',
    'política', 'procedimento', 'vale refeição', 'vale transporte', 'plr',
    'décimo terceiro', 'licença', 'maternidade', 'paternidade', 'treinamento',
    'desenvolvimento', 'carreira', 'avaliação', 'desempenho', 'ponto',
    'horário', 'escala', 'banco de horas', 'overtime', 'extra'
]


class AgenteRHAsync:
    """Agente especializado em Recursos Humanos com operações ASSÍNCRONAS"""

    def __init__(self, *, debug: bool = False) -> None:
        self.config = SubagentConfig(
            identifier="rh",
            name="Ana",
            specialty="Recursos Humanos",
            description="Especialista em recursos humanos, políticas de pessoal, benefícios e procedimentos internos",
            keywords=KEYWORDS,
            table_name="knowledge_hr",
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
            max_tokens=800
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
            return f"Desculpe, encontrei um erro ao processar sua pergunta sobre RH. Por favor, tente novamente."
        
        finally:
            await self.dal_async.disconnect()
    
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
        
        # Pegar as últimas 3 interações
        ultimas_interacoes = historico[-3:]
        
        historico_parts = ["HISTÓRICO RECENTE DA CONVERSA:"]
        for i, (perg, resp) in enumerate(ultimas_interacoes, 1):
            historico_parts.append(f"\nInteração {i}:")
            historico_parts.append(f"Usuário: {perg}")
            historico_parts.append(f"Ana: {resp[:200]}...")  # Resumir resposta
        
        historico_parts.append("\n")
        return "\n".join(historico_parts)
    
    def _adicionar_memoria(self, usuario_id: str, pergunta: str, resposta: str):
        """Adiciona interação à memória"""
        if usuario_id not in self.memoria_conversas:
            self.memoria_conversas[usuario_id] = []
        
        self.memoria_conversas[usuario_id].append((pergunta, resposta))
        
        # Manter apenas as últimas 10 interações
        if len(self.memoria_conversas[usuario_id]) > 10:
            self.memoria_conversas[usuario_id] = self.memoria_conversas[usuario_id][-10:]
    
    def obter_info_agente(self) -> dict:
        """Retorna informações do agente"""
        return {
            'identifier': self.config.identifier,
            'name': self.config.name,
            'specialty': self.config.specialty,
            'descricao': self.config.description,
            'keywords': self.config.keywords,
            'table_name': self.config.table_name,
            'tipo': 'async',
            'memoria_usuarios': len(self.memoria_conversas)
        }


def criar_agente_rh_async(*, debug: bool = False) -> Optional[AgenteRHAsync]:
    """Factory function para criar o agente de RH assíncrono"""
    try:
        if debug:
            print("🏭 Criando agente RH assíncrono...")

        agente = AgenteRHAsync(debug=debug)

        if debug:
            print(f"✅ Agente RH Async criado: {agente.config.name}")
            print(f"📊 Keywords: {len(agente.config.keywords)} termos")
            print(f"🗄️ Tabela: {agente.config.table_name}")

        return agente

    except Exception as e:
        if debug:
            print(f"❌ Erro ao criar agente RH async: {e}")
        return None


if __name__ == "__main__":
    import asyncio
    
    async def teste_agente():
        """Teste do agente RH assíncrono"""
        print("🧪 Testando Agente RH Async...")

        agente = criar_agente_rh_async(debug=True)

        if agente:
            print("✅ Agente RH Async inicializado com sucesso!")

            # Perfil de teste
            perfil_teste = {
                "Nome": "João Silva",
                "Cargo": "Analista",
                "Departamento": "RH",
                "Nivel_Hierarquico": 3,
                "Geografia": "BR",
                "Projetos": ["Projeto X"]
            }

            # Teste de pergunta
            pergunta_teste = "Qual é a política de férias da empresa?"

            print(f"\n🎯 Pergunta de teste: {pergunta_teste}")
            resposta = await agente.processar_async(pergunta_teste, perfil_teste)
            print(f"🤖 Resposta: {resposta[:200]}...")

            print("\n📊 Informações do agente:")
            info = agente.obter_info_agente()
            for chave, valor in info.items():
                print(f"  {chave}: {valor}")
        else:
            print("❌ Falha na inicialização do agente RH Async")
    
    asyncio.run(teste_agente())
