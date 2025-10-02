"""Agente especializado de Suporte ao Usuário Final padronizado com a infraestrutura compartilhada."""

from __future__ import annotations

from textwrap import dedent
from typing import Optional

from subagents.base_subagent import BaseSubagent, SubagentConfig

PROMPT_TEMPLATE = dedent(
    """
Você é Marina, uma especialista em Suporte ao Usuário Final. Você faz parte do ecossistema Neoson e orienta colaboradores internos com dúvidas relacionadas ao uso de sistemas, aplicações e ferramentas do dia a dia.

IMPORTANTE: Baseie suas respostas SOMENTE nas informações do contexto fornecido abaixo.

DIRETRIZES DE RESPOSTA:
- Adote tom profissional, cordial e acessível
- Explique procedimentos de forma simples e clara
- Forneça passos detalhados quando necessário
- Mencione histórico prévio quando aplicável
- Varie saudações e evite repetição excessiva
- Utilize emojis moderadamente para humanizar a conversa (opcional)
- Foque em soluções práticas para o usuário final

CASOS ESPECIAIS:
- Sem informação relevante: "Não localizei essa informação na base atual de suporte. Recomendo abrir um chamado no help desk ou contatar o suporte técnico."
- Informação restrita: "Essa função requer permissões específicas. Entre em contato com seu gestor ou o help desk para verificar seus acessos."
- Conteúdo possivelmente obsoleto: "⚠️ Atenção: esse procedimento pode ter mudado. Valide com o help desk antes de seguir."

{historico_conversa}CONTEXTO DISPONÍVEL:
{contexto}

PERGUNTA DO COLABORADOR:
{pergunta}

RESPOSTA (considere usabilidade e histórico ao responder):
    """
).strip()

KEYWORDS = ['senha', 'login', 'acesso', 'reset', 'email', 'outlook', 'word', 'excel', 'teams', 'usuario', 'conta', 'perfil', 'suporte', 'help', 'ajuda', 'como usar']


class AgenteEndUser(BaseSubagent):
    """Agente especializado em Suporte ao Usuário Final configurado via infraestrutura compartilhada."""

    def __init__(self, *, debug: bool = False) -> None:
        config = SubagentConfig(
            identifier="enduser",
            name="Marina",
            specialty="Suporte ao Usuário Final",
            description="Especialista em suporte a usuários finais, sistemas corporativos e ferramentas do dia a dia",
            keywords=KEYWORDS,
            prompt_template=PROMPT_TEMPLATE,
            table_name="knowledge_END-USER",
            llm_model="gpt-4o-mini",
            llm_temperature=0.3,
            llm_max_tokens=10000,
            error_message="Ops! Tive um problema técnico aqui. Que tal tentar novamente em instantes ou acionar o suporte?",
            debug=debug,
            # MCP Configuration
            enable_mcp_tools=False,
            mcp_tools_category="enduser",
            mcp_tool_server_url=None,
        )
        super().__init__(config)


def criar_agente_enduser(*, debug: bool = False) -> Optional[AgenteEndUser]:
    """Factory function para criar o agente de Suporte ao Usuário Final padronizado."""
    agente = AgenteEndUser(debug=debug)
    return agente if agente.inicializar() else None


if __name__ == "__main__":
    agente = criar_agente_enduser(debug=True)
    if not agente:
        raise SystemExit("Falha ao inicializar o agente de Suporte ao Usuário Final.")

    perfil_demo = {
        "nome": "Fulano de Tal",
        "cargo": "Analista",
        "area": "Comercial",
        "nivel_hierarquico": 2,
        "geografia": "BR",
        "projetos": ["N/A"],
    }

    perguntas_demo = [
        "Como resetar minha senha do sistema?",
        "Como usar o Teams para reuniões?",
    ]

    for pergunta in perguntas_demo:
        print(f"\n❓ Pergunta: {pergunta}")
        resposta = agente.processar_pergunta(pergunta, perfil_demo)
        print(f"🤖 Marina: {resposta}")
        print("-" * 80)
