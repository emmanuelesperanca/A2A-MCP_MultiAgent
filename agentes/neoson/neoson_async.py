"""
NEOSON - Agente Master Multi-Especializado ASSÍNCRONO
Sistema coordenador que gerencia múltiplos agentes especializados de forma assíncrona
Versão otimizada para alta performance e escalabilidade

MELHORIAS IMPLEMENTADAS:
- ✅ Proibição de envio de links nas respostas
- ✅ Glossário corporativo de jargões da empresa
- ✅ Classificação 100% LLM (sem keywords)
"""

import json
import asyncio
from typing import Dict, List, Optional

# Imports dos agentes especializados assíncronos
from agentes.coordenadores.agente_rh_async import AgenteRHAsync
from agentes.coordenadores.ti_coordinator_async import criar_ti_coordinator_async

# Core configuration
from core.config import config, validate_config

# Novos sistemas
from core.agent_classifier import AgentClassifier
from core.glossario_corporativo import (
    detectar_termos_corporativos,
    enriquecer_prompt_com_glossario,
    get_contexto_glossario
)

# LangChain para coordenação
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import numpy as np


class NeosonAsync:
    """
    Agente Master que coordena múltiplos agentes especializados de forma ASSÍNCRONA
    
    VERSÃO 3.0 - Com melhorias:
    - Classificação 100% LLM
    - Glossário corporativo
    - Proibição de links
    """

    def __init__(self):
        self.nome = "Neoson Async"
        self.versao = "3.0.0"
        self.agentes = {}
        self.llm_coordenador = None
        self.embeddings = None
        self.memoria_global = {}
        
        # 🆕 NOVO: Classificador inteligente baseado em LLM
        self.classifier = AgentClassifier()
        
        # 🆕 NOVO: Sistema de glossário corporativo
        self.glossario_ativo = True
        
        # 🆕 NOVO: Regras de segurança
        self.proibir_links = True  # Nunca enviar links nas respostas

    async def inicializar(self) -> bool:
        """Inicializa o Neoson e todos os agentes especializados de forma ASSÍNCRONA"""
        print("🚀 === INICIALIZANDO NEOSON ASYNC - AGENTE MASTER ===")

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

        print("--- 🤖 Inicializando agentes especializados (ASSÍNCRONO)... ---")

        # Inicializar agentes especializados de forma concorrente
        resultados = await asyncio.gather(
            self._inicializar_agente_rh_async(),
            self._inicializar_agente_ti_async(),
            return_exceptions=True
        )

        agentes_ok = 0
        for i, resultado in enumerate(resultados):
            if not isinstance(resultado, Exception):
                agentes_ok += 1
            else:
                print(f"❌ Erro ao inicializar agente {i}: {resultado}")

        print(f"✅ Neoson Async inicializado com {agentes_ok} agentes especializados!")
        return agentes_ok > 0

    async def _inicializar_agente_rh_async(self) -> bool:
        """Inicializa o agente de RH assíncrono"""
        try:
            print("  📋 Inicializando agente de RH (Ana) - ASYNC...")
            agente_rh = AgenteRHAsync(debug=False)
            if agente_rh:
                self.agentes['rh'] = {
                    'instancia': agente_rh,
                    'nome': 'Ana',
                    'especialidade': 'RH',
                    'status': 'ativo'
                }
                print("  ✅ Agente de RH (Ana) inicializado com sucesso (ASYNC)")
                return True
            else:
                print("  ❌ Falha na criação do agente de RH")
                return False
        except Exception as e:
            print(f"  ❌ Erro ao inicializar agente de RH: {str(e)}")
            return False

    async def _inicializar_agente_ti_async(self) -> bool:
        """Inicializa o sistema TI hierárquico assíncrono"""
        try:
            print("  💻 Inicializando sistema TI hierárquico - ASYNC...")
            print("      👥 Sub-especialistas: Governança, Infraestrutura, Desenvolvimento, End-User")
            ti_coordinator = await criar_ti_coordinator_async(debug=True)
            if ti_coordinator:
                self.agentes['ti'] = {
                    'instancia': ti_coordinator,
                    'nome': 'Coordenador TI',
                    'especialidade': 'TI Hierárquico',
                    'status': 'ativo'
                }
                print("  ✅ Sistema TI hierárquico inicializado com sucesso (ASYNC)")
                
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

    async def classificar_pergunta_async(self, pergunta: str) -> dict:
        """
        🆕 NOVO: Classificação 100% LLM - Sem keywords
        
        Usa o AgentClassifier para analisar a pergunta e escolher
        os 3 melhores sub-agentes para responder
        
        Args:
            pergunta: Pergunta do usuário
            
        Returns:
            dict com área principal e agentes selecionados
        """
        try:
            print("🤖 Iniciando classificação inteligente (LLM)...")
            
            # Usar o classificador inteligente
            classificacao = await self.classifier.classify_question(pergunta)
            
            print(f"� Análise: {classificacao['analise']}")
            print(f"🎯 Área: {classificacao['area_principal'].upper()}")
            print("🤖 Agentes selecionados:")
            for i, agent in enumerate(classificacao['agentes_selecionados'], 1):
                print(f"  {i}. {agent['agente']} ({agent['relevancia']}) - {agent['justificativa']}")
            
            return classificacao
            
        except Exception as e:
            print(f"❌ Erro na classificação LLM: {e}")
            # Fallback simples
            return {
                "analise": "Erro na classificação, usando fallback",
                "area_principal": "ti",
                "agentes_selecionados": [
                    {"agente": "enduser", "relevancia": "alta", "justificativa": "Fallback"},
                    {"agente": "governance", "relevancia": "media", "justificativa": "Fallback"},
                    {"agente": "infra", "relevancia": "baixa", "justificativa": "Fallback"}
                ]
            }

    def enriquecer_pergunta_com_glossario(self, pergunta: str) -> tuple:
        """
        🆕 NOVO: Detecta e enriquece pergunta com glossário corporativo
        
        Args:
            pergunta: Pergunta original do usuário
            
        Returns:
            tuple (pergunta_enriquecida, termos_detectados)
        """
        if not self.glossario_ativo:
            return pergunta, []
        
        # Detectar termos corporativos
        termos_detectados = detectar_termos_corporativos(pergunta)
        
        if termos_detectados:
            print(f"📚 Termos corporativos detectados: {', '.join(termos_detectados)}")
            pergunta_enriquecida = enriquecer_prompt_com_glossario(pergunta, termos_detectados)
            return pergunta_enriquecida, termos_detectados
        
        return pergunta, []

    def validar_resposta_sem_links(self, resposta: str) -> str:
        """
        🆕 NOVO: Remove links da resposta para segurança
        
        Args:
            resposta: Resposta gerada pelo agente
            
        Returns:
            Resposta sem links
        """
        if not self.proibir_links:
            return resposta
        
        import re
        
        # Padrões de links a remover
        padroes_links = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            r'\[.*?\]\(.*?\)',  # Links markdown [texto](url)
        ]
        
        resposta_limpa = resposta
        links_removidos = []
        
        for padrao in padroes_links:
            matches = re.findall(padrao, resposta_limpa)
            if matches:
                links_removidos.extend(matches)
                resposta_limpa = re.sub(padrao, '[LINK REMOVIDO POR SEGURANÇA]', resposta_limpa)
        
        if links_removidos:
            print(f"⚠️ {len(links_removidos)} link(s) removido(s) da resposta por segurança")
            print(f"🔒 Links removidos: {links_removidos[:3]}")  # Mostra primeiros 3
        
        return resposta_limpa

    async def processar_pergunta_async(self, pergunta: str, perfil_usuario: dict) -> dict:
        """
        Processa uma pergunta direcionando para o agente apropriado (ASSÍNCRONO)
        
        🆕 VERSÃO 3.0 com:
        - Classificação 100% LLM
        - Enriquecimento com glossário corporativo
        - Validação de segurança (remoção de links)
        """
        try:
            print(f"\n{'='*80}")
            print(f"🔍 PROCESSANDO PERGUNTA (v3.0)")
            print(f"{'='*80}")
            
            # FASE 1: Enriquecer com glossário corporativo
            pergunta_enriquecida, termos_detectados = self.enriquecer_pergunta_com_glossario(pergunta)
            
            # FASE 2: Classificar com LLM (100%)
            classificacao = await self.classificar_pergunta_async(pergunta)
            area_principal = classificacao['area_principal']
            agentes_selecionados = classificacao['agentes_selecionados']
            
            print(f"\n🎯 Área classificada: {area_principal.upper()}")
            print(f"🤖 Agentes escolhidos: {[a['agente'] for a in agentes_selecionados]}")
            
            # FASE 3: Direcionar para o agente apropriado
            if area_principal in self.agentes and self.agentes[area_principal]['status'] == 'ativo':
                agente = self.agentes[area_principal]
                print(f"\n✅ Direcionando para: {agente['nome']}")
                
                # Preparar contexto enriquecido
                contexto_extra = {
                    'termos_corporativos': termos_detectados,
                    'agentes_sugeridos': [a['agente'] for a in agentes_selecionados],
                    'analise_llm': classificacao['analise']
                }
                
                # Chamar o agente de forma ASSÍNCRONA
                if area_principal == 'rh':
                    resposta = await agente['instancia'].processar_async(
                        pergunta_enriquecida,
                        perfil_usuario
                    )
                elif area_principal == 'ti':
                    # Para TI, passar os sub-agentes sugeridos
                    resposta = await agente['instancia'].processar_pergunta_async(
                        pergunta_enriquecida,
                        perfil_usuario,
                        sub_agentes_sugeridos=contexto_extra['agentes_sugeridos']
                    )
                else:
                    resposta = "Agente não encontrado."
                
                # FASE 4: Validar segurança (remover links)
                resposta_segura = self.validar_resposta_sem_links(resposta)
                
                print(f"\n✅ Resposta gerada: {len(resposta_segura)} caracteres")
                print(f"{'='*80}\n")
                
                return {
                    'sucesso': True,
                    'resposta': resposta_segura,
                    'agente_usado': agente['nome'],
                    'especialidade': agente['especialidade'],
                    'classificacao': area_principal,
                    'metadata': {
                        'termos_corporativos': termos_detectados,
                        'agentes_consultados': contexto_extra['agentes_sugeridos'],
                        'analise': classificacao['analise'],
                        'links_removidos': resposta != resposta_segura
                    }
                }
            
            else:
                print(f"\n⚠️ Agente {area_principal} não disponível")
                resposta_erro = f"🔧 O especialista em {area_principal.upper()} não está disponível no momento."
                
                return {
                    'sucesso': True,
                    'resposta': resposta_erro,
                    'agente_usado': 'Neoson',
                    'especialidade': 'Sistema',
                    'classificacao': f'{area_principal}_indisponivel',
                    'metadata': {}
                }
        
        except Exception as e:
            print(f"\n❌ Erro no processamento: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                'sucesso': False,
                'resposta': f"Desculpe, tive um problema ao processar sua pergunta. Por favor, tente novamente.",
                'agente_usado': 'Neoson',
                'especialidade': 'Sistema',
                'classificacao': 'erro',
                'metadata': {'erro': str(e)}
            }

    def _resposta_generica(self, pergunta: str, perfil_usuario: dict) -> str:
        """Gera uma resposta genérica quando não consegue classificar a pergunta"""
        return f"""Oi, {perfil_usuario.get('Nome', perfil_usuario.get('nome', 'pessoal'))}! 👋

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
            usuario_id = f"{perfil_usuario.get('Nome', perfil_usuario.get('nome', 'usuario'))}_{perfil_usuario.get('Departamento', perfil_usuario.get('area', 'geral'))}"
            
            # Limpar memória em cada agente
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


# Factory function assíncrona
async def criar_neoson_async() -> Optional[NeosonAsync]:
    """Cria e inicializa o sistema Neoson de forma ASSÍNCRONA"""
    neoson = NeosonAsync()
    if await neoson.inicializar():
        return neoson
    return None


# Teste assíncrono
async def teste_neoson_async():
    """Testa o sistema Neoson assíncrono com perguntas diversas"""
    print("🧪 === TESTE DO SISTEMA NEOSON ASYNC ===\n")
    
    neoson = await criar_neoson_async()
    
    if not neoson:
        print("❌ Falha na inicialização do Neoson")
        return
    
    # Perfil de teste
    perfil_teste = {
        'Nome': 'Maria Silva',
        'Cargo': 'Gerente de Projetos',
        'Departamento': 'TI',
        'Nivel_Hierarquico': 4,
        'Geografia': 'BR',
        'Projetos': ['Apollo']
    }
    
    # Perguntas de teste
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
    
    # Processar perguntas de forma concorrente (demonstração de async)
    tasks = []
    for i, pergunta in enumerate(perguntas_teste, 1):
        print(f"🗣️ Pergunta {i}: {pergunta}")
        tasks.append(neoson.processar_pergunta_async(pergunta, perfil_teste))
    
    # Aguardar todas as respostas
    resultados = await asyncio.gather(*tasks)
    
    # Exibir resultados
    for i, (pergunta, resultado) in enumerate(zip(perguntas_teste, resultados), 1):
        print(f"\n🤖 Resultado {i}:")
        print(f"   Pergunta: {pergunta}")
        print(f"   Agente: {resultado['agente_usado']} ({resultado['especialidade']})")
        print(f"   Resposta: {resultado['resposta'][:200]}...")
        print(f"   Classificação: {resultado['classificacao']}")
        print("="*80)


if __name__ == "__main__":
    # Executar teste
    asyncio.run(teste_neoson_async())
