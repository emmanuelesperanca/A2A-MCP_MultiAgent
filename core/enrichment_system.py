"""
Sistema de Enriquecimento de Respostas do Neoson

Adiciona valor extra às respostas com:
- Documentos relacionados
- FAQs similares
- Especialistas de contato
- Sugestões de próximas perguntas
- Glossário de termos técnicos

Autor: Neoson Team
Data: 2025-10-09
"""

import asyncio
import re
from typing import List, Dict, Any, Optional
import asyncpg
from langchain_openai import OpenAIEmbeddings

from core.config import ConfigManager


class ResponseEnricher:
    """Enriquece respostas do Neoson com informações adicionais de valor"""
    
    def __init__(self, config: ConfigManager, db_pool: asyncpg.Pool):
        self.config = config
        self.db_pool = db_pool
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=config.openai.api_key
        )
        
        # Mapeamento de especialistas por área
        self.especialistas_map = {
            'ti': {
                'governance': {
                    'nome': 'Ariel - Governança de TI',
                    'email': 'ariel.governance@neoson.com',
                    'telefone': '+55 11 1234-5678',
                    'especialidades': ['Políticas', 'Compliance', 'LGPD', 'ISO 27001']
                },
                'infrastructure': {
                    'nome': 'Alice - Infraestrutura',
                    'email': 'alice.infra@neoson.com',
                    'telefone': '+55 11 1234-5679',
                    'especialidades': ['Servidores', 'Redes', 'Cloud', 'Backup']
                },
                'development': {
                    'nome': 'Carlos - Desenvolvimento',
                    'email': 'carlos.dev@neoson.com',
                    'telefone': '+55 11 1234-5680',
                    'especialidades': ['APIs', 'Deploy', 'CI/CD', 'Features']
                },
                'enduser': {
                    'nome': 'Marina - Suporte',
                    'email': 'marina.suporte@neoson.com',
                    'telefone': '+55 11 1234-5681',
                    'especialidades': ['Login', 'Senha', 'Acesso', 'Dúvidas']
                }
            },
            'rh': {
                'general': {
                    'nome': 'Paula - Recursos Humanos',
                    'email': 'paula.rh@neoson.com',
                    'telefone': '+55 11 1234-5682',
                    'especialidades': ['Férias', 'Benefícios', 'Folha', 'Contratação']
                }
            }
        }
        
        # Termos técnicos comuns e suas definições
        self.glossario_base = {
            'LGPD': 'Lei Geral de Proteção de Dados - Legislação brasileira que regula o tratamento de dados pessoais',
            'ISO 27001': 'Norma internacional para gestão de segurança da informação',
            'FDA CFR 21 Part 11': 'Regulamentação americana sobre assinaturas e registros eletrônicos',
            'RDC ANVISA': 'Resolução da Diretoria Colegiada da Agência Nacional de Vigilância Sanitária',
            'RAG': 'Retrieval-Augmented Generation - Técnica que combina busca de documentos com geração de texto',
            'Embedding': 'Representação vetorial de texto que captura significado semântico',
            'API': 'Application Programming Interface - Interface para comunicação entre sistemas',
            'Cloud': 'Computação em nuvem - Recursos de TI acessados via internet',
            'Backup': 'Cópia de segurança de dados para recuperação em caso de perda',
            'Deploy': 'Processo de colocar uma aplicação em produção',
            'CI/CD': 'Continuous Integration/Continuous Deployment - Automação de integração e deploy',
            'VPN': 'Virtual Private Network - Rede privada virtual para acesso seguro',
            'MFA': 'Multi-Factor Authentication - Autenticação com múltiplos fatores',
            'SLA': 'Service Level Agreement - Acordo de nível de serviço',
            'ABNT': 'Associação Brasileira de Normas Técnicas',
            'Compliance': 'Conformidade com normas, leis e regulamentações',
            'Governança': 'Conjunto de práticas para gestão e controle de recursos de TI'
        }
    
    async def enrich(
        self, 
        resposta_principal: str, 
        pergunta: str, 
        agente_usado: str, 
        perfil_usuario: Dict[str, Any],
        base_conhecimento: str = None
    ) -> Dict[str, Any]:
        """
        Enriquece uma resposta com informações adicionais
        
        Args:
            resposta_principal: Resposta gerada pelo agente
            pergunta: Pergunta original do usuário
            agente_usado: Nome do agente que respondeu
            perfil_usuario: Perfil completo do usuário
            base_conhecimento: Nome da base de conhecimento usada
        
        Returns:
            Dict com resposta enriquecida
        """
        # Executar enriquecimentos em paralelo para melhor performance
        tasks = [
            self._get_related_docs(pergunta, base_conhecimento, perfil_usuario),
            self._get_similar_faqs(pergunta),
            self._generate_suggestions(pergunta, resposta_principal, agente_usado),
            self._extract_glossary(resposta_principal)
        ]
        
        related_docs, similar_faqs, suggestions, glossary = await asyncio.gather(*tasks)
        
        # Obter contatos de especialistas (síncrono)
        expert_contacts = self._get_expert_contacts(agente_usado, perfil_usuario)
        
        return {
            'resposta_principal': resposta_principal,
            'documentos_relacionados': related_docs,
            'faqs_similares': similar_faqs,
            'especialistas_contato': expert_contacts,
            'proximas_sugestoes': suggestions,
            'glossario': glossary
        }
    
    async def _get_related_docs(
        self, 
        pergunta: str, 
        base_conhecimento: Optional[str],
        perfil_usuario: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Busca documentos relacionados à pergunta"""
        try:
            if not base_conhecimento:
                return []
            
            # Gerar embedding da pergunta
            pergunta_embedding = self.embeddings.embed_query(pergunta)
            
            # Buscar documentos similares (diferentes dos já usados na resposta)
            query = f"""
                SELECT 
                    document_name,
                    chunk_text,
                    metadata,
                    1 - (embedding <=> $1::vector) as similarity
                FROM {base_conhecimento}
                WHERE 1 - (embedding <=> $1::vector) > 0.6
                    AND (metadata->>'Areas_liberadas' = 'ALL' 
                         OR $2 = ANY(string_to_array(metadata->>'Areas_liberadas', ',')))
                ORDER BY similarity DESC
                LIMIT 5
            """
            
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    query, 
                    pergunta_embedding,
                    perfil_usuario.get('Departamento', 'ALL')
                )
            
            docs = []
            seen_docs = set()
            
            for row in rows:
                doc_name = row['document_name']
                if doc_name not in seen_docs:
                    seen_docs.add(doc_name)
                    docs.append({
                        'titulo': doc_name,
                        'preview': row['chunk_text'][:200] + '...',
                        'relevancia': round(row['similarity'] * 100, 1),
                        'metadata': row['metadata']
                    })
            
            return docs[:3]  # Limitar a 3 documentos
            
        except Exception as e:
            print(f"❌ Erro ao buscar documentos relacionados: {e}")
            return []
    
    async def _get_similar_faqs(self, pergunta: str) -> List[Dict[str, str]]:
        """Busca FAQs similares já respondidas anteriormente"""
        try:
            # Gerar embedding da pergunta
            pergunta_embedding = self.embeddings.embed_query(pergunta)
            
            # Buscar no histórico de FAQs (tabela que será criada)
            query = """
                SELECT 
                    pergunta,
                    resposta_curta,
                    rating_medio,
                    1 - (pergunta_embedding <=> $1::vector) as similarity
                FROM faqs_historico
                WHERE 1 - (pergunta_embedding <=> $1::vector) > 0.75
                    AND rating_medio >= 4.0
                ORDER BY similarity DESC, rating_medio DESC
                LIMIT 3
            """
            
            async with self.db_pool.acquire() as conn:
                # Verificar se tabela existe
                table_exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'faqs_historico'
                    )
                """)
                
                if not table_exists:
                    return []
                
                rows = await conn.fetch(query, pergunta_embedding)
            
            faqs = []
            for row in rows:
                faqs.append({
                    'pergunta': row['pergunta'],
                    'resposta': row['resposta_curta'],
                    'rating': round(row['rating_medio'], 1),
                    'similaridade': round(row['similarity'] * 100, 1)
                })
            
            return faqs
            
        except Exception as e:
            print(f"❌ Erro ao buscar FAQs similares: {e}")
            return []
    
    def _get_expert_contacts(
        self, 
        agente_usado: str, 
        perfil_usuario: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Retorna contatos de especialistas relevantes"""
        try:
            contacts = []
            
            # Determinar área principal
            area_principal = 'ti' if 'ti' in agente_usado.lower() else 'rh'
            
            # Se for TI hierárquico, identificar subespecialista
            if 'hierárquico' in agente_usado.lower() or 'governance' in agente_usado.lower():
                # Adicionar especialista de governance
                if 'governance' in self.especialistas_map['ti']:
                    contacts.append(self.especialistas_map['ti']['governance'])
            
            # Adicionar especialista geral da área
            if area_principal in self.especialistas_map:
                # Adicionar primeiro especialista disponível se não tiver nenhum
                if not contacts and 'general' in self.especialistas_map[area_principal]:
                    contacts.append(self.especialistas_map[area_principal]['general'])
                elif not contacts:
                    # Pegar primeiro especialista disponível
                    first_key = list(self.especialistas_map[area_principal].keys())[0]
                    contacts.append(self.especialistas_map[area_principal][first_key])
            
            # Adicionar gerente do departamento do usuário (se disponível)
            departamento = perfil_usuario.get('Departamento', '')
            if departamento and departamento.upper() == 'TI':
                contacts.append({
                    'nome': 'Gestor de TI',
                    'email': 'gestor.ti@neoson.com',
                    'telefone': '+55 11 1234-5690',
                    'especialidades': ['Gestão', 'Priorização', 'Recursos']
                })
            
            return contacts[:2]  # Limitar a 2 contatos
            
        except Exception as e:
            print(f"❌ Erro ao obter contatos de especialistas: {e}")
            return []
    
    async def _generate_suggestions(
        self, 
        pergunta: str, 
        resposta: str,
        agente_usado: str
    ) -> List[str]:
        """Gera sugestões de próximas perguntas usando LLM"""
        try:
            from langchain_openai import ChatOpenAI
            
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                openai_api_key=self.config.openai.api_key
            )
            
            prompt = f"""Com base na pergunta e resposta abaixo, gere 3 perguntas relacionadas que o usuário pode querer fazer em seguida.

PERGUNTA ORIGINAL: {pergunta}

RESPOSTA DADA: {resposta[:500]}...

INSTRUÇÕES:
- Gere perguntas práticas e acionáveis
- Explore aspectos não cobertos na resposta
- Mantenha o mesmo contexto/domínio
- Seja específico e direto

FORMATO: Retorne apenas as 3 perguntas, uma por linha, sem numeração ou marcadores.
"""
            
            response = await llm.ainvoke(prompt)
            suggestions_text = response.content.strip()
            
            # Parsear sugestões
            suggestions = [
                line.strip().lstrip('123.-•*') 
                for line in suggestions_text.split('\n') 
                if line.strip()
            ]
            
            return suggestions[:3]
            
        except Exception as e:
            print(f"❌ Erro ao gerar sugestões: {e}")
            # Fallback: sugestões genéricas baseadas no agente
            fallback_suggestions = {
                'ti': [
                    'Como posso solicitar acesso a um novo sistema?',
                    'Qual o procedimento para reportar um problema técnico?',
                    'Onde encontro a documentação técnica completa?'
                ],
                'rh': [
                    'Como faço para solicitar férias?',
                    'Onde consulto meu extrato de benefícios?',
                    'Qual o processo para atualizar meus dados cadastrais?'
                ]
            }
            
            area = 'ti' if 'ti' in agente_usado.lower() else 'rh'
            return fallback_suggestions.get(area, [])[:3]
    
    async def _extract_glossary(self, resposta: str) -> Dict[str, str]:
        """Extrai e define termos técnicos mencionados na resposta"""
        try:
            glossary = {}
            
            # Buscar termos do glossário base que aparecem na resposta
            resposta_upper = resposta.upper()
            
            for termo, definicao in self.glossario_base.items():
                termo_upper = termo.upper()
                # Buscar o termo como palavra completa (word boundary)
                pattern = r'\b' + re.escape(termo_upper) + r'\b'
                if re.search(pattern, resposta_upper):
                    glossary[termo] = definicao
            
            # Ordenar por ordem de aparição na resposta
            glossary_sorted = {}
            for termo in glossary.keys():
                pos = resposta_upper.find(termo.upper())
                glossary_sorted[termo] = (pos, glossary[termo])
            
            # Retornar ordenado e sem a posição
            result = {
                termo: definicao 
                for termo, (pos, definicao) in sorted(
                    glossary_sorted.items(), 
                    key=lambda x: x[1][0]
                )
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Erro ao extrair glossário: {e}")
            return {}


async def create_faqs_table(db_pool: asyncpg.Pool):
    """Cria tabela para armazenar histórico de FAQs"""
    query = """
        CREATE TABLE IF NOT EXISTS faqs_historico (
            id SERIAL PRIMARY KEY,
            pergunta TEXT NOT NULL,
            resposta_curta TEXT NOT NULL,
            resposta_completa TEXT,
            agente_usado VARCHAR(100),
            pergunta_embedding vector(1536),
            rating_medio FLOAT DEFAULT 0.0,
            total_votos INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_faqs_embedding 
        ON faqs_historico USING ivfflat (pergunta_embedding vector_cosine_ops)
        WITH (lists = 100);
        
        CREATE INDEX IF NOT EXISTS idx_faqs_rating 
        ON faqs_historico (rating_medio DESC);
    """
    
    async with db_pool.acquire() as conn:
        await conn.execute(query)
    
    print("✅ Tabela faqs_historico criada com sucesso!")


async def save_faq(
    db_pool: asyncpg.Pool,
    embeddings: OpenAIEmbeddings,
    pergunta: str,
    resposta: str,
    agente_usado: str
):
    """Salva uma FAQ no histórico"""
    try:
        # Gerar embedding
        pergunta_embedding = embeddings.embed_query(pergunta)
        
        # Criar resposta curta (primeiros 200 chars)
        resposta_curta = resposta[:200] + ('...' if len(resposta) > 200 else '')
        
        query = """
            INSERT INTO faqs_historico 
            (pergunta, resposta_curta, resposta_completa, agente_usado, pergunta_embedding)
            VALUES ($1, $2, $3, $4, $5::vector)
            ON CONFLICT DO NOTHING
        """
        
        async with db_pool.acquire() as conn:
            await conn.execute(
                query,
                pergunta,
                resposta_curta,
                resposta,
                agente_usado,
                pergunta_embedding
            )
        
        print(f"✅ FAQ salva: {pergunta[:50]}...")
        
    except Exception as e:
        print(f"❌ Erro ao salvar FAQ: {e}")


async def update_faq_rating(
    db_pool: asyncpg.Pool,
    pergunta: str,
    rating: int
):
    """Atualiza rating de uma FAQ"""
    try:
        query = """
            UPDATE faqs_historico
            SET 
                rating_medio = (rating_medio * total_votos + $2) / (total_votos + 1),
                total_votos = total_votos + 1,
                updated_at = NOW()
            WHERE pergunta = $1
        """
        
        async with db_pool.acquire() as conn:
            await conn.execute(query, pergunta, rating)
        
        print(f"✅ Rating atualizado para: {pergunta[:50]}...")
        
    except Exception as e:
        print(f"❌ Erro ao atualizar rating: {e}")
