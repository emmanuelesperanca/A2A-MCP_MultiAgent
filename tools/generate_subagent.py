#!/usr/bin/env python3
"""Utilitário de linha de comando para gerar novos subagentes padronizados."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from string import Template
from textwrap import dedent, indent

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LLM_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 10000
DEFAULT_ERROR_MESSAGE = (
    "Ops! Tive um problema técnico aqui. Que tal tentar novamente em instantes ou acionar o suporte?"
)

AGENT_TEMPLATE = Template(
    dedent(
        '''\
"""Agente especializado de $specialty padronizado com a infraestrutura compartilhada."""

from __future__ import annotations

from textwrap import dedent
from typing import Optional

from subagents.base_subagent import BaseSubagent, SubagentConfig

PROMPT_TEMPLATE = dedent(
    """
$prompt_block
    """
).strip()

KEYWORDS = $keywords


class $class_name(BaseSubagent):
    """Agente especializado em $specialty configurado via infraestrutura compartilhada."""

    def __init__(self, *, debug: bool = False) -> None:
        config = SubagentConfig(
            identifier="$identifier",
            name="$persona_name",
            specialty="$specialty",
            description="$description",
            keywords=KEYWORDS,
            prompt_template=PROMPT_TEMPLATE,
            llm_model="$llm_model",
            llm_temperature=$llm_temperature,
            llm_max_tokens=$llm_max_tokens,
            error_message="$error_message",
            debug=debug,
            # MCP Configuration
            enable_mcp_tools=$enable_mcp_tools,
            mcp_tools_category="$mcp_tools_category",
            mcp_tool_server_url=$mcp_tool_server_url,
        )
        super().__init__(config)


def criar_agente_$identifier(*, debug: bool = False) -> Optional[$class_name]:
    """Factory function para criar o agente de $specialty padronizado."""
    agente = $class_name(debug=debug)
    return agente if agente.inicializar() else None


if __name__ == "__main__":
    agente = criar_agente_$identifier(debug=True)
    if not agente:
        raise SystemExit("Falha ao inicializar o agente de $specialty.")

    perfil_demo = {
        "nome": "Fulano de Tal",
        "cargo": "$specialty Specialist",
        "area": "$specialty",
        "nivel_hierarquico": 3,
        "geografia": "BR",
        "projetos": ["N/A"],
    }

    perguntas_demo = [
        "Qual é o procedimento padrão para a área de $specialty?",
        "Existe alguma política específica que eu deva conhecer?",
    ]

    for pergunta in perguntas_demo:
        print(f"\\n❓ Pergunta: {pergunta}")
        resposta = agente.processar_pergunta(pergunta, perfil_demo)
        print(f"🤖 $persona_name: {resposta}")
        print("-" * 80)
'''
    )
)

DDL_TEMPLATE = Template(
    dedent(
        '''\
-- DDL gerada para a tabela vetorial multi-tenant do subagente "$identifier"
CREATE TABLE IF NOT EXISTS $table_name (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    conteudo_original TEXT NOT NULL,
    fonte_documento TEXT,
    dado_sensivel BOOLEAN DEFAULT FALSE,
    apenas_para_si BOOLEAN DEFAULT FALSE,
    areas_liberadas TEXT[],
    nivel_hierarquico_minimo SMALLINT DEFAULT 1,
    geografias_liberadas TEXT[],
    projetos_liberados TEXT[],
    idioma VARCHAR(10),
    data_validade DATE,
    responsavel TEXT,
    aprovador TEXT,
    data_ingestao TIMESTAMPTZ DEFAULT NOW(),
    vetor VECTOR(1536) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_${identifier}_tenant_id ON $table_name (tenant_id);
CREATE INDEX IF NOT EXISTS idx_${identifier}_fonte_documento ON $table_name (fonte_documento);
CREATE INDEX IF NOT EXISTS idx_${identifier}_data_validade ON $table_name (data_validade);

CREATE INDEX IF NOT EXISTS idx_${identifier}_vetor_hnsw
    ON $table_name USING hnsw (vetor vector_cosine_ops);
'''
    )
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("identifier", help="Identificador simples (slug) do subagente, ex: finance, facilities.")
    parser.add_argument("--persona-name", dest="persona_name", help="Nome usado pelo agente na conversa.")
    parser.add_argument("--specialty", help="Especialidade/área atendida pelo subagente.")
    parser.add_argument("--description", help="Descrição curta do agente para catálogos/metadados.")
    parser.add_argument(
        "--keywords",
        help="Lista de palavras-chave separadas por vírgula para roteamento (ex: sistemas,infraestrutura).",
    )
    parser.add_argument(
        "--llm-model", default=DEFAULT_LLM_MODEL, help="Modelo de linguagem principal (default: %(default)s)."
    )
    parser.add_argument(
        "--llm-temperature", type=float, default=DEFAULT_TEMPERATURE, help="Temperatura do modelo (default: %(default)s)."
    )
    parser.add_argument(
        "--llm-max-tokens", type=int, default=DEFAULT_MAX_TOKENS, help="Máximo de tokens de saída (default: %(default)s)."
    )
    parser.add_argument(
        "--error-message",
        default=DEFAULT_ERROR_MESSAGE,
        help="Mensagem de fallback em caso de erro do agente.",
    )
    parser.add_argument(
        "--ddl-dir",
        default="migrations",
        help="Diretório relativo onde salvar a DDL gerada (default: %(default)s).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Sobrescreve arquivos existentes se já houverem artefatos gerados.",
    )
    # Opções MCP
    parser.add_argument(
        "--enable-mcp",
        action="store_true",
        help="Habilita MCP Tools para este subagente.",
    )
    parser.add_argument(
        "--mcp-category",
        help="Categoria de tools MCP (ex: rh, ti, finance). Default: usa o identifier.",
    )
    parser.add_argument(
        "--mcp-server-url",
        help="URL base do servidor MCP (opcional, para tools remotas).",
    )
    return parser.parse_args()


def validate_identifier(identifier: str) -> str:
    slug = identifier.strip().lower().replace("-", "_")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", slug):
        raise ValueError(
            "identifier deve começar com letra minúscula e conter apenas letras minúsculas, números ou underscore"
        )
    return slug


def to_pascal_case(value: str) -> str:
    parts = re.split(r"[_\-]", value)
    return "".join(part.capitalize() for part in parts if part)


def ensure_keywords(base_keywords: list[str], specialty: str) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for keyword in base_keywords + [specialty]:
        kw = keyword.strip()
        if not kw:
            continue
        key = kw.lower()
        if key not in seen:
            seen.add(key)
            normalized.append(kw)
    return normalized


def render_agent_file(context: dict[str, object]) -> str:
    prompt_template: str = context.pop("prompt_template")  # type: ignore[assignment]
    prompt_block = indent(prompt_template, "    ")
    rendered = AGENT_TEMPLATE.substitute({**context, "prompt_block": prompt_block, "keywords": context["keywords"]})
    return rendered.strip() + "\n"


def render_prompt(persona_name: str, specialty: str) -> str:
    template = Template(
        dedent(
            '''\
Você é $persona_name, um(a) especialista em $specialty. Você faz parte do ecossistema Neoson e orienta colaboradores internos com dúvidas relacionadas à especialidade.

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
'''
        ).strip()
    )
    return template.substitute(persona_name=persona_name, specialty=specialty)


def render_ddl(identifier: str, table_name: str) -> str:
    return DDL_TEMPLATE.substitute(identifier=identifier, table_name=table_name).strip() + "\n"


def main() -> int:
    args = parse_args()
    try:
        identifier = validate_identifier(args.identifier)
    except ValueError as exc:
        print(f"❌ Identificador inválido: {exc}", file=sys.stderr)
        return 1

    persona_name = args.persona_name or to_pascal_case(identifier)
    specialty = args.specialty or persona_name

    # Gerar description mais rica semanticamente se não fornecida
    if not args.description:
        description = (
            f"Especialista em {specialty} no ecossistema Neoson, responsável por orientar "
            f"colaboradores em questões relacionadas à área, procedimentos, políticas e "
            f"melhores práticas específicas do domínio de {specialty.lower()}"
        )
    else:
        description = args.description

    base_keywords: list[str] = []
    if args.keywords:
        base_keywords.extend([item.strip() for item in args.keywords.split(",")])
    keywords = ensure_keywords(base_keywords, specialty)

    prompt_template = render_prompt(persona_name, specialty)

    class_name = f"Agente{to_pascal_case(identifier)}"
    module_name = f"agente_{identifier}.py"
    module_path = PROJECT_ROOT / module_name

    if module_path.exists() and not args.overwrite:
        print(f"❌ Arquivo '{module_name}' já existe. Use --overwrite para substituí-lo.", file=sys.stderr)
        return 1

    ddl_dir = PROJECT_ROOT / args.ddl_dir
    ddl_dir.mkdir(parents=True, exist_ok=True)
    table_name = f"knowledge_{identifier}"
    ddl_filename = f"create_{table_name}.sql"
    ddl_path = ddl_dir / ddl_filename

    if ddl_path.exists() and not args.overwrite:
        print(f"❌ Arquivo DDL '{ddl_filename}' já existe. Use --overwrite para substituí-lo.", file=sys.stderr)
        return 1

    # Configurações MCP
    mcp_category = args.mcp_category or identifier
    mcp_server_url = f'"{args.mcp_server_url}"' if args.mcp_server_url else "None"

    agent_content = render_agent_file(
        {
            "identifier": identifier,
            "persona_name": persona_name,
            "specialty": specialty,
            "description": description,
            "keywords": repr(keywords or [specialty]),
            "llm_model": args.llm_model,
            "llm_temperature": args.llm_temperature,
            "llm_max_tokens": args.llm_max_tokens,
            "error_message": args.error_message,
            "class_name": class_name,
            "prompt_template": prompt_template,
            # MCP params
            "enable_mcp_tools": str(args.enable_mcp).lower(),
            "mcp_tools_category": mcp_category,
            "mcp_tool_server_url": mcp_server_url,
        }
    )

    ddl_content = render_ddl(identifier, table_name)

    module_path.write_text(agent_content, encoding="utf-8")
    ddl_path.write_text(ddl_content, encoding="utf-8")

    table_env = f"KNOWLEDGE_{identifier.upper()}_TABLE"
    db_env = f"KNOWLEDGE_{identifier.upper()}_DATABASE_URL"

    print("✅ Subagente gerado com sucesso!")
    print(f"   • Arquivo do agente: {module_path.relative_to(PROJECT_ROOT)}")
    print(f"   • DDL da tabela: {ddl_path.relative_to(PROJECT_ROOT)}")
    print("\nPróximos passos sugeridos:")
    print(f"   1. Configure as variáveis de ambiente {table_env} e {db_env} conforme necessário.")
    print(f"   2. Execute a DDL gerada para criar a tabela {table_name} com suporte multi-tenant.")
    print(f"   3. Ajuste o prompt em {module_path.name} para refletir o tom desejado.")
    print("   4. Registre o novo agente no orquestrador (por exemplo, atualizando 'neoson.py').")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
