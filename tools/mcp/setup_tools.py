"""Script para inicializar e configurar todas as MCP tools no registry."""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_all_tools():
    """Configura todas as tools MCP disponíveis no registry global."""
    from .registry import default_registry
    
    total_tools = 0
    
    try:
        # Configura tools de RH
        from .rh_tools import setup_rh_tools_registry
        rh_count = setup_rh_tools_registry()
        total_tools += rh_count
        logger.info(f"✅ {rh_count} tools de RH configuradas")
        
        # Configura tools de TI
        from .ti_tools import setup_ti_tools_registry
        ti_count = setup_ti_tools_registry()
        total_tools += ti_count
        logger.info(f"✅ {ti_count} tools de TI configuradas")
        
        # Mostra estatísticas finais
        stats = default_registry.get_stats()
        logger.info(f"📊 Registry configurado: {stats}")
        
        return total_tools
        
    except Exception as e:
        logger.error(f"❌ Erro ao configurar tools: {e}")
        return 0


def list_available_tools():
    """Lista todas as tools disponíveis por categoria."""
    from .registry import default_registry
    
    print("\n🔧 === MCP TOOLS DISPONÍVEIS ===")
    
    for category in default_registry.list_categories():
        tools = default_registry.get_tools_for_category(category)
        print(f"\n📁 Categoria: {category.upper()}")
        print("-" * 40)
        
        for tool in tools:
            print(f"  🛠️  {tool.name}")
            print(f"      📝 {tool.description}")
            
            # Mostra parâmetros principais
            params = []
            for param_name, param_def in tool.parameters.items():
                if isinstance(param_def, dict) and param_def.get("required", False):
                    params.append(f"{param_name}*")
                else:
                    params.append(param_name)
            
            if params:
                print(f"      📋 Parâmetros: {', '.join(params[:3])}{'...' if len(params) > 3 else ''}")
            print()


if __name__ == "__main__":
    print("🚀 Inicializando MCP Tools Registry...")
    
    # Configura todas as tools
    total = setup_all_tools()
    
    if total > 0:
        print(f"\n✅ {total} tools configuradas com sucesso!")
        list_available_tools()
    else:
        print("\n❌ Falha na configuração das tools")