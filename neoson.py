"""
NEOSON - Agente Master Multi-Especializado
Sistema coordenador que gerencia múltiplos agentes especializados
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Imports dos agentes especializados
from agente_rh import AgenteRH
from ti_coordinator import criar_ti_coordinator

# Core configuration
from core.config import config, print_config_summary, validate_config

# LangChain para coordenação
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class Neoson:
    """
    Agente Master que coordena múltiplos agentes especializados
    """
    
    def __init__(self):
        self.nome = "Neoson"
        self.versao = "1.0.0"
        self.agentes = {}
        self.llm_coordenador = None
        self.embeddings = None
        self.memoria_global = {}
        
        # Mapeamento de palavras-chave para agentes (busca rápida)
        # IMPORTANTE: TI tem prioridade para termos de governança e políticas técnicas
        self.keywords_mapping = {
            'ti': ['TI', 'tecnologia', 'sistema', 'senha', 'VPN', 'servidor', 'backup', 
                   'segurança', 'firewall', 'API', 'desenvolvimento', 'computador', 'software', 
                   'hardware', 'rede', 'acesso', 'governança', 'infraestrutura', 'deploy', 
                   'suporte', 'LGPD', 'compliance', 'monitoramento', 'usuário final', 
                   'governance', 'policy', 'políticas de TI', 'ariel'],
            'rh': ['RH', 'recursos humanos', 'férias', 'benefícios', 'salário', 'contrato', 
                   'home office', 'folga', 'falta', 'atestado', 'demissão', 'contratação', 
                   'ana', 'políticas de RH', 'políticas trabalhistas']
        }
        
        # Palavras compostas que têm prioridade sobre palavras individuais
        self.priority_keywords = {
            'ti': ['governança', 'governance', 'lgpd', 'compliance', 'política de senha', 
                   'política de segurança', 'política de TI', 'ariel', 'signature policy'],
            'rh': ['política de RH', 'política trabalhista', 'política de férias', 'ana']
        }
        
        # Descrições detalhadas para análise semântica
        self.agent_descriptions = {
            'rh': (
                "Especialista em Recursos Humanos responsável por políticas de pessoal, "
                "benefícios corporativos, gestão de férias e licenças, processos de contratação "
                "e demissão, procedimentos de home office, questões trabalhistas, planos de "
                "carreira, avaliações de desempenho e compliance de RH"
            ),
            'ti': (
                "Sistema TI hierárquico com sub-especialistas em Governança (políticas LGPD, "
                "compliance, métodos de delivery), Infraestrutura (servidores, redes, "
                "monitoramento, backup), Desenvolvimento (APIs, deploy, arquitetura) e "
                "Suporte ao Usuário Final (senhas, acessos, troubleshooting básico)"
            )
        }
        
        # Template para classificação de perguntas
        self.template_classificacao = """
        Você é Neoson, um sistema de IA que coordena agentes especializados.
        
        Analise a pergunta do usuário e determine qual agente especializado deve responder:
        
        AGENTES DISPONÍVEIS:
        - RH: Recursos Humanos (Ana) - férias, benefícios, políticas de RH, salários, contratos, home office
        - TI: Sistema TI Hierárquico - governança, infraestrutura, desenvolvimento, suporte usuário final
        
        PERGUNTA: "{pergunta}"
        
        Responda APENAS com o nome do agente (RH ou TI) ou GERAL se não souber classificar.
        
        RESPOSTA:
        """

    async def inicializar(self):
        """Inicializa o Neoson e todos os agentes especializados"""
        print("🚀 === INICIALIZANDO NEOSON - AGENTE MASTER ===")
        
        # Validar configurações centralizadas
        validation_results = validate_config()
        if not all(validation_results.values()):
            print("❌ Erro na validação de configurações:")
            for component, valid in validation_results.items():
                status = "✅" if valid else "❌"
                print(f"  {status} {component}")
            raise ValueError("Configurações inválidas")
        
        print("✅ Configurações validadas com sucesso")
        
        # Usar configuração centralizada
        api_key = config.openai.api_key
        
        # Inicializar LLM coordenador e embeddings
        self.llm_coordenador = ChatOpenAI(
            api_key=api_key,
            model=config.openai.chat_model,
            temperature=0.1,
            max_tokens=50
        )
        
        self.embeddings = OpenAIEmbeddings(
            api_key=api_key,
            model=config.openai.embedding_model
        )
        
        print("--- 🤖 Inicializando agentes especializados... ---")
        
        # Inicializar agentes especializados
        resultados = await asyncio.gather(
            self._inicializar_agente_rh(),
            self._inicializar_agente_ti(),
            return_exceptions=True
        )
        
        agentes_ok = 0
        for i, resultado in enumerate(resultados):
            if not isinstance(resultado, Exception):
                agentes_ok += 1
        
        print(f"✅ Neoson inicializado com {agentes_ok} agentes especializados!")
        return agentes_ok > 0

    async def _inicializar_agente_rh(self):
        """Inicializa o agente de RH padronizado"""
        try:
            print("  📋 Inicializando agente de RH (Ana)...")
            agente_rh = AgenteRH()
            if agente_rh:
                self.agentes['rh'] = {
                    'instancia': agente_rh,
                    'nome': 'Ana',
                    'especialidade': 'RH',
                    'status': 'ativo'
                }
                print("  ✅ Agente de RH (Ana) inicializado com sucesso")
                return True
            else:
                print("  ❌ Falha na criação do agente de RH")
                return False
        except Exception as e:
            print(f"  ❌ Erro ao inicializar agente de RH: {str(e)}")
            return False

    async def _inicializar_agente_ti(self):
        """Inicializa o sistema TI hierárquico com sub-especialistas"""
        try:
            print("  💻 Inicializando sistema TI hierárquico...")
            print("      👥 Sub-especialistas: Governança, Infraestrutura, Desenvolvimento, End-User")
            ti_coordinator = criar_ti_coordinator(debug=True)
            if ti_coordinator:
                self.agentes['ti'] = {
                    'instancia': ti_coordinator,
                    'nome': 'Coordenador TI',
                    'especialidade': 'TI Hierárquico',
                    'status': 'ativo'
                }
                print("  ✅ Sistema TI hierárquico inicializado com sucesso")
                
                # Mostrar informações da hierarquia
                info = ti_coordinator.get_info()
                if 'hierarchy_stats' in info:
                    stats = info['hierarchy_stats']
                    print(f"      📊 Sub-agentes ativos: {stats.get('sub_agents', 0)}")
                
                return True
            else:
                print("  ❌ Falha na inicialização do sistema TI hierárquico")
                return False
        except Exception as e:
            print(f"  ❌ Erro ao inicializar sistema TI: {str(e)}")
            return False

    def classificar_pergunta(self, pergunta: str) -> str:
        """Classifica a pergunta usando abordagem híbrida: keywords + embeddings"""
        try:
            pergunta_lower = pergunta.lower()
            
            # FASE 1a: Busca por palavras prioritárias (mais específicas)
            for agente_key, priority_words in self.priority_keywords.items():
                for priority_word in priority_words:
                    if priority_word.lower() in pergunta_lower:
                        print(f"🎯 Match prioritário: '{priority_word}' → {agente_key.upper()}")
                        return agente_key
            
            # FASE 1b: Busca rápida por palavras-chave gerais
            for agente_key, keywords in self.keywords_mapping.items():
                for keyword in keywords:
                    if keyword.lower() in pergunta_lower:
                        print(f"🔍 Match direto por keyword: '{keyword}' → {agente_key.upper()}")
                        return agente_key
            
            # FASE 2: Se não encontrou por keywords, usar análise semântica
            if not self.embeddings or not self.agentes:
                print("⚠️ Embeddings ou agentes não disponíveis, usando fallback LLM")
                return self._classificar_com_llm(pergunta)
            
            print("🧠 Nenhuma keyword encontrada, analisando semanticamente...")
            return self._classificar_com_embeddings(pergunta)
            
        except Exception as e:
            print(f"❌ Erro na classificação: {str(e)}")
            return 'geral'

    def _classificar_com_embeddings(self, pergunta: str) -> str:
        """Classifica usando similaridade semântica com embeddings"""
        try:
            # Gerar embedding da pergunta
            pergunta_embedding = self.embeddings.embed_query(pergunta)
            
            melhor_agente = None
            melhor_score = -1
            
            # Comparar com cada agente disponível (incluindo descrições fixas)
            agentes_para_testar = list(self.agentes.keys()) + list(self.agent_descriptions.keys())
            agentes_unicos = list(set(agentes_para_testar))
            
            for agente_key in agentes_unicos:
                # Tentar obter metadados dinâmicos do agente
                texto_agente = ""
                
                if agente_key in self.agentes and self.agentes[agente_key]['status'] == 'ativo':
                    agente_obj = self.agentes[agente_key].get('instancia')
                    if agente_obj and hasattr(agente_obj, 'obter_info_agente'):
                        try:
                            info_agente = agente_obj.obter_info_agente()
                            texto_agente = (
                                f"{info_agente.get('descricao', '')}. "
                                f"Especialidade: {info_agente.get('especialidade', '')}. "
                                f"Palavras-chave: {', '.join(info_agente.get('keywords', []))}"
                            )
                        except Exception:
                            pass  # Fallback para descrição fixa
                
                # Se não conseguiu metadados dinâmicos, usar descrição fixa
                if not texto_agente and agente_key in self.agent_descriptions:
                    keywords_texto = ', '.join(self.keywords_mapping.get(agente_key, []))
                    texto_agente = f"{self.agent_descriptions[agente_key]}. Palavras-chave: {keywords_texto}"
                
                if not texto_agente:
                    continue  # Pular se não tem informação
                
                # Gerar embedding do agente
                agente_embedding = self.embeddings.embed_query(texto_agente)
                
                # Calcular similaridade usando produto escalar normalizado (cosseno)
                score = np.dot(pergunta_embedding, agente_embedding) / (
                    np.linalg.norm(pergunta_embedding) * np.linalg.norm(agente_embedding)
                )
                
                print(f"📊 Similaridade {agente_key.upper()}: {score:.3f}")
                
                if score > melhor_score:
                    melhor_score = score
                    melhor_agente = agente_key
            
            # Retornar se score for suficientemente alto
            if melhor_agente and melhor_score > 0.65:  # Threshold de confiança
                print(f"✅ Melhor match semântico: {melhor_agente.upper()} (score: {melhor_score:.3f})")
                return melhor_agente
            
            print(f"⚠️ Score insuficiente ({melhor_score:.3f}), usando fallback LLM")
            return self._classificar_com_llm(pergunta)
            
        except Exception as e:
            print(f"❌ Erro na análise semântica: {str(e)}")
            return self._classificar_com_llm(pergunta)

    def _classificar_com_llm(self, pergunta: str) -> str:
        """Fallback usando LLM para classificação"""
        try:
            prompt_formatado = self.template_classificacao.format(pergunta=pergunta)
            resposta = self.llm_coordenador.invoke(prompt_formatado)
            
            classificacao = resposta.content.strip().upper() if hasattr(resposta, 'content') else str(resposta).strip().upper()
            
            if classificacao in ['RH', 'TI']:
                print(f"🤖 Classificação LLM: {classificacao}")
                return classificacao.lower()
            
            return 'geral'
            
        except Exception as e:
            print(f"❌ Erro no fallback LLM: {str(e)}")
            return 'geral'

    def processar_pergunta(self, pergunta: str, perfil_usuario: dict) -> dict:
        """Processa uma pergunta direcionando para o agente apropriado"""
        try:
            # Classificar a pergunta
            agente_escolhido = self.classificar_pergunta(pergunta)
            
            # Log da classificação
            print(f"🎯 Pergunta classificada para: {agente_escolhido.upper()}")
            print(f"🔍 Debug - Agentes disponíveis: {list(self.agentes.keys())}")
            print(f"🔍 Debug - Agente escolhido existe? {agente_escolhido in self.agentes}")
            
            # Direcionar para o agente apropriado
            if agente_escolhido in self.agentes and self.agentes[agente_escolhido]['status'] == 'ativo':
                agente = self.agentes[agente_escolhido]
                print(f"✅ Direcionando para agente: {agente['nome']}")
                
                # Diferentes formas de chamar cada agente
                if agente_escolhido == 'rh':
                    # Agente RH usa o método padronizado da classe
                    resposta = agente['instancia'].processar(pergunta, perfil_usuario)
                elif agente_escolhido == 'ti':
                    # Agente TI usa o coordenador hierárquico
                    print(f"🔄 Passando pergunta para TI Coordinator: '{pergunta[:50]}...'")
                    resposta = agente['instancia'].processar_pergunta(pergunta, perfil_usuario)
                    print(f"📋 Resposta recebida do TI Coordinator: {len(resposta)} caracteres")
                else:
                    resposta = "Agente não encontrado."
                
                return {
                    'sucesso': True,
                    'resposta': resposta,
                    'agente_usado': agente['nome'],
                    'especialidade': agente['especialidade'],
                    'classificacao': agente_escolhido
                }
            
            else:
                print(f"⚠️ Agente {agente_escolhido} não disponível ou não existe")
                # Se o agente foi classificado mas não está disponível, mostrar isso
                if agente_escolhido in ['rh', 'ti'] and agente_escolhido not in self.agentes:
                    resposta_erro = f"🔧 O especialista em {agente_escolhido.upper()} não está disponível no momento. Tente novamente mais tarde ou reformule sua pergunta."
                    return {
                        'sucesso': True,
                        'resposta': resposta_erro,
                        'agente_usado': 'Neoson',
                        'especialidade': 'Sistema',
                        'classificacao': f'{agente_escolhido}_indisponivel'
                    }
                
                # Resposta genérica do Neoson
                resposta_generica = self._resposta_generica(pergunta, perfil_usuario)
                return {
                    'sucesso': True,
                    'resposta': resposta_generica,
                    'agente_usado': 'Neoson',
                    'especialidade': 'Coordenação Geral',
                    'classificacao': 'geral'
                }
        
        except Exception as e:
            print(f"❌ Erro no processamento: {str(e)}")
            return {
                'sucesso': False,
                'resposta': f"Desculpe, tive um problema ao processar sua pergunta. Erro: {str(e)}",
                'agente_usado': 'Neoson',
                'especialidade': 'Sistema',
                'classificacao': 'erro'
            }

    def _resposta_generica(self, pergunta: str, perfil_usuario: dict) -> str:
        """Gera uma resposta genérica quando não consegue classificar a pergunta"""
        return f"""Oi, {perfil_usuario.get('nome', 'pessoal')}! 👋

