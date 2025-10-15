# 🤖 CLASSIFICADOR INTELIGENTE DE AGENTES
# Sistema que usa LLM para escolher os melhores sub-agentes para cada pergunta

import json
from typing import List, Dict
from openai import AsyncOpenAI
from core.config import ConfigManager

config = ConfigManager()


# 📚 BASE DE CONHECIMENTO DOS AGENTES
AGENTES_KNOWLEDGE_BASE = {
    "ti": {
        "name": "TI - Tecnologia da Informação",
        "description": "Coordena equipe especializada em tecnologia, infraestrutura, sistemas e desenvolvimento",
        "subagentes": {
            "governance": {
                "name": "Ariel - Governança de TI",
                "description": "Especialista em políticas de TI, compliance, segurança da informação, LGPD/GDPR, auditoria, controles internos, gestão de riscos tecnológicos e normas ISO 27001",
                "expertise": [
                    "Políticas e procedimentos de TI",
                    "Compliance e regulamentações (LGPD, GDPR, SOX)",
                    "Segurança da informação e cibersegurança",
                    "Gestão de riscos e controles internos",
                    "Auditoria de sistemas e processos",
                    "Normas ISO 27001, ISO 20000",
                    "Governança corporativa de TI",
                    "Data Protection Officer (DPO)"
                ]
            },
            "infra": {
                "name": "Alice - Infraestrutura e Redes",
                "description": "Especialista em servidores, redes, cloud computing, virtualização, storage, backup, disaster recovery, monitoramento de sistemas e performance",
                "expertise": [
                    "Servidores físicos e virtuais (VMware, Hyper-V)",
                    "Redes TCP/IP, switches, roteadores, firewalls",
                    "Cloud computing (Azure, AWS, Google Cloud)",
                    "VPN, VDI, acesso remoto",
                    "Storage e backup (SAN, NAS, Veeam)",
                    "Disaster recovery e business continuity",
                    "Monitoramento (Zabbix, PRTG, Nagios)",
                    "Performance e otimização de infraestrutura"
                ]
            },
            "dev": {
                "name": "Carlos - Desenvolvimento e Sistemas",
                "description": "Especialista em desenvolvimento de software, APIs, integrações, banco de dados, DevOps, CI/CD, debugging, sistemas ERP (SAP, TOTVS, Salesforce)",
                "expertise": [
                    "Desenvolvimento web (Python, JavaScript, C#, Java)",
                    "APIs REST, GraphQL, microservices",
                    "Integrações entre sistemas (SAP, TOTVS, Salesforce)",
                    "Banco de dados (SQL Server, PostgreSQL, Oracle)",
                    "DevOps, CI/CD, Docker, Kubernetes",
                    "Git, controle de versão, code review",
                    "Debugging e troubleshooting de aplicações",
                    "Arquitetura de software e design patterns"
                ]
            },
            "enduser": {
                "name": "Marina - Suporte ao Usuário Final",
                "description": "Especialista em suporte técnico, help desk, problemas de hardware/software de usuários, instalação de programas, impressoras, Office 365, configuração de dispositivos móveis",
                "expertise": [
                    "Suporte técnico N1 e N2",
                    "Windows 10/11, MacOS, iOS, Android",
                    "Office 365, Outlook, Teams, OneDrive, SharePoint",
                    "Impressoras, scanners, periféricos",
                    "Instalação e configuração de software",
                    "Active Directory, criação de usuários",
                    "Senha, acesso, permissões",
                    "Dispositivos móveis corporativos (MDM)"
                ]
            }
        }
    },
    "rh": {
        "name": "RH - Recursos Humanos",
        "description": "Coordena equipe especializada em gestão de pessoas, benefícios, treinamento e relações trabalhistas",
        "subagentes": {
            "admin": {
                "name": "Ana - Administração de Pessoal",
                "description": "Especialista em folha de pagamento, admissão, demissão, férias, ponto, contratos, documentação trabalhista, FGTS, INSS, rescisão",
                "expertise": [
                    "Folha de pagamento e cálculos trabalhistas",
                    "Admissão de colaboradores (documentação, contrato)",
                    "Demissão e rescisão contratual",
                    "Férias, abono pecuniário, licenças",
                    "Controle de ponto e banco de horas",
                    "FGTS, INSS, impostos trabalhistas",
                    "eSocial, CAGED, RAIS",
                    "Documentação e arquivos de pessoal"
                ]
            },
            "benefits": {
                "name": "Bruno - Benefícios e Remuneração",
                "description": "Especialista em benefícios corporativos (plano de saúde, vale-alimentação, Gympass), PPR/PLR, política salarial, pesquisa de mercado, C&B, job grades",
                "expertise": [
                    "Plano de saúde e odontológico",
                    "Vale-refeição, vale-alimentação, vale-transporte",
                    "Gympass, TotalPass, benefícios de bem-estar",
                    "Seguro de vida, auxílio creche",
                    "PPR (Programa de Participação nos Resultados)",
                    "Política salarial e estrutura de cargos",
                    "Pesquisa salarial e benchmarking",
                    "Job evaluation e job grades"
                ]
            },
            "training": {
                "name": "Carla - Treinamento e Desenvolvimento",
                "description": "Especialista em capacitação, treinamentos técnicos/comportamentais, onboarding, PDI, avaliação de desempenho, planos de carreira, mentoria, L&D",
                "expertise": [
                    "Programas de treinamento técnico e comportamental",
                    "Onboarding de novos colaboradores",
                    "PDI (Plano de Desenvolvimento Individual)",
                    "Avaliação de desempenho e feedback 360",
                    "Planos de carreira e sucessão",
                    "Mentoria e coaching",
                    "Universidade corporativa e e-learning",
                    "Desenvolvimento de lideranças"
                ]
            },
            "relations": {
                "name": "Diego - Relações Trabalhistas",
                "description": "Especialista em legislação trabalhista, convenções coletivas, sindicatos, processos trabalhistas, mediação de conflitos, CLT, reforma trabalhista, homologações",
                "expertise": [
                    "Legislação trabalhista (CLT, reforma trabalhista)",
                    "Convenções coletivas e acordos sindicais",
                    "Processos trabalhistas e defesas",
                    "Mediação de conflitos e relações sindicais",
                    "Homologações e rescisões assistidas",
                    "Normas regulamentadoras (NRs)",
                    "CIPA, segurança do trabalho, ASO",
                    "Assédio moral/sexual e questões disciplinares"
                ]
            }
        }
    }
}


