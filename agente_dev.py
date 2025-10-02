"""Agente especializado de Desenvolvimento padronizado com a infraestrutura compartilhada."""

from __future__ import annotations

from textwrap import dedent
from typing import Optional

from subagents.base_subagent import BaseSubagent, SubagentConfig

PROMPT_TEMPLATE = dedent(
    """
Você é Carlos, um especialista em Desenvolvimento de Sistemas. Você faz parte do ecossistema Neoson e orienta colaboradores internos com dúvidas relacionadas ao desenvolvimento, aplicações e sistemas.

IMPORTANTE: Baseie suas respostas SOMENTE nas informações do contexto fornecido abaixo.

DIRETRIZES DE RESPOSTA:
- Adote tom profissional, cordial e acessível
- Explique termos técnicos quando necessário e sugira próximos passos
- Mencione histórico prévio quando aplicável
- Varie saudações e evite repetição excessiva
- Utilize emojis moderadamente para humanizar a conversa (opcional)
- Alerte quando o conteúdo parecer desatualizado ou incompleto
- Foque em desenvolvimento, aplicações e sistemas

CASOS ESPECIAIS:
- Sem informação relevante: "Não localizei essa informação na base atual de desenvolvimento. Recomendo acionar o time responsável ou registrar um ticket conforme o procedimento padrão."
- Informação restrita: "Essa informação é restrita. Solicite autorização formal à liderança ou registre um ticket justificando a necessidade."
- Conteúdo possivelmente obsoleto: "⚠️ Atenção: essa informação pode estar desatualizada. Valide com o time de desenvolvimento antes de seguir."

{historico_conversa}CONTEXTO DISPONÍVEL:
{contexto}

PERGUNTA DO COLABORADOR:
{pergunta}

RESPOSTA (considere desenvolvimento e histórico ao responder):
    """
).strip()

KEYWORDS = ['desenvolvimento', 'aplicação', 'sistema', 'código', 'projeto', 'bug', 'feature', 'deploy', 'release', 'api', 'banco', 'dados']


class AgenteDev(BaseSubagent):
    """Agente especializado em Desenvolvimento configurado via infraestrutura compartilhada."""

    def __init__(self, *, debug: bool = False) -> None:
        config = SubagentConfig(
            identifier="dev",
            name="Carlos",
            specialty="Desenvolvimento",
            description="Especialista em desenvolvimento de sistemas, aplicações e projetos de software",
            keywords=KEYWORDS,
            prompt_template=PROMPT_TEMPLATE,
            table_name="knowledge_ARCHITETURE & DEV",
            llm_model="gpt-4o-mini",
            llm_temperature=0.3,
            llm_max_tokens=10000,
            error_message="Ops! Tive um problema técnico aqui. Que tal tentar novamente em instantes ou acionar o suporte?",
            debug=debug,
            # MCP Configuration
            enable_mcp_tools=False,
            mcp_tools_category="dev",
            mcp_tool_server_url=None,
        )
        super().__init__(config)


def criar_agente_dev(*, debug: bool = False) -> Optional[AgenteDev]:
    """Factory function para criar o agente de Desenvolvimento padronizado."""
    agente = AgenteDev(debug=debug)
    return agente if agente.inicializar() else None


if __name__ == "__main__":
    agente = criar_agente_dev(debug=True)
    if not agente:
        raise SystemExit("Falha ao inicializar o agente de Desenvolvimento.")

    perfil_demo = {
        "nome": "Fulano de Tal",
        "cargo": "Desenvolvimento Specialist",
        "area": "Desenvolvimento",
        "nivel_hierarquico": 3,
        "geografia": "BR",
        "projetos": ["N/A"],
    }

    perguntas_demo = [
        "Como faço deploy de uma nova versão?",
        "Qual é o processo para reportar bugs?",
    ]

    for pergunta in perguntas_demo:
        print(f"\n❓ Pergunta: {pergunta}")
        resposta = agente.processar_pergunta(pergunta, perfil_demo)
        print(f"🤖 Carlos: {resposta}")
        print("-" * 80)
