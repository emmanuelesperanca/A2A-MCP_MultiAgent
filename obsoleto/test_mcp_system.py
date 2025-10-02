"""Teste básico do sistema MCP - executar do diretório raiz do projeto."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.mcp.base import MCPTool, MCPClient
from tools.mcp.registry import ToolRegistry


def test_basic_mcp():
    """Teste básico da funcionalidade MCP."""
    print("🚀 Testando sistema MCP...")
    
    # 1. Criar uma tool simples de teste
    test_tool = MCPTool(
        name="test_ping",
        description="Tool de teste que retorna pong",
        parameters={
            "message": {
                "type": "string", 
                "description": "Mensagem para ecoar",
                "required": False,
                "default": "pong"
            }
        },
        category="test"
    )
    
    print(f"✅ Tool criada: {test_tool.name}")
    
    # 2. Criar registry e registrar tool
    registry = ToolRegistry()
    registry.register_tool(test_tool)
    
    print(f"✅ Tool registrada no registry")
    
    # 3. Criar cliente MCP
    client = MCPClient()
    client.register_tool(test_tool)
    
    print(f"✅ Cliente MCP criado")
    
    # 4. Executar tool
    result = client.call_tool("test_ping", {"message": "Hello MCP!"})
    
    print(f"📊 Resultado da execução:")
    print(f"   Status: {result.status}")
    print(f"   Sucesso: {result.is_success}")
    print(f"   Dados: {result.data}")
    print(f"   Tempo: {result.execution_time_ms}ms")
    
    # 5. Teste com tool inexistente
    result2 = client.call_tool("tool_inexistente", {})
    print(f"\n📊 Teste com tool inexistente:")
    print(f"   Status: {result2.status}")
    print(f"   Erro: {result2.error_message}")
    
    return True


def test_rh_ti_tools():
    """Testa as tools específicas de RH e TI."""
    print("\n🏢 Testando tools de RH e TI...")
    
    try:
        # Importar e configurar tools
        from tools.mcp.rh_tools import get_rh_tools
        from tools.mcp.ti_tools import get_ti_tools
        
        rh_tools = get_rh_tools()
        ti_tools = get_ti_tools()
        
        print(f"✅ {len(rh_tools)} tools de RH carregadas")
        print(f"✅ {len(ti_tools)} tools de TI carregadas")
        
        # Listar tools
        print("\n📋 Tools de RH:")
        for tool in rh_tools[:3]:  # Mostra apenas as primeiras 3
            print(f"  - {tool.name}: {tool.description}")
        
        print("\n📋 Tools de TI:")
        for tool in ti_tools[:3]:  # Mostra apenas as primeiras 3
            print(f"  - {tool.name}: {tool.description}")
        
        # Teste de execução com uma tool de RH
        client = MCPClient()
        test_tool = rh_tools[0]  # Primeira tool de RH
        client.register_tool(test_tool)
        
        result = client.call_tool(test_tool.name, {"cpf": "12345678901"})
        print(f"\n🧪 Teste da tool '{test_tool.name}':")
        print(f"   Status: {result.status}")
        print(f"   Dados: {result.data}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar tools: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("🔧 TESTE DO SISTEMA MCP NEOSON")
    print("=" * 50)
    
    success = True
    
    # Teste básico
    if test_basic_mcp():
        print("\n✅ Teste básico passou!")
    else:
        print("\n❌ Teste básico falhou!")
        success = False
    
    # Teste das tools específicas
    if test_rh_ti_tools():
        print("\n✅ Teste das tools específicas passou!")
    else:
        print("\n❌ Teste das tools específicas falhou!")
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("💥 ALGUNS TESTES FALHARAM!")
    print("=" * 50)