# 🎯 PROMPT PARA CLASSIFICAÇÃO INTELIGENTE
CLASSIFICACAO_PROMPT = """Você é um especialista em classificação de perguntas para um sistema multi-agente corporativo.

**SUA MISSÃO:** Analisar a pergunta do usuário e escolher os 3 melhores sub-agentes para responder.

**BASE DE AGENTES DISPONÍVEIS:**

{agents_knowledge}

**INSTRUÇÕES:**
1. Leia atentamente a pergunta do usuário
2. Identifique os tópicos principais e secundários
3. Analise qual(is) área(s) são mais relevantes (TI ou RH)
4. Escolha os 3 sub-agentes mais capacitados para responder, em ordem de relevância
5. Considere que alguns assuntos podem envolver múltiplas áreas (ex: acesso a sistema = Governance + EndUser)

**CRITÉRIOS DE ESCOLHA:**
- Relevância direta da expertise do agente com a pergunta
- Capacidade de fornecer resposta completa e técnica
- Experiência específica no assunto questionado
- Possibilidade de resposta complementar entre os agentes

**FORMATO DE RESPOSTA:**
Retorne APENAS um JSON válido no formato:
{{
    "analise": "Breve análise da pergunta (1-2 frases)",
    "area_principal": "ti" ou "rh",
    "agentes_selecionados": [
        {{
            "agente": "nome_do_agente",
            "relevancia": "alta" ou "media" ou "baixa",
            "justificativa": "Por que esse agente foi escolhido"
        }}
    ]
}}

**PERGUNTA DO USUÁRIO:**
{user_question}

**ATENÇÃO:** 
- Retorne EXATAMENTE 3 agentes, ordenados por relevância (mais relevante primeiro)
- Use os nomes técnicos dos agentes: governance, infra, dev, enduser, admin, benefits, training, relations
- Seja preciso e técnico na justificativa
"""


