"""
Wrapper para executável PyInstaller - Neoson Backend
Este arquivo substitui o start_fastapi.py quando rodando como executável
"""

import sys
import os
import shutil
from pathlib import Path

# ============================================================================
# Configurar paths para executável
# ============================================================================

if getattr(sys, 'frozen', False):
    # Rodando como executável PyInstaller
    BASE_PATH = Path(sys._MEIPASS)  # Diretório temporário do PyInstaller
    APP_PATH = Path(sys.executable).parent  # Diretório do executável
    
    # Mudar diretório de trabalho para onde está o executável
    os.chdir(APP_PATH)
    print(f"📁 Diretório de trabalho alterado para: {APP_PATH}")
    
    # Criar diretório static se não existir
    STATIC_DIR = APP_PATH / "static"
    STATIC_SOURCE = BASE_PATH / "static"
    
    if STATIC_SOURCE.exists() and not STATIC_DIR.exists():
        print("📁 Copiando arquivos estáticos...")
        shutil.copytree(STATIC_SOURCE, STATIC_DIR)
    elif not STATIC_DIR.exists():
        print("📁 Criando diretório static vazio...")
        STATIC_DIR.mkdir(parents=True, exist_ok=True)
    
    # Criar diretório templates se não existir
    TEMPLATES_DIR = APP_PATH / "templates"
    TEMPLATES_SOURCE = BASE_PATH / "templates"
    
    if TEMPLATES_SOURCE.exists() and not TEMPLATES_DIR.exists():
        print("📄 Copiando templates...")
        shutil.copytree(TEMPLATES_SOURCE, TEMPLATES_DIR)
    elif not TEMPLATES_DIR.exists():
        print("📄 Criando diretório templates vazio...")
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
else:
    # Rodando como script Python normal
    BASE_PATH = Path(__file__).parent
    APP_PATH = BASE_PATH

# Adicionar diretórios ao Python path
sys.path.insert(0, str(BASE_PATH))
sys.path.insert(0, str(APP_PATH))

print(f"📁 BASE_PATH: {BASE_PATH}")
print(f"📁 APP_PATH: {APP_PATH}")
print(f"📁 sys._MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
print()

# ============================================================================
# Importações
# ============================================================================

import uvicorn
from dotenv import load_dotenv

# Carregar .env - procurar em múltiplos locais
env_file_locations = [
    APP_PATH / '.env',          # Na pasta do executável (externo)
    BASE_PATH / '.env',         # Dentro do bundle (_internal)
    Path.cwd() / '.env',        # No diretório de trabalho atual
]

env_loaded = False
for env_file in env_file_locations:
    if env_file.exists():
        print(f"✅ Carregando .env de: {env_file}")
        load_dotenv(env_file)
        env_loaded = True
        break

if not env_loaded:
    print(f"⚠️ Arquivo .env não encontrado em:")
    for loc in env_file_locations:
        print(f"   - {loc}")
    print(f"💡 Crie um arquivo .env em uma dessas localizações")

# ============================================================================
# Verificar variáveis de ambiente
# ============================================================================

print("\n🔍 Verificando variáveis de ambiente...")

required_vars = {
    'OPENAI_API_KEY': 'Chave da API OpenAI',
}

all_ok = True
for var, description in required_vars.items():
    value = os.getenv(var)
    if value:
        # Ocultar parte sensível
        display_value = value[:10] + '...' if len(value) > 10 else '***'
        print(f"  ✅ {var}: {display_value}")
    else:
        print(f"  ❌ {var}: NÃO CONFIGURADO ({description})")
        all_ok = False

if not all_ok:
    print(f"\n⚠️ Arquivo .env não encontrado")
    print(f"💡 Crie um arquivo .env com as variáveis necessárias")
    response = input("\n❓ Continuar mesmo assim? (s/N): ")
    if response.lower() != 's':
        print("⏹️ Inicialização cancelada")
        sys.exit(1)

print()

# ============================================================================
# Banner
# ============================================================================

print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║                 🚀 NEOSON - BACKEND FASTAPI                      ║
║                                                                   ║
║              Sistema Multi-Agente de IA Assíncrono               ║
║                       Versão 2.0.0 - Executável                  ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")

# ============================================================================
# Iniciar servidor
# ============================================================================

print("🚀 Iniciando servidor FastAPI...\n")

# Configuração do servidor
HOST = os.getenv('FASTAPI_HOST', '127.0.0.1')
PORT = int(os.getenv('FASTAPI_PORT', '8000'))
RELOAD = False  # Sempre False no executável
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info')

print("📋 Configuração do Servidor:")
print(f"  🌐 Host: {HOST}")
print(f"  🔌 Porta: {PORT}")
print(f"  🔄 Auto-reload: ❌")
print(f"  👥 Workers: 1")
print(f"  📊 Log Level: {LOG_LEVEL}")
print()

# URLs úteis
base_url = f"http://{HOST}:{PORT}"
print("📍 URLs Disponíveis:")
print(f"  🏠 Interface Web: {base_url}")
print(f"  📚 Documentação (Swagger): {base_url}/docs")
print(f"  📖 Documentação (ReDoc): {base_url}/redoc")
print(f"  ❤️  Health Check: {base_url}/health")
print(f"  📊 Status: {base_url}/api/status")
print()
print("🔄 Pressione Ctrl+C para parar o servidor\n")
print("=" * 70)
print()

# ============================================================================
# Importar e iniciar aplicação
# ============================================================================

try:
    # Importar o módulo app_fastapi
    print("📦 Importando módulo app_fastapi...")
    import app_fastapi
    
    print("✅ Módulo importado com sucesso")
    print(f"📦 App: {app_fastapi.app}")
    print()
    
    # Iniciar servidor com o objeto app diretamente
    uvicorn.run(
        app_fastapi.app,  # Objeto app diretamente, não string
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_level=LOG_LEVEL.lower(),
    )
    
except KeyboardInterrupt:
    print("\n\n⏹️ Servidor parado pelo usuário")
    
except ImportError as e:
    print(f"\n\n❌ ERRO: Não foi possível importar 'app_fastapi': {e}")
    print(f"\n🔍 Diagnóstico:")
    print(f"  📁 Diretório atual: {os.getcwd()}")
    print(f"  📁 Python path: {sys.path[:3]}")
    print(f"  📦 Arquivos em BASE_PATH:")
    if BASE_PATH.exists():
        for item in BASE_PATH.iterdir():
            print(f"    - {item.name}")
    sys.exit(1)
    
except Exception as e:
    print(f"\n\n❌ Erro ao iniciar servidor: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
