"""
Exemplo de uso do sistema de configuração centralizada.

Este arquivo demonstra como usar o novo módulo core.config para
gerenciar configurações de forma centralizada e seguir o princípio DRY.
"""

from core.config import (
    config, 
    get_openai_config, 
    get_database_url, 
    get_table_name, 
    validate_config, 
    print_config_summary
)


def exemplo_uso_basico():
    """Demonstra o uso básico do sistema de configuração."""
    
    print("=== EXEMPLO DE USO DO SISTEMA DE CONFIGURAÇÃO ===\n")
    
    # 1. Validar configurações
    print("1. Validando configurações...")
    validation_results = validate_config()
    
    for component, is_valid in validation_results.items():
        status = "✅" if is_valid else "❌"
        print(f"   {status} {component}")
    
    if not all(validation_results.values()):
        print("\n❌ Algumas configurações estão inválidas!")
        return False
    
    print("✅ Todas as configurações são válidas!\n")
    
    # 2. Acessar configurações OpenAI
    print("2. Configurações OpenAI:")
    openai_config = get_openai_config()
    print(f"   - Modelo de chat: {openai_config.chat_model}")
    print(f"   - Modelo de embedding: {openai_config.embedding_model}")
    print(f"   - Temperature: {openai_config.temperature}")
    print(f"   - Max tokens: {openai_config.max_tokens}")
    print(f"   - API key configurada: {'Sim' if openai_config.api_key else 'Não'}\n")
    
    # 3. Acessar configurações de banco de dados
    print("3. Configurações de banco de dados:")
    
    domains = ["main", "rh", "ti", "governance", "infra", "dev", "enduser"]
    for domain in domains:
        try:
            db_url = get_database_url(domain)
            table_name = get_table_name(domain)
            url_preview = db_url[:50] + "..." if len(db_url) > 50 else db_url
            print(f"   - {domain}: {table_name} ({url_preview})")
        except Exception as e:
            print(f"   - {domain}: ❌ Erro: {e}")
    
    print()
    
    # 4. Usar configuração diretamente do singleton
    print("4. Acesso direto ao singleton:")
    print(f"   - Debug mode: {config.app.debug}")
    print(f"   - Log level: {config.app.log_level}")
    print(f"   - Flask host: {config.app.flask_host}")
    print(f"   - Flask port: {config.app.flask_port}")
    print(f"   - Environment: {config.app.environment}\n")
    
    return True


def exemplo_uso_em_agente():
    """Demonstra como usar o sistema em um agente."""
    
    print("=== EXEMPLO DE USO EM UM AGENTE ===\n")
    
    try:
        # Configuração para um agente de RH
        print("Configurando agente de RH...")
        
        # Obter configuração específica do domínio
        rh_config = config.get_database_config("rh")
        openai_config = config.openai
        
        print(f"✅ Database URL: {rh_config['url'][:50]}...")
        print(f"✅ Table name: {rh_config['table']}")
        print(f"✅ OpenAI model: {openai_config.chat_model}")
        
        # Simular inicialização de componentes
        print("\nSimulando inicialização de componentes:")
        print(f"   - LLM configurado: {openai_config.chat_model}")
        print(f"   - Embeddings configurados: {openai_config.embedding_model}")
        print(f"   - Vector store conectado: {rh_config['table']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na configuração do agente: {e}")
        return False


def exemplo_migracao_codigo_antigo():
    """Mostra como migrar código antigo para o novo sistema."""
    
    print("=== EXEMPLO DE MIGRAÇÃO DE CÓDIGO ANTIGO ===\n")
    
    print("❌ CÓDIGO ANTIGO (repetitivo):")
    print("""
    # Em cada arquivo...
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    db_url = os.getenv("DATABASE_URL") 
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    """)
    
    print("✅ CÓDIGO NOVO (centralizado):")
    print("""
    # Em cada arquivo...
    from core.config import config
    
    api_key = config.openai.api_key
    db_url = config.database.main_url
    model = config.openai.chat_model
    """)
    
    print("\n🎯 BENEFÍCIOS:")
    print("   - ✅ Configuração centralizada")
    print("   - ✅ Validação automática") 
    print("   - ✅ Singleton pattern (performance)")
    print("   - ✅ Tipagem forte")
    print("   - ✅ Facilita testes")
    print("   - ✅ Facilita manutenção")


if __name__ == "__main__":
    print("🔧 DEMONSTRAÇÃO DO SISTEMA DE CONFIGURAÇÃO CENTRALIZADA\n")
    
    try:
        # Mostrar resumo da configuração
        print_config_summary()
        print("\n" + "="*60 + "\n")
        
        # Executar exemplos
        if exemplo_uso_basico():
            print("="*60 + "\n")
            exemplo_uso_em_agente()
            print("\n" + "="*60 + "\n")
            exemplo_migracao_codigo_antigo()
            
            print(f"\n🎉 Sistema de configuração funcionando perfeitamente!")
            
    except Exception as e:
        print(f"❌ Erro durante a demonstração: {e}")
        print("\n💡 Verifique se o arquivo .env está configurado corretamente.")