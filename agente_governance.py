"""Agente especializado de Governança de TI padronizado com a infraestrutura compartilhada."""

from __future__ import annotations

from textwrap import dedent
from typing import Optional

from subagents.base_subagent import BaseSubagent, SubagentConfig

PROMPT_TEMPLATE = dedent(
    """
    Você é Ariel, um(a) especialista em Governança de TI. Você faz parte do ecossistema Neoson e orienta colaboradores internos com dúvidas relacionadas à especialidade.

    IMPORTANTE:
    1. RESPONDA SEMPRE NO MESMO IDIOMA da pergunta do usuário (português, inglês, espanhol, etc.)
    2. CONSULTE TODAS as documentações disponíveis independente do idioma (português, inglês, espanhol)
    3. TRADUZA e ADAPTE o conteúdo dos documentos para o idioma da resposta
    4. CITE SEMPRE as fontes originais com seus nomes originais

    Somos uma empresa global e seguimos normas nacionais e internacionais de governança, compliance e segurança da informação.

    ESTRUTURA DA RESPOSTA:
    - Para cada política/norma encontrada, organize por fonte
    - Traduza o conteúdo para o idioma da pergunta mantendo precisão técnica
    - Indique claramente qual norma/política cada resposta se refere
    - Mantenha os nomes originais dos documentos nas citações

    DIRETRIZES DE RESPOSTA:
    - Detecte automaticamente o idioma da pergunta e responda no mesmo idioma
    - Adote tom profissional, cordial e acessível
    - Explique termos técnicos quando necessário
    - Para documentos em inglês respondendo em português: traduza mantendo termos técnicos precisos
    - Para documentos em português respondendo em inglês: traduza mantendo conformidade regulatória
    - Mencione histórico prévio quando aplicável
    - Utilize emojis moderadamente para humanizar a conversa (opcional)
    - Alerte quando o conteúdo parecer desatualizado

    CASOS ESPECIAIS POR IDIOMA:
    
    Se pergunta em PORTUGUÊS:
    - Sem informação: "Não localizei essa informação na base atual. Recomendo acionar o time responsável ou registrar um ticket."
    - Informação restrita: "Essa informação é restrita. Solicite autorização formal à liderança."
    - Conteúdo obsoleto: "⚠️ Atenção: essa informação pode estar desatualizada. Valide com o time responsável."
    
    Se pergunta em INGLÊS:
    - Sem informação: "I couldn't find this information in the current database. I recommend contacting the responsible team or submitting a ticket."
    - Informação restrita: "This information is restricted. Please request formal authorization from leadership."
    - Conteúdo obsoleto: "⚠️ Warning: this information may be outdated. Please validate with the responsible team."
    
    Se pergunta em ESPANHOL:
    - Sem informação: "No pude encontrar esta información en la base actual. Recomiendo contactar al equipo responsable o crear un ticket."
    - Informação restrita: "Esta información es restringida. Solicite autorización formal del liderazgo."
    - Conteúdo obsoleto: "⚠️ Atención: esta información puede estar desactualizada. Valide con el equipo responsable."

    {historico_conversa}CONTEXTO DISPONÍVEL:
    {contexto}

    PERGUNTA DO COLABORADOR:
    {pergunta}

    RESPOSTA (no mesmo idioma da pergunta, consultando documentos em qualquer idioma):
    """
).strip()

KEYWORDS = [
    # Português
    'política', 'compliance', 'auditoria', 'segurança', 'lgpd', 'iso', 'itil',
    'governança', 'riscos', 'controle', 'norma', 'Governança de TI', 'senhas',
    'assinatura', 'digital', 'eletrônica', 'validação', 'conformidade',

    # Inglês
    'policy', 'governance', 'compliance', 'audit', 'security', 'gdpr',
    'signature', 'digital', 'electronic', 'validation', 'regulatory',
    'control', 'risk', 'standard', 'password', 'authentication',

    # Espanhol
    'política', 'gobernanza', 'cumplimiento', 'auditoría', 'seguridad',
    'firma', 'digital', 'electrónica', 'validación', 'normativa',
    'control', 'riesgo', 'estándar', 'contraseña', 'autenticación'
]


class AgenteGovernance(BaseSubagent):
    """Agente especializado em Governança de TI configurado via infraestrutura compartilhada."""

    def __init__(self, *, debug: bool = False) -> None:
        config = SubagentConfig(
            identifier="governance",
            name="Ariel",
            specialty="Governança de TI",
            description="Especialista em governança de TI, compliance, políticas de segurança e conformidade regulatória",
            keywords=KEYWORDS,
            prompt_template=PROMPT_TEMPLATE,
            table_name="knowledge_IT GOVERNANCE & DELIVERY METHODS",
            llm_model="gpt-4o",
            llm_temperature=0.3,
            llm_max_tokens=10000,
            error_message="Ops! Tive um problema técnico aqui. Que tal tentar novamente em instantes ou acionar o suporte?",
            debug=debug,
            # MCP Configuration
            enable_mcp_tools=False,
            mcp_tools_category="governance",
            mcp_tool_server_url=None,
        )
        super().__init__(config)


def criar_agente_governance(*, debug: bool = False) -> Optional[AgenteGovernance]:
    """Factory function para criar o agente de Governança de TI padronizado."""
    agente = AgenteGovernance(debug=debug)
    return agente if agente.inicializar() else None


if __name__ == "__main__":
    agente = criar_agente_governance(debug=True)
    if not agente:
        raise SystemExit("Falha ao inicializar o agente de Governança de TI.")

    perfil_demo = {
        "nome": "Fulano de Tal",
        "cargo": "Governança de TI Specialist",
        "area": "Governança de TI",
        "nivel_hierarquico": 3,
        "geografia": "BR",
        "projetos": ["N/A"],
    }

    perguntas_demo = [
        "Qual é o procedimento padrão para a área de Governança de TI?",
        "Existe alguma política específica que eu deva conhecer?",
    ]

    for pergunta in perguntas_demo:
        print(f"\n❓ Pergunta: {pergunta}")
        resposta = agente.processar_pergunta(pergunta, perfil_demo)
        print(f"🤖 Ariel: {resposta}")
        print("-" * 80)
