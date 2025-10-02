"""Tools específicas para o agente de Tecnologia da Informação."""

from .base import MCPTool

# Tools de TI - Começando com simulações locais (sem endpoint)
ti_tools = [
    MCPTool(
        name="resetar_senha_usuario",
        description="Reseta a senha de um usuário no Active Directory",
        parameters={
            "username": {
                "type": "string",
                "description": "Nome de usuário (login) no Active Directory",
                "required": True
            },
            "gerar_temporaria": {
                "type": "boolean",
                "description": "Se deve gerar senha temporária ou permitir que usuário defina",
                "required": False,
                "default": True
            },
            "forcar_mudanca": {
                "type": "boolean",
                "description": "Se deve forçar mudança de senha no próximo login",
                "required": False,
                "default": True
            }
        },
        category="ti",
    ),
    
    MCPTool(
        name="verificar_status_servidor",
        description="Verifica o status de saúde de servidores e serviços",
        parameters={
            "servidor": {
                "type": "string",
                "description": "Nome ou IP do servidor a verificar",
                "required": True
            },
            "servicos": {
                "type": "array",
                "description": "Lista de serviços específicos para verificar",
                "items": {"type": "string"},
                "required": False
            },
            "incluir_metricas": {
                "type": "boolean",
                "description": "Se deve incluir métricas de performance (CPU, RAM, etc.)",
                "required": False,
                "default": False
            }
        },
        category="ti",
    ),
    
    MCPTool(
        name="criar_chamado_ti",
        description="Cria um novo chamado de suporte técnico",
        parameters={
            "solicitante": {
                "type": "string",
                "description": "Nome ou email do solicitante",
                "required": True
            },
            "titulo": {
                "type": "string",
                "description": "Título resumido do problema",
                "required": True
            },
            "descricao": {
                "type": "string",
                "description": "Descrição detalhada do problema",
                "required": True
            },
            "prioridade": {
                "type": "string",
                "description": "Prioridade do chamado: baixa, media, alta, critica",
                "required": False,
                "default": "media"
            },
            "categoria": {
                "type": "string",
                "description": "Categoria do problema: hardware, software, rede, acesso, email, etc.",
                "required": False,
                "default": "geral"
            }
        },
        category="ti",
    ),
    
    MCPTool(
        name="verificar_espaco_disco",
        description="Verifica o espaço em disco disponível nos servidores",
        parameters={
            "servidor": {
                "type": "string",
                "description": "Nome do servidor ou 'todos' para verificar todos",
                "required": True
            },
            "unidade": {
                "type": "string",
                "description": "Unidade específica (C:, D:, etc.) ou 'todas'",
                "required": False,
                "default": "todas"
            },
            "limite_alerta": {
                "type": "number",
                "description": "Percentual de uso para gerar alerta (0-100)",
                "required": False,
                "default": 80
            }
        },
        category="ti",
    ),
    
    MCPTool(
        name="gerenciar_acesso_vpn",
        description="Gerencia acesso VPN de usuários (ativar, desativar, verificar status)",
        parameters={
            "username": {
                "type": "string",
                "description": "Nome de usuário",
                "required": True
            },
            "acao": {
                "type": "string",
                "description": "Ação a realizar: ativar, desativar, verificar_status",
                "required": True
            },
            "periodo_dias": {
                "type": "number",
                "description": "Período em dias para acesso temporário (apenas para ação 'ativar')",
                "required": False
            }
        },
        category="ti",
    ),
    
    MCPTool(
        name="backup_status",
        description="Verifica o status dos backups automáticos",
        parameters={
            "sistema": {
                "type": "string",
                "description": "Sistema específico ou 'todos' para verificar todos os backups",
                "required": True
            },
            "periodo": {
                "type": "string",
                "description": "Período para verificar: hoje, semana, mes",
                "required": False,
                "default": "hoje"
            }
        },
        category="ti",
    )
]


def get_ti_tools():
    """Retorna a lista de tools de TI."""
    return ti_tools


def setup_ti_tools_registry():
    """Configura as tools de TI no registry global."""
    from .registry import default_registry
    
    for tool in ti_tools:
        default_registry.register_tool(tool, "ti")
    
    return len(ti_tools)