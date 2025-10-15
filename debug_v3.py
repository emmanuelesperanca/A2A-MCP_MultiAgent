"""
🔍 DEBUG - Teste Rápido das Melhorias v3.0
Identifica problemas de importação e inicialização
"""

import sys
from pathlib import Path

print("="*80)
print("🔍 TESTE DE DEBUG - NEOSON v3.0")
print("="*80)

# Teste 1: Imports
print("\n📦 TESTE 1: Verificando Imports...")
try:
    print("  ✓ Importando glossario_corporativo...")
    from core.glossario_corporativo import detectar_termos_corporativos, GLOSSARIO_CORPORATIVO
    print(f"    ✅ Glossário OK ({len(GLOSSARIO_CORPORATIVO)} termos)")
except Exception as e:
    print(f"    ❌ ERRO: {e}")
    sys.exit(1)

try:
    print("  ✓ Importando agent_classifier...")
    from core.agent_classifier import AgentClassifier, AGENTES_KNOWLEDGE_BASE
    print(f"    ✅ Classifier OK ({len(AGENTES_KNOWLEDGE_BASE)} áreas)")
except Exception as e:
    print(f"    ❌ ERRO: {e}")
    sys.exit(1)

try:
    print("  ✓ Importando security_instructions...")
    from core.security_instructions import get_security_prompt
    print("    ✅ Security OK")
except Exception as e:
    print(f"    ❌ ERRO: {e}")
    sys.exit(1)

try:
    print("  ✓ Importando neoson_async...")
    from neoson_async import NeosonAsync
    print("    ✅ NeosonAsync OK")
except Exception as e:
    print(f"    ❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Teste 2: Instanciação
print("\n🤖 TESTE 2: Instanciando Neoson...")
try:
    neoson = NeosonAsync()
    print(f"    ✅ Neoson instanciado (v{neoson.versao})")
    print(f"    ✅ Classifier presente: {neoson.classifier is not None}")
    print(f"    ✅ Glossário ativo: {neoson.glossario_ativo}")
    print(f"    ✅ Links proibidos: {neoson.proibir_links}")
except Exception as e:
    print(f"    ❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Teste 3: Métodos
print("\n⚙️ TESTE 3: Verificando Métodos...")
try:
    print("  ✓ Testando enriquecer_pergunta_com_glossario...")
    pergunta, termos = neoson.enriquecer_pergunta_com_glossario("Como acesso o GBS?")
    print(f"    ✅ Termos detectados: {termos}")
except Exception as e:
    print(f"    ❌ ERRO: {e}")

try:
    print("  ✓ Testando validar_resposta_sem_links...")
    limpa = neoson.validar_resposta_sem_links("Acesse https://test.com")
    print(f"    ✅ Link removido: {'https' not in limpa}")
except Exception as e:
    print(f"    ❌ ERRO: {e}")

# Teste 4: Classificador Async
print("\n🧠 TESTE 4: Testando Classificador (pode demorar ~3s)...")
try:
    import asyncio
    async def test_classificador():
        resultado = await neoson.classificar_pergunta_async("Como resetar senha?")
        return resultado
    
    resultado = asyncio.run(test_classificador())
    print(f"    ✅ Classificação OK")
    print(f"    📊 Área: {resultado['area_principal']}")
    print(f"    🤖 Agentes: {[a['agente'] for a in resultado['agentes_selecionados']]}")
except Exception as e:
    print(f"    ❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("✅ TESTE DE DEBUG CONCLUÍDO")
print("="*80)
print("\nSe todos os testes passaram, o problema está na inicialização async do FastAPI.")
print("Verifique se criar_neoson_async() está usando NeosonAsync corretamente.")