Eu sou o Neoson, seu assistente inteligente! Não consegui identificar exatamente sobre qual área é sua pergunta.

🤖 **Posso te ajudar com:**
• 📋 **Questões de RH** (Ana): Férias, benefícios, políticas, home office
• 💻 **Questões de TI** (Sistema Hierárquico):
  - 🏛️ Governança (Ariel): Políticas LGPD, compliance, delivery methods
  - 🖥️ Infraestrutura (Alice): Servidores, redes, monitoramento
  - ⚡ Desenvolvimento (Carlos): APIs, deploy, arquitetura
  - 🎧 Suporte Usuário (Marina): Senhas, acessos, troubleshooting

Você pode reformular sua pergunta mencionando a área, ou posso tentar direcionar para o especialista mais adequado.

Como posso ajudar melhor? 😊"""

    def obter_status_sistema(self) -> dict:
        """Retorna o status de todos os agentes"""
        status = {
            'neoson': {
                'nome': self.nome,
                'versao': self.versao,
                'status': 'ativo',
                'agentes_gerenciados': len(self.agentes)
            },
            'agentes': {}
        }
        
        for agente_id, agente_info in self.agentes.items():
            status['agentes'][agente_id] = {
                'nome': agente_info['nome'],
                'especialidade': agente_info['especialidade'],
                'status': agente_info['status']
            }
        
        return status

    def limpar_memoria_usuario(self, perfil_usuario: dict) -> bool:
        """Limpa a memória de todos os agentes para um usuário"""
        try:
            usuario_id = f"{perfil_usuario.get('nome', 'usuario')}_{perfil_usuario.get('area', 'geral')}"
            
            # Limpar memória em cada agente (implementar conforme cada agente)
            for agente_id, agente in self.agentes.items():
                if hasattr(agente['instancia'], 'memoria_conversas'):
                    if usuario_id in agente['instancia'].memoria_conversas:
                        del agente['instancia'].memoria_conversas[usuario_id]
            
            # Limpar memória global
            if usuario_id in self.memoria_global:
                del self.memoria_global[usuario_id]
            
            return True
        except Exception as e:
            print(f"❌ Erro ao limpar memória: {str(e)}")
            return False


# Factory function
async def criar_neoson():
    """Cria e inicializa o sistema Neoson"""
    neoson = Neoson()
    if await neoson.inicializar():
        return neoson
    return None


# Teste assíncrono
async def teste_neoson():
    """Testa o sistema Neoson com perguntas diversas"""
    print("🧪 === TESTE DO SISTEMA NEOSON ===\n")
    
    neoson = await criar_neoson()
    
    if not neoson:
        print("❌ Falha na inicialização do Neoson")
        return
    
    # Perfil de teste
    perfil_teste = {
        'nome': 'Maria Silva',
        'Nome': 'Maria Silva',  # Para compatibilidade com agente RH
        'cargo': 'Gerente de Projetos',
        'Cargo': 'Gerente de Projetos',  # Para compatibilidade com agente RH
        'area': 'TI',
        'Departamento': 'TI',  # Para compatibilidade com agente RH
        'nivel_hierarquico': 4,
        'Nivel_Hierarquico': 4,  # Para compatibilidade com agente RH
        'geografia': 'BR',
        'Geografia': 'BR',  # Para compatibilidade com agente RH
        'projetos': ['Apollo'],
        'Projetos': ['Apollo']  # Para compatibilidade com agente RH
    }
    
    # Perguntas de teste para diferentes áreas
    perguntas_teste = [
        "Como funciona a política de férias da empresa?",  # RH
        "Preciso resetar minha senha do sistema. Como faço?",  # TI
        "Quantos dias de home office posso fazer por semana?",  # RH
        "Onde estão os servidores de produção?",  # TI
        "Qual é o horário de funcionamento da empresa?",  # Geral
    ]
    
    print("Status do sistema:")
    status = neoson.obter_status_sistema()
    print(json.dumps(status, indent=2, ensure_ascii=False))
    print("\n" + "="*80 + "\n")
    
    for i, pergunta in enumerate(perguntas_teste, 1):
        print(f"🗣️ Pergunta {i}: {pergunta}")
        
        resultado = neoson.processar_pergunta(pergunta, perfil_teste)
        
        print(f"🤖 {resultado['agente_usado']} ({resultado['especialidade']}):")
        print(f"   {resultado['resposta']}")
        print(f"📊 Classificação: {resultado['classificacao']}")
        print("="*80 + "\n")


if __name__ == "__main__":
    # Executar teste
    asyncio.run(teste_neoson())