class AgentClassifier:
    """
    Classificador inteligente que usa LLM para escolher os melhores agentes
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.openai.api_key)
        self.model = config.openai.chat_model
    
    def _format_agents_knowledge(self) -> str:
        """Formata a base de conhecimento dos agentes para o prompt"""
        formatted = ""
        
        for area_key, area_data in AGENTES_KNOWLEDGE_BASE.items():
            formatted += f"\n### {area_data['name']}\n"
            formatted += f"{area_data['description']}\n\n"
            
            for agent_key, agent_data in area_data['subagentes'].items():
                formatted += f"**{agent_key}** - {agent_data['name']}\n"
                formatted += f"{agent_data['description']}\n"
                formatted += "Especialidades:\n"
                for exp in agent_data['expertise']:
                    formatted += f"  - {exp}\n"
                formatted += "\n"
        
        return formatted
    
    async def classify_question(self, user_question: str) -> Dict:
        """
        Classifica a pergunta e retorna os 3 melhores agentes
        
        Args:
            user_question: Pergunta do usuário
            
        Returns:
            Dict com análise e agentes selecionados
        """
        try:
            # Formata o prompt
            agents_knowledge = self._format_agents_knowledge()
            prompt = CLASSIFICACAO_PROMPT.format(
                agents_knowledge=agents_knowledge,
                user_question=user_question
            )
            
            # Chama a LLM
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um classificador preciso e técnico."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Baixa temperatura para mais consistência
                max_tokens=800
            )
            
            # Parse da resposta
            result_text = response.choices[0].message.content.strip()
            
            # Remove markdown se houver
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            elif result_text.startswith("```"):
                result_text = result_text.replace("```", "").strip()
            
            result = json.loads(result_text)
            
            # Validação básica
            if "agentes_selecionados" not in result:
                raise ValueError("Resposta da LLM não contém 'agentes_selecionados'")
            
            if len(result["agentes_selecionados"]) != 3:
                raise ValueError(f"LLM retornou {len(result['agentes_selecionados'])} agentes, esperado 3")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao parsear JSON da LLM: {e}")
            print(f"Resposta recebida: {result_text[:500]}")
            return self._fallback_classification(user_question)
            
        except Exception as e:
            print(f"❌ Erro na classificação LLM: {e}")
            return self._fallback_classification(user_question)
    
    def _fallback_classification(self, user_question: str) -> Dict:
        """
        Classificação de fallback baseada em keywords simples
        Usado apenas se a LLM falhar
        """
        question_lower = user_question.lower()
        
        # Keywords básicas para TI
        ti_keywords = ["sistema", "senha", "acesso", "rede", "vpn", "computador", "software", 
                       "servidor", "email", "outlook", "backup", "internet", "wi-fi"]
        
        # Keywords básicas para RH
        rh_keywords = ["férias", "salário", "benefício", "folha", "contrato", "demissão",
                       "admissão", "treinamento", "vale", "plano de saúde", "ponto"]
        
        ti_score = sum(1 for kw in ti_keywords if kw in question_lower)
        rh_score = sum(1 for kw in rh_keywords if kw in question_lower)
        
        if ti_score >= rh_score:
            return {
                "analise": "Classificação de fallback baseada em keywords (LLM indisponível)",
                "area_principal": "ti",
                "agentes_selecionados": [
                    {"agente": "enduser", "relevancia": "alta", "justificativa": "Fallback TI"},
                    {"agente": "governance", "relevancia": "media", "justificativa": "Fallback TI"},
                    {"agente": "infra", "relevancia": "baixa", "justificativa": "Fallback TI"}
                ]
            }
        else:
            return {
                "analise": "Classificação de fallback baseada em keywords (LLM indisponível)",
                "area_principal": "rh",
                "agentes_selecionados": [
                    {"agente": "admin", "relevancia": "alta", "justificativa": "Fallback RH"},
                    {"agente": "benefits", "relevancia": "media", "justificativa": "Fallback RH"},
                    {"agente": "training", "relevancia": "baixa", "justificativa": "Fallback RH"}
                ]
            }
    
    def get_agent_names(self, classification: Dict) -> List[str]:
        """
        Extrai os nomes dos agentes da classificação
        
        Args:
            classification: Dict retornado por classify_question
            
        Returns:
            Lista com nomes dos 3 agentes
        """
        return [agent["agente"] for agent in classification["agentes_selecionados"]]
    
    def get_agent_info(self, agent_name: str, area: str) -> Dict:
        """
        Retorna informações detalhadas de um agente
        
        Args:
            agent_name: Nome técnico do agente (ex: 'governance')
            area: Área do agente ('ti' ou 'rh')
            
        Returns:
            Dict com informações do agente
        """
        try:
            return AGENTES_KNOWLEDGE_BASE[area]["subagentes"][agent_name]
        except KeyError:
            return None


# 🧪 FUNÇÃO DE TESTE
async def test_classifier():
    """Testa o classificador com perguntas exemplo"""
    classifier = AgentClassifier()
    
    test_questions = [
        "Como faço para resetar minha senha do SAP?",
        "Quero saber sobre meu PPR deste ano",
        "Minha VPN não está conectando, o que fazer?",
        "Preciso tirar férias em dezembro, qual o processo?",
        "Como funciona a política de LGPD na empresa?"
    ]
    
    print("🧪 TESTANDO CLASSIFICADOR INTELIGENTE\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"TESTE {i}: {question}")
        print('='*80)
        
        result = await classifier.classify_question(question)
        
        print(f"\n📊 ANÁLISE: {result['analise']}")
        print(f"🎯 ÁREA: {result['area_principal'].upper()}")
        print("\n🤖 AGENTES SELECIONADOS:")
        
        for j, agent in enumerate(result['agentes_selecionados'], 1):
            print(f"  {j}. {agent['agente']} ({agent['relevancia']})")
            print(f"     → {agent['justificativa']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_classifier())
