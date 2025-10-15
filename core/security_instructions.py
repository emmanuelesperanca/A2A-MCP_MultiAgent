# 🔒 INSTRUÇÕES DE SEGURANÇA PARA AGENTES
# Regras que devem ser incluídas em todos os prompts dos agentes

SECURITY_INSTRUCTIONS = """
**⚠️ REGRAS DE SEGURANÇA - OBRIGATÓRIAS:**

1. **PROIBIDO ENVIAR LINKS:**
   - NUNCA inclua URLs, links ou endereços web nas suas respostas
   - NUNCA sugira "acesse este link" ou "clique aqui"
   - Se precisar referenciar um sistema, mencione apenas o NOME do sistema
   - Exemplo correto: "Acesse o sistema SAP"
   - Exemplo ERRADO: "Acesse https://sap.company.com"
   
2. **CONFIDENCIALIDADE:**
   - Não compartilhe informações sensíveis sem verificação
   - Não mencione senhas, códigos ou credenciais
   
3. **PRECISÃO:**
   - Se não souber a resposta, diga "Não tenho essa informação"
   - Não invente informações
   - Base suas respostas apenas nos dados da base de conhecimento
"""

LINK_PROHIBITION_NOTICE = """
🔒 **ATENÇÃO:** Por motivos de segurança, este sistema NÃO fornece links diretos.
Se você precisa acessar um sistema específico, procure o nome do sistema no seu menu
de aplicações corporativas ou contate o suporte para orientações.
"""


def get_security_prompt() -> str:
    """Retorna as instruções de segurança formatadas para inclusão em prompts"""
    return SECURITY_INSTRUCTIONS.strip()


def get_link_prohibition_notice() -> str:
    """Retorna o aviso sobre proibição de links"""
    return LINK_PROHIBITION_NOTICE.strip()


def inject_security_in_prompt(prompt: str) -> str:
    """
    Injeta instruções de segurança em um prompt existente
    
    Args:
        prompt: Prompt original
        
    Returns:
        Prompt com instruções de segurança injetadas
    """
    security_section = f"\n\n{SECURITY_INSTRUCTIONS}\n"
    
    # Inserir antes das instruções finais ou no final
    if "INSTRUÇÕES:" in prompt or "INSTRUCTIONS:" in prompt:
        # Inserir antes das instruções
        parts = prompt.split("INSTRUÇÕES:" if "INSTRUÇÕES:" in prompt else "INSTRUCTIONS:", 1)
        return parts[0] + security_section + ("INSTRUÇÕES:" if "INSTRUÇÕES:" in prompt else "INSTRUCTIONS:") + parts[1]
    else:
        # Adicionar no final
        return prompt + security_section
