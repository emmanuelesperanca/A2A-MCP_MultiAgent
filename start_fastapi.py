"""
Script de Inicialização Simplificado para FastAPI
Facilita o start do servidor com diferentes configurações
"""

import os
import sys
import argparse
from pathlib import Path


def verificar_dependencias():
    """Verifica se as dependências necessárias estão instaladas"""
    print("🔍 Verificando dependências...")
    
    dependencias_criticas = [
        'fastapi',
        'uvicorn',
        'asyncpg',
        'langchain',
        'openai'
    ]
    
    faltando = []
    for dep in dependencias_criticas:
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep} - NÃO INSTALADO")
            faltando.append(dep)
    
    if faltando:
        print(f"\n⚠️  Dependências faltando: {', '.join(faltando)}")
        print(f"📦 Instale com: pip install -r requirements_fastapi.txt")
        return False
    
    print("✅ Todas as dependências estão instaladas!\n")
    return True


def verificar_env():
    """Verifica se as variáveis de ambiente estão configuradas"""
    print("🔍 Verificando variáveis de ambiente...")
    
    env_vars = {
        'OPENAI_API_KEY': 'Chave da API OpenAI',
        'DATABASE_URL': 'URL do banco de dados PostgreSQL'
    }
    
    env_file = Path('.env')
    if not env_file.exists():
        print(f"  ⚠️  Arquivo .env não encontrado")
        print(f"  💡 Crie um arquivo .env com as variáveis necessárias")
        return False
    
    # Carregar .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("  ⚠️  python-dotenv não instalado")
        return False
    
    todas_ok = True
    for var, descricao in env_vars.items():
        valor = os.getenv(var)
        if valor:
            # Ocultar parte sensível
            if 'KEY' in var or 'PASSWORD' in var:
                valor_display = valor[:10] + '...' if len(valor) > 10 else '***'
            else:
                valor_display = valor[:30] + '...' if len(valor) > 30 else valor
            print(f"  ✅ {var}: {valor_display}")
        else:
            print(f"  ❌ {var}: NÃO CONFIGURADO ({descricao})")
            todas_ok = False
    
    if not todas_ok:
        print(f"\n⚠️  Configure as variáveis de ambiente no arquivo .env")
        return False
    
    print("✅ Variáveis de ambiente configuradas!\n")
    return True


def exibir_banner():
    """Exibe banner de inicialização"""
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║                 🚀 NEOSON - BACKEND FASTAPI                      ║
    ║                                                                   ║
    ║              Sistema Multi-Agente de IA Assíncrono               ║
    ║                         Versão 2.0.0                             ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)


def iniciar_servidor(args):
    """Inicia o servidor FastAPI com as configurações especificadas"""
    import uvicorn
    
    print("🚀 Iniciando servidor FastAPI...\n")
    
    config = {
        'app': 'app_fastapi:app',
        'host': args.host,
        'port': args.port,
        'reload': args.reload,
        'log_level': args.log_level,
    }
    
    if args.workers and args.workers > 1:
        config['workers'] = args.workers
        if args.reload:
            print("⚠️  --reload não funciona com múltiplos workers, desabilitando reload...")
            config['reload'] = False
    
    # Exibir configuração
    print("📋 Configuração do Servidor:")
    print(f"  🌐 Host: {config['host']}")
    print(f"  🔌 Porta: {config['port']}")
    print(f"  🔄 Auto-reload: {'✅' if config['reload'] else '❌'}")
    print(f"  👥 Workers: {config.get('workers', 1)}")
    print(f"  📊 Log Level: {config['log_level']}")
    print()
    
    # URLs úteis
    base_url = f"http://{config['host']}:{config['port']}"
    print("📍 URLs Disponíveis:")
    print(f"  🏠 Interface Web: {base_url}")
    print(f"  📚 Documentação (Swagger): {base_url}/docs")
    print(f"  📖 Documentação (ReDoc): {base_url}/redoc")
    print(f"  ❤️  Health Check: {base_url}/health")
    print(f"  📊 Status: {base_url}/api/status")
    print()
    print("🔄 Pressione Ctrl+C para parar o servidor\n")
    print("=" * 70)
    
    try:
        uvicorn.run(**config)
    except KeyboardInterrupt:
        print("\n\n⏹️  Servidor parado pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro ao iniciar servidor: {e}")
        sys.exit(1)


def main():
    """Função principal"""
    exibir_banner()
    
    parser = argparse.ArgumentParser(
        description='Inicia o servidor FastAPI do Neoson',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  
  # Desenvolvimento (auto-reload)
  python start_fastapi.py --dev
  
  # Produção (4 workers)
  python start_fastapi.py --prod --workers 4
  
  # Porta customizada
  python start_fastapi.py --port 8080
  
  # Host customizado (acessível externamente)
  python start_fastapi.py --host 0.0.0.0 --port 8000
        """
    )
    
    # Argumentos
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Host do servidor (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Porta do servidor (default: 8000)'
    )
    
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Habilitar auto-reload (desenvolvimento)'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=1,
        help='Número de workers (produção)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['critical', 'error', 'warning', 'info', 'debug'],
        default='info',
        help='Nível de log (default: info)'
    )
    
    parser.add_argument(
        '--dev',
        action='store_true',
        help='Modo desenvolvimento (--reload --log-level debug)'
    )
    
    parser.add_argument(
        '--prod',
        action='store_true',
        help='Modo produção (--workers 4 --log-level warning)'
    )
    
    parser.add_argument(
        '--skip-checks',
        action='store_true',
        help='Pular verificações de dependências e ambiente'
    )
    
    args = parser.parse_args()
    
    # Atalhos de modo
    if args.dev:
        args.reload = True
        args.log_level = 'debug'
        print("🔧 Modo DESENVOLVIMENTO ativado\n")
    
    if args.prod:
        args.workers = 4
        args.log_level = 'warning'
        args.reload = False
        print("🚀 Modo PRODUÇÃO ativado\n")
    
    # Verificações
    if not args.skip_checks:
        if not verificar_dependencias():
            sys.exit(1)
        
        if not verificar_env():
            resposta = input("\n❓ Continuar mesmo assim? (s/N): ")
            if resposta.lower() != 's':
                print("⏹️  Inicialização cancelada")
                sys.exit(1)
            print()
    
    # Iniciar servidor
    iniciar_servidor(args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Inicialização cancelada pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
