"""Agente especializado de Infraestrutura de TI padronizado com a infraestrutura compartilhada."""

from __future__ import annotations

from textwrap import dedent
from typing import Optional

from subagents.base_subagent import BaseSubagent, SubagentConfig

PROMPT_TEMPLATE = dedent(
    """
    Você é Alice, um(a) especialista em Infraestrutura de TI. Você faz parte do ecossistema Neoson e orienta colaboradores internos com dúvidas relacionadas à especialidade.

    IMPORTANTE: Baseie suas respostas SOMENTE nas informações do contexto fornecido abaixo.

    DIRETRIZES DE RESPOSTA:
    - Adote tom profissional, cordial e acessível
    - Explique termos técnicos quando necessário e sugira próximos passos
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

    RESPOSTA (considere governança e histórico ao responder):
    """
).strip()

KEYWORDS = ['servidor', 'rede', 'hardware', 'datacenter', 'backup', 'Infraestrutura de TI']


class AgenteInfra(BaseSubagent):
    """Agente especializado em Infraestrutura de TI configurado via infraestrutura compartilhada."""

    def __init__(self, *, debug: bool = False) -> None:
        config = SubagentConfig(
            identifier="infra",
            name="Alice",
            specialty="Infraestrutura de TI",
            description="Especialista em infraestrutura de TI e operações",
            keywords=KEYWORDS,
            prompt_template=PROMPT_TEMPLATE,
            table_name="knowledge_TECH",
            llm_model="gpt-4o-mini",
            llm_temperature=0.3,
            llm_max_tokens=10000,
            error_message="Ops! Tive um problema técnico aqui. Que tal tentar novamente em instantes ou acionar o suporte?",
            debug=debug,
            # MCP Configuration
            enable_mcp_tools=False,
            mcp_tools_category="infra",
            mcp_tool_server_url=None,
        )
        super().__init__(config)


def criar_agente_infra(*, debug: bool = False) -> Optional[AgenteInfra]:
    """Factory function para criar o agente de Infraestrutura de TI padronizado."""
    agente = AgenteInfra(debug=debug)
    return agente if agente.inicializar() else None


if __name__ == "__main__":
    agente = criar_agente_infra(debug=True)
    if not agente:
        raise SystemExit("Falha ao inicializar o agente de Infraestrutura de TI.")

    perfil_demo = {
        "nome": "Fulano de Tal",
        "cargo": "Infraestrutura de TI Specialist",
        "area": "Infraestrutura de TI",
        "nivel_hierarquico": 3,
        "geografia": "BR",
        "projetos": ["N/A"],
    }

    perguntas_demo = [
        "Qual é o procedimento padrão para a área de Infraestrutura de TI?",
        "Existe alguma política específica que eu deva conhecer?",
    ]

    for pergunta in perguntas_demo:
        print(f"\n❓ Pergunta: {pergunta}")
        resposta = agente.processar_pergunta(pergunta, perfil_demo)
        print(f"🤖 Alice: {resposta}")
        print("-" * 80)
