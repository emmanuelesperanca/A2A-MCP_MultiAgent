"""Tools específicas para o agente de Recursos Humanos."""

from .base import MCPTool

# Tools de RH - Começando com simulações locais (sem endpoint)
rh_tools = [
    MCPTool(
        name="consultar_saldo_ferias",
        description="Consulta o saldo de férias disponível do colaborador",
        parameters={
            "cpf": {
                "type": "string",
                "description": "CPF do colaborador (apenas números)",
                "required": True
            },
            "ano": {
                "type": "string",
                "description": "Ano de referência (YYYY)",
                "required": False,
                "default": "2025"
            }
        },
        category="rh",
        # endpoint=None significa que é uma tool local/simulada por enquanto
    ),

    MCPTool(
        name="consultar_banco_horas",
        description="Consulta o saldo atual de banco de horas do colaborador",
        parameters={
            "cpf": {
                "type": "string",
                "description": "CPF do colaborador (apenas números)",
                "required": True
            },
            "periodo": {
                "type": "string",
                "description": "Período no formato YYYY-MM",
                "required": False
            }
        },
        category="rh",
    ),
    
    MCPTool(
        name="solicitar_ferias",
        description="Cria uma solicitação de férias no sistema de RH",
        parameters={
            "cpf": {
                "type": "string",
                "description": "CPF do colaborador",
                "required": True
            },
            "data_inicio": {
                "type": "string",
                "description": "Data de início das férias (YYYY-MM-DD)",
                "required": True
            },
            "data_fim": {
                "type": "string",
                "description": "Data de fim das férias (YYYY-MM-DD)",
                "required": True
            },
            "observacoes": {
                "type": "string",
                "description": "Observações adicionais sobre as férias",
                "required": False,
                "optional": True
            }
        },
        category="rh",
    ),
    
    MCPTool(
        name="consultar_beneficios",
        description="Consulta benefícios disponíveis e utilizados pelo colaborador",
        parameters={
            "cpf": {
                "type": "string",
                "description": "CPF do colaborador",
                "required": True
            },
            "tipo_beneficio": {
                "type": "string",
                "description": "Tipo específico de benefício (vale_refeicao, plano_saude, etc.) ou 'todos'",
                "required": False,
                "default": "todos"
            }
        },
        category="rh",
    ),
    
    MCPTool(
        name="atualizar_dados_pessoais",
        description="Atualiza dados pessoais do colaborador no sistema",
        parameters={
            "cpf": {
                "type": "string",
                "description": "CPF do colaborador",
                "required": True
            },
            "campo": {
                "type": "string",
                "description": "Campo a ser atualizado (telefone, endereco, email_pessoal, etc.)",
                "required": True
            },
            "novo_valor": {
                "type": "string",
                "description": "Novo valor para o campo",
                "required": True
            }
        },
        category="rh",
    )
]


def get_rh_tools():
    """Retorna a lista de tools de RH."""
    return rh_tools


def setup_rh_tools_registry():
    """Configura as tools de RH no registry global."""
    from .registry import default_registry
    
    for tool in rh_tools:
        default_registry.register_tool(tool, "rh")
    
    return len(rh_tools)