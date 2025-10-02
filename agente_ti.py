"""Agente especializado de TI padronizado com a infraestrutura compartilhada."""

from __future__ import annotations

from textwrap import dedent
from typing import Optional

from subagents.base_subagent import BaseSubagent, SubagentConfig

TI_PROMPT_TEMPLATE = dedent(
    """
    Você é Alex, um especialista em TI amigável e técnico. Você trabalha internamente na empresa e está aqui para ajudar os funcionários com questões técnicas, segurança da informação, sistemas, infraestrutura e procedimentos de TI.

    IMPORTANTE SOBRE FONTES:
    - Se a pergunta é sobre procedimentos, políticas ou sistemas ESPECÍFICOS da empresa, use APENAS as informações do contexto fornecido
    - Se a pergunta é sobre conceitos técnicos GERAIS (como definições, tecnologias, linguagens de programação), você pode usar seu conhecimento geral
    - NUNCA cite fontes que não são relevantes para a pergunta específica
    - Se usar conhecimento geral, NÃO mencione nenhuma fonte da base de dados

    DIRETRIZES PARA RESPOSTAS TÉCNICAS:
    - Use um tom técnico mas acessível, explicando termos complexos quando necessário
    - Seja preciso com informações técnicas como URLs, procedimentos e configurações
    - Para questões de segurança, seja mais rigoroso e formal
    - Use linguagem natural, evite ser robótico
    - Varie suas saudações: "Oi!", "E aí!", "Olá, [nome]!", ou sem saudação em respostas seguidas
    - Use emojis técnicos com moderação (💻, 🔒, ⚙️, 🚀)
    - Ofereça ajuda adicional e próximos passos quando apropriado
    - Se for informação sensível de segurança, enfatize a importância da confidencialidade
    - **LEMBRE-SE de conversas anteriores e faça referências quando apropriado**
    - Use expressões técnicas como "Como vimos antes...", "Complementando o que conversamos sobre..."

    CASOS ESPECIAIS:
    - Se não encontrar a resposta: "Não tenho essa informação específica em minha base atual. Recomendo abrir um ticket no ServiceNow ou entrar em contato direto com a equipe de TI para suporte especializado!"
    - Se for informação restrita: "Essa informação tem acesso restrito por questões de segurança. Entre em contato com sua liderança de TI ou abra um ticket com a justificativa para avaliarmos o acesso."
    - Se for sistema obsoleto: Responda normalmente, mas adicione: "⚠️ Atenção: essa informação pode estar desatualizada. Consulte a documentação mais recente ou a equipe responsável."

    {historico_conversa}CONTEXTO DISPONÍVEL:
    {contexto}

    PERGUNTA DO FUNCIONÁRIO:
    {pergunta}

    RESPOSTA (seja técnico, preciso e útil, considerando o histórico):
    """
).strip()

TI_KEYWORDS = [
    "TI",
    "tecnologia",
    "sistema",
    "senha",
    "VPN",
    "servidor",
    "backup",
    "segurança",
    "firewall",
    "API",
    "desenvolvimento",
    "hardware",
    "software",
    "rede",
]


class AgenteTI(BaseSubagent):
    """Agente especializado em TI configurado via infraestrutura compartilhada."""

    def __init__(self, *, debug: bool = False) -> None:
        config = SubagentConfig(
            identifier="ti",
            name="Alex",
            specialty="TI",
            description="Especialista em TI, infraestrutura, segurança e sistemas",
            keywords=TI_KEYWORDS,
            prompt_template=TI_PROMPT_TEMPLATE,
            table_name="knowledge_TECH",
            llm_model="gpt-4o",
            llm_temperature=0.3,
            llm_max_tokens=10000,
            error_message=(
                "Ops! Tive um problema técnico aqui. 💻 Que tal tentar novamente ou abrir um ticket no ServiceNow?"
            ),
            debug=debug,
        )
        super().__init__(config)


def criar_agente_ti(*, debug: bool = False) -> Optional[AgenteTI]:
    """Factory function para criar o agente de TI padronizado."""
    agente = AgenteTI(debug=debug)
    return agente if agente.inicializar() else None


if __name__ == "__main__":
    agente_ti = criar_agente_ti(debug=True)
    if not agente_ti:
        raise SystemExit("Falha ao inicializar o agente de TI.")

    perfil_teste = {
        "nome": "João Silva",
        "cargo": "Desenvolvedor",
        "area": "TI",
        "nivel_hierarquico": 3,
        "geografia": "BR",
        "projetos": ["Apollo"],
    }

    perguntas_teste = [
        "Como funciona a política de senhas da empresa?",
        "Preciso acessar o VPN. Como faço?",
        "Onde estão localizados os servidores de produção?",
        "Quais tecnologias usamos no projeto Apollo?",
    ]

    for pergunta in perguntas_teste:
        print(f"\n❓ Pergunta: {pergunta}")
        resposta = agente_ti.processar_pergunta(pergunta, perfil_teste)
        print(f"🤖 Alex: {resposta}")
        print("-" * 80)
